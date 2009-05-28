# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2008 Openmoko
#    copyright 2009 Openmoko
#
#    This file is part of Paroli.
#
#    Paroli is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paroli is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paroli.  If not, see <http://www.gnu.org/licenses/>.

import elementary
import e_dbus
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.x
import ecore.evas
#import etk

import logging
logger = logging.getLogger('gui')

import tichy

class EventsLoop(tichy.Object):

    def __init__(self):
        self.dbus_loop = e_dbus.DBusEcoreMainLoop()
        try:
            elementary.c_elementary.theme_overlay_add("/usr/share/elementary/themes/paroli.edj")
        except:
            logger.info("can't add elementary theme overlay, please update your bindings")
        elementary.init()

    def run(self):
        """start the main loop

        This method only return after we call `quit`.
        """
        
        
        ecore.main_loop_begin()
        ecore.x.on_window_delete_request_add(self.test)
        #elementary.run()
        # XXX: elementary also has a run method : elementary.run(),
        #      how does it work with ecore.main_loop ?

    def test(self, *args, **kargs):
        logger.info("delete request with %s %s", args, kargs)

    def timeout_add(self, time, callback, *args):
        return ecore.timer_add(time / 1000., callback, *args)
        pass

    def source_remove(self, timer):
        pass
        timer.delete()

    def quit(self):
        self.emit("closing")
        logger.info("emitted closing")
        ecore.main_loop_quit()
        elementary.shutdown()
        
    def iterate(self):
        #ecore.main_loop_iterate()
        pass

class elm_window(tichy.Object):
    def __init__(self, title="Paroli"):
        self.elm_obj = elementary.Window(title, elementary.ELM_WIN_BASIC)
        self.elm_obj.title_set(title)
        self.elm_obj.autodel_set(True)
        self.elm_obj.on_del_add(self.closing)
    
    def printer(self, *args, **kargs):
        logger.info("window printer called with %s and %s", args, kargs)
    
    def closing(self, *args, **kargs):
        self.emit("closing")
        
    def info(self, *args, **kargs):
        print self.elm_obj.size_get()
        layer = self.elm_obj.layer_get()
        print layer
        if self.elm_obj.size_get() != self.size:
            if self.size[0] == 1:
                self.size = self.elm_obj.size_get()
            else:
                self.elm_obj.layer_set(layer-1)
                print self.elm_obj.layer_get()
                self.elm_obj.resize(self.size[0],self.size[1])
        
        
class elm_layout(tichy.Object):
    def __init__(self, win, edje_file, group, x=1.0, y=1.0):
        self.elm_obj = elementary.Layout(win.elm_obj)
        self.elm_obj.file_set(edje_file, group)
        self.elm_obj.show()
        self.add_callback("*", "main_command", self.relay)
        self.Edje = self.elm_obj.edje_get()
        
    def relay(self, emission, signal, source):
        logger.debug("%s relaying %s", str(self), str(signal))
        self.emit(signal)
    
    def add(self, part, element):
        self.elm_obj.content_set(part, element)

    def add_callback(self, signal, source, func):
        self.elm_obj.edje_get().signal_callback_add(signal, source, func)

    def delete(self, *args, **kargs):
        self.elm_obj.hide()
        self.elm_obj.delete()

class elm_scroller(tichy.Object):
    def __init__(self, win):
        self.elm_obj = elementary.Scroller(win.elm_obj)
        self.elm_obj.size_hint_weight_set(1.0, 1.0)
        self.elm_obj.size_hint_align_set(-1.0, -1.0)
        if hasattr(self.elm_obj, "bounce_set"):
            self.elm_obj.bounce_set(0, 0)
        self.elm_obj.show()
        
class elm_box(tichy.Object):
    def __init__(self, win):
        self.elm_obj = elementary.Box(win)
        self.elm_obj.size_hint_weight_set(0.0, 0.0)
        self.elm_obj.size_hint_align_set(0.0, 0.0)
        self.elm_obj.show()

class elm_tb(tichy.Object):
    def __init__(self, parent, onclick, edje_file, standalone=False):
        self.parent = parent
        self.onclick = onclick
        self.standalone = tichy.config.getboolean('standalone','activated', False)
        if self.standalone == True:
            self.bg = elm_layout(parent.window, edje_file, "bg-tb-on")
            self.tb = elm_layout(parent.window, edje_file, "tb")
            self.bg.elm_obj.content_set("tb-swallow", self.tb.elm_obj)
            self.tb.elm_obj.edje_get().signal_callback_add("top-bar", "*", self.signal)
        else:
            self.bg = elm_layout(parent.window, edje_file, "bg-tb-off")

    def signal(self, emission, signal, source):
        logger.info(" %s emitting %s", str(self.parent), str(self.onclick))
        self.parent.emit(self.onclick)

class elm_layout_window(tichy.Object):
    def __init__(self, edje_file, group, x=1.0, y=1.0, tb=False, onclick=None):
        self.window = elm_window()  
        self.window.elm_obj.show()
        
        self.tb_action = onclick or 'back'
        
        self.bg_m = tichy.Service.get("TopBar").create(self, self.tb_action, tb)
        
        self.bg = self.bg_m.bg
        
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def tb_action_set(self, func):
        self.tb_action = func

    def delete(self, *args, **kargs):
        self.window.elm_obj.delete()
        
    def printer(self, *args, **kargs):
        print args
        
    def restore_orig(self, *args, **kargs):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
   
    def empty_window(self, *args, **kargs):
        self.bg.elm_obj.resize_object_del(self.main_layout.elm_obj)

class elm_layout_subwindow(elm_layout_window):
    def __init__(self, window, edje_file, group):
        self.window = window.window
        self.bg = window.bg_m.bg
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        #print self.bg.Edje.part_exists("content-swallow")
        #self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def restore_orig(self):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)

class elm_list_subwindow(elm_layout_window):
    def __init__(self, window, edje_file, group, swallow, layout=None):
        self.window = window.window
        self.bg = window.bg_m.bg
        self.bg_m = window.bg_m
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = elm_scroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        if layout != None:
            self.window.elm_obj.resize_object_del(layout)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()
    
class elm_list_window(elm_layout_window):
    def __init__(self, edje_file, group, swallow , sx=None, sy=None, tb=False, onclick=None):
        self.window = elm_window()  
        self.window.elm_obj.show()
        
        self.tb_action = onclick or 'back'
        
        self.bg_m = tichy.Service.get("TopBar").create(self, self.tb_action, tb)
        
        self.bg = self.bg_m.bg
        
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = elm_scroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()
      
class elm_list(tichy.Object):
      def __init__(self, model, Parent, EdjeFile, EdjeGroup, label_list, comp_fct):
          
          self.model = model
          self.parent = Parent
          self.EdjeFile = EdjeFile
          self.EdjeGroup = EdjeGroup
          self.Elm_win = Parent.window
          self.label_list = label_list    
          self._comp_fct = comp_fct
          self.cb_list = []
          self.cb_list.append(self.model.connect('appended', self._redraw_view))
          self.cb_list.append(self.model.connect('inserted', self._redraw_view))
          self.cb_list.append(self.model.connect('removed', self._redraw_view))
          self.box = elm_box(self.Elm_win.elm_obj)
          self.callbacks = []
          self.sort()
          self.items = []
          self.letter_index = {}
          self._redraw_view()
          self.Elm_win.elm_obj.on_del_add(self._remove_cb)
    
      def _redraw_view(self, *args, **kargs):
          #logger.info("list redrawing")
          if self.Elm_win.elm_obj.is_deleted() == True:
                self._remove_cb()
          else:
              self.sort()
              if self.box.elm_obj.is_deleted() == False:
                  self.box.elm_obj.delete()
              self.box = elm_box(self.Elm_win.elm_obj)
              self.items = []
              self.letter_index = {}
              #self.model.sort()
              for item in self.model:
                  if self.Elm_win.elm_obj.is_deleted() == True:
                      logger.info(str(self.model))
                      logger.info("window deleted")
                  ly = elementary.Layout(self.Elm_win.elm_obj)
                  ly.file_set(self.EdjeFile, self.EdjeGroup)              
                  edje_obj = ly.edje_get()
                  for part, attribute in self.label_list:
                    if hasattr(item, attribute):
                        value = getattr(item, attribute)
                        #if self.label_list.index((part, attribute)) == 0:
                            #if self.letter_index.has_key(value[0]) == False:
                                #self.letter_index[value[0]] = self.model.index(item)
                        
                        if isinstance(value, tichy.Item):
                            value = unicode(value.get_text())
                        elif isinstance(value, tichy.Text):
                            value = value.value
                        
                        txt = unicode(value).encode('utf-8')
                        edje_obj.part_text_set(part,txt)
                    else:
                        logger.info(" %s doesn't have attribute %s", str(item), str(attribute))
                  
                  ##check for optional display elements
                  if edje_obj.data_get('attribute1') != None:
                      attribute = edje_obj.data_get('attribute1')
                      if edje_obj.data_get('attribute2') != None:
                          item_cp = getattr(item,attribute)
                          attribute = edje_obj.data_get('attribute2')
                      else:  
                          item_cp = item
                      if edje_obj.data_get('value') == 'None':
                          value = None
                      else:
                          value = edje_obj.data_get('value')
                      signal = edje_obj.data_get('signal')
                      if attribute[-2] == "(":
                          test = getattr(item_cp,attribute[:-2])()
                      else:
                          test = getattr(item_cp,attribute)
                      if test == value:
                          edje_obj.signal_emit(signal,'*')

                  ly.size_hint_min_set(470,100)
                  self.box.elm_obj.pack_end(ly)
                  ly.show()
                  self.items.append([item,edje_obj,ly])
                  edje_obj.signal_callback_add("*", "list_command", self.signal_send_others, [item,edje_obj,ly])
              
              self.parent.scroller.elm_obj.content_set(self.box.elm_obj)
              self.box.elm_obj.show()
              
              self.parent.scroller.elm_obj.show()
              
              self._renew_callbacks()

      def _renew_callbacks(self, *args, **kargs):
          logger.info("renewing callbacks")
          for cb in self.callbacks:
                for i in self.items:
                    i[1].signal_callback_add(cb[0], cb[1] , cb[2], i)

      def sort(self,*args,**kargs):
          logger.debug("list sorting")
          self.model.sort(self._comp_fct)
    
      def _remove_cb(self, *args, **kargs):
          logger.debug('window removed, removing cb')
          for i in self.cb_list :
              try:
                  self.model.disconnect(i)
              except Exception, e:
                  logger.debug("ooops wrong oid")
      
      def _modified(self, *args, **kargs):
          logger.info('scrolled')
          logger.info(args)
          logger.info(kargs)
      
      def add_callback(self, signal, source, func):
          self.callbacks.append([signal, source, func])
          for i in self.items:
              i[1].signal_callback_add(signal, source , func, i)

      def signal_send_others(self, emission, signal, source, item):
          for i in self.items:
              if i != item:
                  i[1].signal_emit(signal, "list")

      def signal_send(self, signal, source):
          for i in self.items:
              i[1].signal_emit(signal, source)

      def _remove_item(self, list, removed_item):
          logger.info('remove called')
          for item in self.items:
              if item[0] is removed_item:
                  index = item
                  item[2].remove_all()
          
          self.items.remove(index)
          self._redraw_box()
      
      def jump_to_index(self, key):
          if self.letter_index.has_key(key):
              position = self.letter_index[key]
              point_y = 60 * int(position)
              if hasattr(self.parent.scroller.elm_obj, 'region_show'):
                  self.parent.scroller.elm_obj.region_show(0, point_y, 480, 60)
              else:
                  logger.info("scroller doesn't have method bounce_set please update your bindings")
      
###XXX: everything below is deprecated and will be removed
#class Widget(tichy.Object):
    #def __init__(self, parent, etk_obj = None, item = None, expand = False, **kargs):
        #self.etk_obj = etk_obj or etk.VBox()
        #self.item = item
        #self.parent = parent
        #self.children = []
        #self.expand = expand
        #if self.parent:
            #self.parent.get_contents_child().add(self)
        ##self.show()
    #def add(self, child):
        #self.etk_obj.add(child.etk_obj)
        #self.children.append(child)
    #def get_evas(self):
        #return self.parent.get_evas()
    #def show(self):
        #try:
            #self.etk_obj.show_all()
        #except Exception, e:
            #pass

    #def get_contents_child(self):
        #return self

    #def parent_as(self, cls):
        #if isinstance(self.parent, cls):
            #return self.parent
        #return self.parent.parent_as(cls)

    #def __get_window(self):
        #return self.parent_as(Window)
    #window = property(__get_window)

    #def destroy(self):
        #self.etk_obj.destroy()

    ## No tags for this implementation
    #def add_tag(self, tag):
        #pass
    #def remove_tag(self, tag):
        #pass

#class Window(Widget):
    #def __init__(self, parent, w=480, h=580, **kargs):
        #etk_obj = ecore.evas.SoftwareX11(w=w, h=h)
        #etk_obj.callback_delete_request_set(self.delete_request)
        #Widget.__init__(self, None, etk_obj=etk_obj)

    #def delete_request(self,*args,**kargs):
        #logger.info(str(args))
        #self.emit('delete_request')

    #def show(self):
        #self.etk_obj.show()

    #def destroy(self):
        #self.etk_obj.hide()

#class Screen(Window):
    #"""We don't use screen at all

    #It doesn't make sense with etk backend.
    #"""

    #def __init__(self, loop, painter, **kargs):
        #pass

    #def add(self, child):
        #pass


#class Box(Widget):
    #def __init__(self, parent, axis=0, **kargs):
        #if axis == 0:
            #etk_obj = etk.HBox()
        #else:
            #etk_obj = etk.VBox()
        #super(Box, self).__init__(parent, etk_obj=etk_obj, **kargs)

    #def add(self, child):
        #policy = etk.VBox.FILL
        #if child.expand:
            #policy = etk.VBox.EXPAND_FILL
        #self.etk_obj.append(child.etk_obj, etk.VBox.START, policy, 0)

#class Frame(Box):
    #def __init__(self, parent, **kargs):
        #super(Frame, self).__init__(parent, **kargs)

#class Fixed(Widget):
    #pass

#class Table(Widget):
    #pass

#class Table(Widget):
    #def __init__(self, parent, nb = 3, **kargs):
        #self.nb = nb
        #self.current = 0
        #etk_obj = etk.Table(nb, 5, etk.Table.HOMOGENEOUS)
        #super(Table, self).__init__(parent, etk_obj=etk_obj, **kargs)
    #def add(self, child):
        #x = self.current % self.nb
        #y = self.current / self.nb
        #self.etk_obj.attach_default(child.etk_obj, x, x, y, y)
        #self.current += 1

#class Scrollable(Widget):
    #def __init__(self, parent, **kargs):
        #etk_obj = etk.ScrolledView()
        #super(Scrollable, self).__init__(parent, etk_obj=etk_obj, **kargs)
    #def add(self, child):
        #self.etk_obj.add_with_viewport(child.etk_obj)

#class Button(Widget):
    #def __init__(self, parent, **kargs):
        #etk_obj = etk.Button()
        #super(Button, self).__init__(parent, etk_obj=etk_obj, **kargs)
        #self.etk_obj.connect('clicked', self.on_clicked)
    #def on_clicked(self, *args):
        #self.emit('clicked')

#class Label(Widget):
    #def __init__(self, parent, text, **kargs):
        #etk_obj = etk.Label(text)
        #super(Label, self).__init__(parent, etk_obj=etk_obj, **kargs)

    #def __get_text(self):
        #return self.etk_obj.get()
    #def __set_text(self, value):
        #self.etk_obj.set(value)
    #text = property(__get_text, __set_text)

#class Edit(Widget):
    #def __init__(self, parent, item = None, **kargs):
        #etk_obj = etk.Entry()
        #super(Edit, self).__init__(parent, etk_obj=etk_obj, **kargs)
    
    #def set_text(self,txt):
        #self.etk_obj.text = txt

    #def set_pw_mode(self,mode):
        #self.etk_obj.password_mode_set(mode)

#class Spring(Widget):
    #def __init__(self, parent, expandable = True, **kargs):
        #super(Spring, self).__init__(parent, expandable=expandable, **kargs)


#class SurfWidget(Widget):
    #pass

#class ImageWidget(Widget):
    #def __init__(self, parent, image, **kargs):
        #self.image = image
        #etk_obj = etk.Image()
        #etk_obj.set_from_file(image.path)
        #super(ImageWidget, self).__init__(parent, etk_obj=etk_obj, **kargs)

#class ScrollableSlide(Widget):
    #pass

#class Painter(object):
    #"""We don't use Painter at all

    #It doesn't make sense with etk backend.
    #"""
    #def __init__(self, size, fullscreen = None):
        #pass

#####ADDED by mirko

#class ScrollerEdje(tichy.Object):
    
    #def __init__(self, EdjeObject):
        #self.box = etk.VBox()
        #self.scrollbox = etk.c_etk.ScrolledView()
        #self.scrollbox.add_with_viewport(self.box)
        ### hide scrollbars with (2, 2)
        #self.scrollbox.policy_set(2, 0)
        ### make it dragable
        #self.scrollbox.dragable_set(True)
        ### make it non-bouncing with (False)
        #self.scrollbox.drag_bouncy_set(True)
        
        #self.canvas = etk.Canvas()
        #self.canvas.show_all()
        ##logger.info(self.canvas.geometry_get())
        #self.canvas.object_add(EdjeObject)
        #self.box.append(self.canvas, etk.VBox.START, etk.VBox.EXPAND_FILL, 0)        

#class EdjeObject(tichy.Object):
    #"""Base class for edje Elements used to generate application windows """
    #def __init__(self, Parent, EdjeFile, EdjeGroup, EdjeWindows=None, Keyboard=None ):
        ##super(EdjeObject, self).__init__()
        #self.Parent = Parent
        #self.EdjeFile = EdjeFile
        #self.EdjeGroup = EdjeGroup
        #self.Evas = Parent.etk_obj.evas
        #self.Edje = edje.Edje(self.Evas, file=self.EdjeFile, group=self.EdjeGroup)
        #self.Edje.data['windows'] = tichy.List()
        #self.Edje.data['EdjeObject'] = self
        #self.Windows = self.Edje.data['windows']
        #self.EdjeWindows = EdjeWindows
        
        ##self.Edje.on_del_add(self.delete)
        
        #if EdjeWindows != None:
            #EdjeWindows.append(self)

        #if Keyboard != None:
            #self.Edje.on_show_add(self.open_keyboard)
            #self.Edje.on_hide_add(self.close_keyboard)
            #self.Edje.on_del_add(self.close_keyboard)

    #def show(self,layer=2,*args,**kargs):
        #self.Edje.layer_set(layer)
        #self.Edje.show()

    #def dehide(self,*args,**kargs):
        #self.Edje.show()

    #def add_callback(self, signal, source, callback, *args, **kargs):
        #self.Edje.signal_callback_add(signal, source, callback, *args, **kargs)

    #def data_add(self, key, data):
        #if not self.Edje.data[key]:
            #self.Edje.data[key] = data
        #else:
            #self.Edje.data[key].append(data)

    #def signal(self, signal, source):
        #self.Edje.signal_emit(signal, source)

    #def close_keyboard(self, *args, **kargs):
        #logger.info("close keyboard called")
        #self.Parent.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
    
    #def open_keyboard(self, *args, **kargs):
        #logger.info("open keyboard called")
        #self.Parent.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)

    #def hide(self,*args,**kargs):
        #self.Edje.hide()

    #def back(self, *args, **kargs):
        #if self.EdjeWindows != None:
            #self.EdjeWindows.remove(self)
            
        #self.Edje.delete()

    #def delete(self, *args, **kargs):
        #try:
            #if self.Windows != None:
                #aux_list = self.Windows
                
                #for i in range(len(aux_list)):  
                    #if isinstance(self.Windows[i-1], edje.Edje):
                        #self.Windows[i-1]['EdjeObject'].delete()
                    #else:    
                        #self.Windows[i-1].delete()
                    
        #except Exception, e:
            #dialog = tichy.Service.get('Dialog')
            #logger.error(Exception, " ", e)
            #dialog.error(self.Parent, e)
        
        #if self.EdjeWindows != None:
            #if self.EdjeWindows.count(self) != 0:
                #self.EdjeWindows.remove(self)
            
        #self.Edje.delete()

#class EdjeWSwallow(EdjeObject):
      #"""Use this if your EdjeObject has a swallow part, the delete method will take care of deleting it on close"""
      #def __init__(self, Parent, EdjeFile, EdjeGroup, EdjeSwallow, EdjeWindows=None, Keyboard= None):
          #self.Swallow = EdjeSwallow
          #super(EdjeWSwallow, self).__init__(Parent, EdjeFile, EdjeGroup, EdjeWindows, Keyboard)
      
      #def embed(self, child, box, part):
          #embed = etk.Embed(self.Evas)
          #embed.add(child)
          #embed.show_all()
          #self.Edje.part_swallow(part, embed.object)

      #def back(self, *args, **kargs):
          #if self.EdjeWindows != None:
              #self.EdjeWindows.remove(self)
              
          #self.Edje.part_swallow_get(self.Swallow).visible_set(0)
          #self.Edje.part_swallow_get(self.Swallow).delete()
          
          #self.Edje.delete()

      #def delete(self, *args, **kargs):
          ##print "delete called on: ", self
          
          #try:
              #if self.Windows != None:
                #aux_list = self.Windows
                
                #for i in range(len(aux_list)):  
                    #if isinstance(self.Windows[i-1], edje.Edje):
                        #self.Windows[i-1]['EdjeObject'].delete()
                    #else:    
                        #self.Windows[i-1].delete()
                  
          #except Exception, e:
              #dialog = tichy.Service.get('Dialog')
              #logger.error(Exception, " ", e)
              #dialog.error(self.Parent, e)
          
          #if self.EdjeWindows != None:
              #if self.EdjeWindows.count(self) != 0:
                  #self.EdjeWindows.remove(self)
          
          #if self.Edje.part_swallow_get(self.Swallow) != None:
          
              #self.Edje.part_swallow_get(self.Swallow).visible_set(0)
              #self.Edje.part_swallow_get(self.Swallow).delete()
          
          #if self.Edje.is_deleted() != True:
              #self.Edje.delete()

#class EvasList(tichy.Object):
      #def __init__(self, model, Parent, EdjeFile, EdjeGroup, label_list, comp_fct, EdjeFrame=None ):
          #self.model = model
          #self.parent = Parent
          #self.EdjeFrame = EdjeFrame
          #self.EdjeFile = EdjeFile
          #self.EdjeGroup = EdjeGroup
          #self.Evas = Parent.etk_obj.evas
          #self.label_list = label_list    
          #self._comp_fct = comp_fct
          #self.monitor(self.model, 'appended', self._append_new)
          #self.monitor(self.model, 'removed', self._remove_item)
          #self.box = etk.VBox()
          #self.callbacks = []
          #self.sort()
          #self.items = []
          #self.page_size = 1.0
          #if self.EdjeFrame != None:
              #self.EdjeFrame.Edje.signal_emit(str(len(self.model)),"python")
    
      #def _modified(self, *args, **kargs):
          #logger.info('scrolled')
          #logger.info(args)
          #logger.info(kargs)
    
      #def get_swallow_object(self):
          #self.items = []
  
          #for item in self.model:
              #single = self.generate_single_item(item)
              #self.box.append(single[2], etk.VBox.START, etk.VBox.EXPAND_FILL, 0)
              #self.items.append(single)
              #item.connect('modified',self._redraw_view)
              
          #self.scrollbox = etk.c_etk.ScrolledView()
          #self.scrollbox.add_with_viewport(self.box)
          ### hide scrollbars
          #self.scrollbox.policy_set(2, 2)
          ### make it dragable
          #self.scrollbox.dragable_set(False)
          ### make it non-bouncing
          #self.scrollbox.drag_bouncy_set(False)
          ##scrollbox.add_with_viewport(self.box)
          #self.scrollbox.drag_damping_set(0)
          ##get scrollbar value
          #self.calc_value()
          
          #self.vscrollbar = self.scrollbox.vscrollbar_get()
          ##scrollbox.vscrollbar_get().connect(scrollbox.vscrollbar_get().VALUE_CHANGED_SIGNAL,self._modified)
          ##logger.info(scrollbox.drag_damping_get())
          #return self.scrollbox
   
      #def generate_single_item(self, item):
          
          #canvas_obj = etk.Canvas()
          #edje_obj = EdjeObject(self.parent, self.EdjeFile, self.EdjeGroup)
          #canvas_obj.object_add(edje_obj.Edje)
          #edje_obj.Edje.signal_callback_add("send_all", "*" , self.send_signal)
          ### set text in text parts
          #for part, attribute in self.label_list:
              #if hasattr(item, attribute):
                  #value = getattr(item, attribute)
                  #if isinstance(value, tichy.Item):
                      #value = unicode(value.get_text())
                  #txt = unicode(value).encode('utf-8')
                  #edje_obj.Edje.part_text_set(part,txt)
      
          ###check for optional display elements
          #if edje_obj.Edje.data_get('attribute1') != None:
              #attribute = edje_obj.Edje.data_get('attribute1')
              #if edje_obj.Edje.data_get('attribute2') != None:
                  #item_cp = getattr(item,attribute)
                  #attribute = edje_obj.Edje.data_get('attribute2')
              #else:  
                  #item_cp = item
              #if edje_obj.Edje.data_get('value') == 'None':
                  #value = None
              #else:
                  #value = edje_obj.Edje.data_get('value')
              #signal = edje_obj.Edje.data_get('signal')
              #if attribute[-2] == "(":
                  #test = getattr(item_cp,attribute[:-2])()
              #else:
                  #test = getattr(item_cp,attribute)
              #if test == value:
                  #edje_obj.Edje.signal_emit(signal,'*')

          #return [item,edje_obj,canvas_obj]
      
      #def add_callback(self, signal, source, func):
          #self.callbacks.append([signal, source, func])
          #for i in self.items:
              #i[1].Edje.signal_callback_add(signal, source , func, i)

      #def send_signal(self, emission, signal, source):
          #for i in self.items:
              #if emission != i[1].Edje:
                  #i[1].Edje.signal_emit(source, signal)

      #def _renew_callbacks(self, *args, **kargs):
          #for cb in self.callbacks:
                #for i in self.items:
                    #i[1].Edje.signal_callback_add(cb[0], cb[1] , cb[2], i)

      #def _append_new(self, list, item, **kargs):
          #logger.info('append called')
          #item.connect('modified',self._redraw_view)
          #new_item = self.generate_single_item(item)
          #for cb in self.callbacks:
              #new_item[1].Edje.signal_callback_add(cb[0], cb[1] , cb[2], new_item)
          #self.box.prepend(new_item[2], etk.VBox.START, etk.VBox.EXPAND_FILL, 0)
          #self.items.insert(0,new_item)
          #self._redraw_view()
          ##self.sort()
          ##self._redraw_box()
          
      #def _remove_item(self, list, removed_item):
          #logger.info('remove called')
          #for item in self.items:
              #if item[0] is removed_item:
                  #index = item
                  #item[2].remove_all()
          
          #self.items.remove(index)
          #self._redraw_box()

      #def _redraw_view(self,*args,**kargs):
          #logger.info("list redrawing")
          
          #self.sort()
          #self.box.remove_all()
          
          #self.calc_value()
          
          #del self.items
          #self.items = []
          #for item in self.model:
              #single = self.generate_single_item(item)
              #self.box.append(single[2], etk.VBox.START, etk.VBox.EXPAND_FILL, 0)
              #self.items.append(single)
              ##item.connect('modified',self._redraw_view)

          #self._redraw_box()
          #self._renew_callbacks()

      #def _redraw_box(self,*args,**kargs):
          #logger.info('redrawing called')
          #self.sort()
          #self.box.redraw_queue()
          #if self.EdjeFrame != None:
              #self.EdjeFrame.Edje.signal_emit(str(len(self.model)),"python")
          #self.box.show_all()

      #def sort(self,*args,**kargs):
          #logger.info("list sorting")
          #self.model.sort(self._comp_fct)

      #def calc_value(self, *args, **kargs):
          #item_count = len(self.model)
          #pages = max( ( len( self.model ) - 1 ) / 6 + 1, 1 )
          #self.page_size = 1.0 / pages

      #def paging(self, delta):
          #new_value = delta * 360.0
          #length = len(self.model) * 60
          #old_value = self.vscrollbar.value_get()
          #if ((old_value + new_value) > length):
              #new_value = length
          #elif ((old_value + new_value) < 0.0):
              #new_value = 0.0
          #else:
              #new_value = old_value + new_value
          #logger.info("old: %f ,new: %f ,length: %d", old_value, new_value, length)
          #self.vscrollbar.value_set( new_value )
          #self.vscrollbar.redraw_queue()
