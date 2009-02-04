#    Paroli
#
#    copyright 2008 Openmoko
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

import e_dbus
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.evas
import ecore.x
import etk

import logging
logger = logging.getLogger('gui')

import tichy

class Widget(tichy.Object):
    def __init__(self, parent, etk_obj = None, item = None, expand = False, **kargs):
        self.etk_obj = etk_obj or etk.VBox()
        self.item = item
        self.parent = parent
        self.children = []
        self.expand = expand
        if self.parent:
            self.parent.get_contents_child().add(self)
        #self.show()
    def add(self, child):
        self.etk_obj.add(child.etk_obj)
        self.children.append(child)
    def get_evas(self):
        return self.parent.get_evas()
    def show(self):
        try:
            self.etk_obj.show_all()
        except Exception, e:
            pass

    def get_contents_child(self):
        return self

    def parent_as(self, cls):
        if isinstance(self.parent, cls):
            return self.parent
        return self.parent.parent_as(cls)

    def __get_window(self):
        return self.parent_as(Window)
    window = property(__get_window)

    def destroy(self):
        self.etk_obj.destroy()

    # No tags for this implementation
    def add_tag(self, tag):
        pass
    def remove_tag(self, tag):
        pass

class Window(Widget):
    def __init__(self, parent, w=480, h=580, **kargs):
        etk_obj = ecore.evas.SoftwareX11(w=w, h=h)
        etk_obj.callback_delete_request_set(self.delete_request)
        Widget.__init__(self, None, etk_obj=etk_obj)

    def delete_request(self,*args,**kargs):
        logger.info(str(args))
        self.emit('delete_request')

    def show(self):
        self.etk_obj.show()

    def destroy(self):
        self.etk_obj.hide()

class Screen(Window):
    """We don't use screen at all

    It doesn't make sense with etk backend.
    """

    def __init__(self, loop, painter, **kargs):
        pass

    def add(self, child):
        pass


class Box(Widget):
    def __init__(self, parent, axis=0, **kargs):
        if axis == 0:
            etk_obj = etk.HBox()
        else:
            etk_obj = etk.VBox()
        super(Box, self).__init__(parent, etk_obj=etk_obj, **kargs)

    def add(self, child):
        policy = etk.VBox.FILL
        if child.expand:
            policy = etk.VBox.EXPAND_FILL
        self.etk_obj.append(child.etk_obj, etk.VBox.START, policy, 0)

class Frame(Box):
    def __init__(self, parent, **kargs):
        super(Frame, self).__init__(parent, **kargs)

class Fixed(Widget):
    pass

class Table(Widget):
    pass

class Table(Widget):
    def __init__(self, parent, nb = 3, **kargs):
        self.nb = nb
        self.current = 0
        etk_obj = etk.Table(nb, 5, etk.Table.HOMOGENEOUS)
        super(Table, self).__init__(parent, etk_obj=etk_obj, **kargs)
    def add(self, child):
        x = self.current % self.nb
        y = self.current / self.nb
        self.etk_obj.attach_default(child.etk_obj, x, x, y, y)
        self.current += 1

class Scrollable(Widget):
    def __init__(self, parent, **kargs):
        etk_obj = etk.ScrolledView()
        super(Scrollable, self).__init__(parent, etk_obj=etk_obj, **kargs)
    def add(self, child):
        self.etk_obj.add_with_viewport(child.etk_obj)

class Button(Widget):
    def __init__(self, parent, **kargs):
        etk_obj = etk.Button()
        super(Button, self).__init__(parent, etk_obj=etk_obj, **kargs)
        self.etk_obj.connect('clicked', self.on_clicked)
    def on_clicked(self, *args):
        self.emit('clicked')

class Label(Widget):
    def __init__(self, parent, text, **kargs):
        etk_obj = etk.Label(text)
        super(Label, self).__init__(parent, etk_obj=etk_obj, **kargs)

    def __get_text(self):
        return self.etk_obj.get()
    def __set_text(self, value):
        self.etk_obj.set(value)
    text = property(__get_text, __set_text)

class Edit(Widget):
    def __init__(self, parent, item = None, **kargs):
        etk_obj = etk.Entry()
        super(Edit, self).__init__(parent, etk_obj=etk_obj, **kargs)


class Spring(Widget):
    def __init__(self, parent, expandable = True, **kargs):
        super(Spring, self).__init__(parent, expandable=expandable, **kargs)


class SurfWidget(Widget):
    pass

class ImageWidget(Widget):
    def __init__(self, parent, image, **kargs):
        self.image = image
        etk_obj = etk.Image()
        etk_obj.set_from_file(image.path)
        super(ImageWidget, self).__init__(parent, etk_obj=etk_obj, **kargs)



class ScrollableSlide(Widget):
    pass


class Painter(object):
    """We don't use Painter at all

    It doesn't make sense with etk backend.
    """
    def __init__(self, size, fullscreen = None):
        pass

class EventsLoop(object):

    def __init__(self):
        self.dbus_loop = e_dbus.DBusEcoreMainLoop()

    def run(self):
        #import ecore.x
        #ecore.c_ecore._event_mapping_register(3,ecore.x.EventWindowDestroy)
        #ecore.c_ecore.event_handler_add(3,self.moo)
        #m = ecore.x.on_window_destroy_add(self.moo)
        #print m.event_cls
        #print dir(m)
        ecore.main_loop_begin()

    def moo(self,*args,**kargs):
        print "here"
        return True

    def timeout_add(self, time, callback, *args):
        return ecore.timer_add(time / 1000., callback, *args)

    def source_remove(self, timer):
        timer.delete()

    def quit(self):
        ecore.main_loop_quit()

####ADDED by mirko

class EdjeObject(tichy.Object):
    """Base class for edje Elements used to generate application windows """
    def __init__(self, Parent, EdjeFile, EdjeGroup, EdjeWindows=None):
        #super(EdjeObject, self).__init__()
        self.Parent = Parent
        self.EdjeFile = EdjeFile
        self.EdjeGroup = EdjeGroup
        self.Evas = Parent.etk_obj.evas
        self.Edje = edje.Edje(self.Evas, file=self.EdjeFile, group=self.EdjeGroup)
        self.Edje.data['windows'] = []
        self.Windows = self.Edje.data['windows']
        self.EdjeWindows = EdjeWindows
        if EdjeWindows != None:
            EdjeWindows.append(self)

    def show(self,layer=2,*args,**kargs):
        self.Edje.layer_set(layer)
        self.Edje.show()

    def dehide(self,*args,**kargs):
        self.Edje.show()

    def add_callback(self, signal, source, callback):
        self.Edje.signal_callback_add(signal, source, callback)

    def data_add(self, key, data):
        if not self.Edje.data[key]:
            self.Edje.data[key] = data
        else:
            self.Edje.data[key].append(data)

    def signal(self, signal, source):
        self.Edje.signal_emit(signal, source)

    def hide(self,*args,**kargs):
        self.Edje.hide()

    def delete(self, emission=None, source=None, param=None):
        try:
          if self.Edje.data['windows'] != None:
            for i in self.Edje.data['windows']:
              i.delete()
        except Exception, e:
            dialog = tichy.Service('Dialog')
            logger.error(Exception, " ", e)
            dialog.error(self.Parent, e)
        
        if self.EdjeWindows != None:
            self.EdjeWindows.remove(self)
            
        self.Edje.delete()

class EdjeWSwallow(EdjeObject):
      """Use this if your EdjeObject has a swallow part, the delete method will take care of deleting it on close"""
      def __init__(self, Parent, EdjeFile, EdjeGroup, EdjeSwallow, EdjeWindows=None):
          self.Swallow = EdjeSwallow
          super(EdjeWSwallow, self).__init__(Parent, EdjeFile, EdjeGroup, EdjeWindows)
      
      def embed(self, child, box, part):
          embed = etk.Embed(self.Evas)
          embed.add(child)
          embed.show_all()
          self.Edje.part_swallow(part, embed.object)
          try:
              box.box.show_all()
          except Exception,e:
              dir(e)

      def delete(self, source=None, emission=None, param=None):
          
          self.Edje.part_swallow_get(self.Swallow).visible_set(0)
          self.Edje.part_swallow_get(self.Swallow).delete()
          
          try:
              if self.Edje.data['windows'] != None:
                for i in self.Edje.data['windows']:
                  i.delete()
          except Exception, e:
              dialog = tichy.Service('Dialog')
              logger.error(Exception, " ", e)
              dialog.error(self.Parent, e)
        
          if self.EdjeWindows != None:
              self.EdjeWindows.remove(self)
             
          self.Edje.delete()

class entry:
    """deprecated use Edit instead"""
    def __init__(self,text='Unknown',pw=False):
        self.entry = etk.Entry()
        self.entry.text = text
        self.entry.password_mode_set(False)

class edje_box:
    """deprecated"""
    def __init__(self,instance,dimension,scrollable):
        assert dimension in ['V', 'H']
        if dimension == 'V':
            self.box = etk.VBox()
        else:
            self.box = etk.HBox()

        if scrollable == 1:
            ##create scrolled view
            self.scrolled_view = etk.ScrolledView()
            ##add box to scrolled view object
            self.scrolled_view.add_with_viewport(self.box)
            ## hide scrollbars
            self.scrolled_view.policy_set(2, 2)
            ## make it dragable
            self.scrolled_view.dragable_set(1)
            ## make it non-bouncing
            self.scrolled_view.drag_bouncy_set(0)

        self.box.show()

    #def append(element,)

    def embed(self,instance,box,embed_object='instance.window_embed'):
        eval(embed_object + '.add(box)')
        eval(embed_object + '.show_all()')

class contact_list:
    """deprecated"""
    def __init__(self, items, box, main, edje_file, item_group, app_window, kind='contacts', arbit_window=None):
        self.items = items
        self.item_list = []
        self.edje_file = edje_file
        self.app_window = app_window
        self.item_group = item_group
        self.main = main
        self.box = box
        self.arbit_window = arbit_window
        self.item_status = "ORIGINAL"
        
        if kind == 'contacts':
            for i in items:
                name = i.name
                tel = i.tel
                self.generate_single_item_obj(name,tel,i)
        elif kind == 'msgs':
            for i in items:
                name = str(i.peer).encode('utf8')
                if str(i.status) == 'unread' and str(i.direction) == 'in':
                    tel = 'NEW! ' + str((i.text)).encode('utf8')
                elif str(i.status) == 'read' and str(i.direction) == 'out':
                    tel = '> ' + str((i.text)).encode('utf8')
                else :
                    tel = str((i.text)).encode('utf8')
                self.generate_single_item_obj(name,tel,i)
        elif kind == 'history':
            for i in items:
                name = i
                tel = i.timestamp
                self.generate_single_item_obj(name,tel,i)


        box.box.show()
        #return item_list

    def drag(self, emission, source, param):
        if self.item_status == "ORIGINAL":
            self.item_status = "DRAGGING"

    def drag_start(self, emission, source, param):
        if self.item_status == "ORIGINAL":
            self.item_status = "DRAGGING"

    def drag_stop(self, emission, source, param):
        part_name = param
        edje_obj = emission
        # Get the value to determine it's a rightward slide
        value = edje_obj.part_drag_value_get(part_name)
        if value[0] > 100:
            edje_obj.signal_emit('RIGHTWARD_SLIDE', '*');
            self.item_status = "OPEN_UP"
        else:
            if self.item_status == "DRAGGING":
                self.item_status = "ORIGINAL"
            elif self.item_status == "OPEN_UP":
                self.item_status = "CLOSING"

        # Set the value back to zero
        edje_obj.part_drag_value_set(part_name, 0.0, 0.0)


    def show_details(self, emission, source, param, contact, graphic_objects):
        if self.item_status == "ORIGINAL":
            self.app_window.show_details(emission, source, param, contact, graphic_objects)
        else:
            if self.item_status == "CLOSING":
                self.item_status = "ORIGINAL"
        

    def generate_single_item_obj(self,title,subtitle,contact):
        label_list = [(unicode(title),'label'),(str(subtitle),'label-number')]

        canvas_obj = etk.Canvas()
        edje_obj = edje.Edje(self.main, file=self.edje_file, group=self.item_group)
        canvas_obj.object_add(edje_obj)

        for e,i in label_list:
            edje_obj.part_text_set(i,e)

        self.box.box.append(canvas_obj, etk.VBox.START, etk.VBox.NONE, 0)

        if self.app_window.name == 'Paroli-Contacts':
            edje_obj.signal_callback_add("contact_details", "*", self.show_details, contact, [canvas_obj,edje_obj])
            edje_obj.signal_callback_add("create_message", "*", self.app_window.create_message,contact)
            edje_obj.signal_callback_add("drag", "*", self.drag)
            edje_obj.signal_callback_add("drag,start", "*", self.drag_start)
            edje_obj.signal_callback_add("drag,stop", "*", self.drag_stop)
          
        elif self.app_window.name == 'Paroli-Msgs':
            if self.item_group == 'message-contacts_item':
                edje_obj.signal_callback_add("add_contact", "*", self.app_window.add_recipient, contact, self.arbit_window)
            else:
                edje_obj.signal_callback_add("contact_details", "*", self.app_window.show_details, contact, canvas_obj)

        elif self.app_window.name == 'Paroli-I/O':
            edje_obj.signal_callback_add("call_contact", "*", self.app_window.call_contact, contact)
            edje_obj.signal_callback_add("create_message", "*", self.app_window.create_message,contact)
        else:
            edje_obj.signal_callback_add("call_contact", "*", self.app_window.call_contact)

        edje_obj.layer_set(5)
        edje_obj.show()

        if self.app_window.name == 'Paroli-I/O':
            self.item_list.append([unicode(title),edje_obj,canvas_obj,contact])
        else:
            self.item_list.append([unicode(title),edje_obj,canvas_obj])


class lists:
    """deprecated"""
    def generate_contacts_list(self,instance,main,scroller,box,app_window,item_group):
        item_list = []
        edje_file = '../tichy/gui_paroli/edje/paroli-in-tichy.edj'
        for i in scroller:
            label_list = [(unicode(i[0]),'label'),(str(i[1]).encode('utf8'),'label-number')]
            canvas_obj = etk.Canvas()
            edje_obj = edje.Edje(main, file=edje_file, group=item_group)
            canvas_obj.object_add(edje_obj)
            for e,i in label_list:
                edje_obj.part_text_set(i,e)

            box.box.append(canvas_obj, etk.VBox.START, etk.VBox.NONE, 0)

            edje_obj.signal_callback_add("*", "*", app_window.self_test)

            edje_obj.layer_set(5)
            edje_obj.show()
            item_list.append([unicode(i[0]),edje_obj,canvas_obj])
        return item_list
        box.box.show()

    def generate_list(self,instance,main,scroller,box,app_window,item_group):
        edje_file = '../tichy/gui_paroli/edje/paroli-in-tichy.edj'
        for i in range(len(scroller)):
            label_list = [('testos'+str(i+1),'label')]
            canvas_obj = etk.Canvas()
            edje_obj = edje.Edje(main, file=edje_file, group=item_group)
            canvas_obj.object_add(edje_obj)

            for e,i in label_list:
                edje_obj.part_text_set(i,e)

            hbox = etk.HBox()

            texts = [('Missed','255 0 0 255'),('at','255 255 255 255'),('15:35','255 255 255 255')]

            for n,i in texts:
                width = len(str(n)) * 13
                text_canvas = etk.Canvas()
                text_edj = edje.Edje(main, file=edje_file, group='history-label', size=(int(width),30))
                text_edj.part_text_set('text',n)
                text_edj.color_set(int(i.split(' ')[0]),int(i.split(' ')[1]),int(i.split(' ')[2]),int(i.split(' ')[3]))
                text_canvas.object_add(text_edj)
                hbox.append(text_canvas, etk.HBox.START, etk.HBox.NONE, 0)

            text_evas = etk.Embed(main)
            text_evas.add(hbox)
            text_evas.show_all()
            edje_obj.part_swallow('label-action',text_evas.object)
            instance.history_items.append([edje_obj,text_evas,canvas_obj])

            box.box.append(canvas_obj, etk.VBox.START, etk.VBox.NONE, 0)

            edje_obj.signal_callback_add("*", "*", app_window.self_test)
            edje_obj.layer_set(5)
            edje_obj.show()

        box.box.show()


class edje_gui():
    """deprecated"""
    def __init__(self, parent,group,edje_file='../tichy/gui_paroli/design/paroli-in-tichy.edj'):

        self.parent = parent
        self.group = group
        self.edje_file = edje_file
        self.edj = edje.Edje(self.parent.etk_obj.evas, file=self.edje_file, group=group)
        self.edj.size = parent.etk_obj.evas.size
        parent.etk_obj.data["edje"] = self.edj
        edje.frametime_set(1.0/30)

    def get_evas(self):
        return self.parent.etk_obj.evas

    def show(self):
        edje.frametime_set(1.0/30)
        self.edje.layer_set(2)
        self.edje.show()
        self.parent.etk_obj.activate()
        self.parent.etk_obj.show()

    def add(self, child,box, part):
        embed = etk.Embed(self.parent.etk_obj.evas)
        embed.add(child)
        embed.show_all()
        self.edj.part_swallow(part,embed.object)
        try:
            box.box.show_all()
        except Exception,e:
            dir(e)

    def close_window(self,orig,orig_parent,emission, source, param):
        orig.edj.delete()
        orig_parent.etk_obj.visibility_set(0)

    ##more generic

    def del_sign_from(self,orig,orig_parent,emission, source, param):
        logger.debug("del_sign_from called")
        value = emission.part_text_get(param)
        emission.part_text_set(param,value[:-1])

    def add_sign_to(self,orig,orig_parent,emission, source, param):
        logger.debug("add_sign_to called")
        part = param.split(',')[0]
        new_sign = param.split(',')[1]
        value = emission.part_text_get(part)
        if value == None:
            new = str(new_sign)
        else:
            new = str(value)+str(new_sign)
        emission.part_text_set(part,new)

    def clear_signs_in(self,orig,orig_parent,emission, source, param):
        emission.part_text_set(param,'')

    def wait_seconds(self,emission, source, param):

        data = [ param.split(',')[1] , emission]

        try:
            ecore.timer_add(float(param.split(',')[0]), self.arbitrary_signal,data)
        except Exception,e:
            logger.error("error in wait_second : %s", e)

    def arbitrary_signal(self,data):
        logger.debug("arbit sig")
        data[1].signal_emit(data[0],"*")
        return 0

    def delete(self,emission=None, source=None, param=None):
        self.edj.delete()

    def close_extra_child(self,emission, source, param):
        logger.debug("close extra child")
        if param != 'none':
            try:
                self.edj.part_swallow_get(param).visible_set(0)
            except Exception,e:
                logger.error("Error in close_extra_child: %s", e)

            try:
                self.edj.part_swallow_get(param).delete()
            except Exception,e:
                logger.error("Error in close_extra_child: %s", e)

        try:
            self.edj.delete()
        except Exception,e:
            logger.error("Error in close_extra_child: %s", e)

##UNUSED ONLY FOR REFERENCE

class main_edje(Widget):
    """deprecated"""
    def __init__(self, **kargs):
        self.etk_obj = ecore.evas.SoftwareX11(w=480, h=640)
        #Widget.__init__(self, None, etk_obj=etk_obj)
    def show(self):
        self.etk_obj.show()
        super(main_edje, self).show()

class edje_window():
    """deprecated"""
    def __init__(self, parent,group,app=None,phone=None,phone_book=None,edje_file='../tichy/gui_paroli/design/paroli-in-tichy.edj'):

        self.parent = parent
        self.app = app
        self.gsm = phone
        self.group = group
        self.phone_book = phone_book
        self.extra_child = None
        self.text_field = None
        self.name = 'none'
        if group == "tele.psd":
            self.edje_file = '../test/plugins/apps/paroli-dialer/dialer/tele.edj'
        else:
            self.edje_file = edje_file
        self.edj = edje.Edje(self.parent.etk_obj.evas, file=self.edje_file, group=group)
        self.edj.size = parent.etk_obj.evas.size
        parent.etk_obj.data["edje"] = self.edj
        edje.frametime_set(1.0/30)
        self.edj.signal_callback_add("*", "*", self.self_test)
        self.edj.layer_set(2)
        self.edj.show()

    def get_contents_child(self):
        return self

    def get_evas(self):
        return self.parent.etk_obj.evas

    def show(self):
        edje.frametime_set(1.0/30)
        self.edje.layer_set(2)
        self.edje.show()
        self.parent.etk_obj.activate()
        self.parent.etk_obj.show()

    def scroller(self):
        pass

    def add(self, child,box, part):
        embed = etk.Embed(self.parent.etk_obj.evas)
        embed.add(child)
        embed.show_all()
        self.edj.part_swallow(part,embed.object)
        try:
            box.box.show_all()
        except Exception,e:
            dir(e)

    def self_test(self,emission, source, param):
        try:
            eval(source + '(self,self.parent,emission, source, param)')
        except Exception, e:
            dir(e)

    def open_edje(self,orig,orig_parent,emission, source, param):
        logger.debug("open_edje called")
        new_edje = edje_window(orig_parent,param,orig.gsm,orig.phone_book)
        orig_parent.add(new_edje)
        orig.delete()

    def open_edje_above(self,orig,orig_parent,emission, source, param):
        logger.debug("open_edje_above called")
        new_edje = edje_window(orig_parent,param,orig.gsm,orig.phone_book)
        orig_parent.add(new_edje)

    def close_edje_above(self,orig,orig_parent,emission, source, param):
        emission.delete()

    def number_edit(self,orig,orig_parent,emission, source, param):
        logger.debug("number_edit called")
        value = emission.part_text_get("num_field-label")
        if value == None:
            new = str(param)
        else:
            new = str(value)+str(param)
        emission.part_text_set('num_field-label',new)

    def number_edit_del(self,orig,orig_parent,emission, source, param):
        logger.debug("number_edit_del called")
        value = emission.part_text_get("num_field-label")
        emission.part_text_set("num_field-label",value[:-1])

    def number_edit_add(self,orig,orig_parent,emission, source, param):
        logger.debug("number_edit_add called")

    def close_window(self,orig,orig_parent,emission, source, param):
        orig.edj.delete()
        orig_parent.etk_obj.visibility_set(0)

    def start_call(self,orig,orig_parent,emission, source, param):
        logger.debug("start_call called")
        number = emission.part_text_get("num_field-text")
        try:
            call = self.gsm.create_call(number)
            call_id = call.initiate()
            emission.part_text_set("active_call",str(call.id))
        except Exception, e:
            logger.error("Error in start_call : %s", e)

    def end_call(self,orig,orig_parent,emission, source, param):
        logger.debug("end call called")
        call_id = emission.part_text_get("active_call")
        self.gsm.gsm_call_iface.Release(int(call_id))

    def save_contact(self,orig,orig_parent,emission, source, param):
        try:
            self.app.save_number(orig,orig_parent,emission, source, param)
        except Exception,e:
            logger.error("Error in save_contact : %s", e)


    def num_field_pressed(self,orig,orig_parent,emission, source, param):
        curr_num = self.edj.part_text_get('num_field-text')
        if curr_num == None or len(curr_num) == 0:
            orig.app.load_phone_book(orig,orig_parent,emission, source, param)
        else:
            logger.debug("num_field not empty")
            orig.app.add_contact(orig,orig_parent,emission, source, param)

    def call_pressed(self,orig,orig_parent,emission, source, param):
        curr_num = self.edj.part_text_get('num_field-text')
        if curr_num == None or len(curr_num) == 0:
            logger.debug("num_field empty")
        else:
            logger.debug("num_field not empty")
            try:
                orig.app.calling(orig,orig_parent,emission, source, curr_num)
            except Exception, e:
                logger.error("Error in call_pressed : %s", e)

    def del_sign_from(self,orig,orig_parent,emission, source, param):
        logger.debug("del sign from called")
        value = emission.part_text_get(param)
        emission.part_text_set(param,value[:-1])

    def add_sign_to(self,orig,orig_parent,emission, source, param):
        logger.debug("add_sign_to called")
        part = param.split(',')[0]
        new_sign = param.split(',')[1]
        value = emission.part_text_get(part)
        if value == None:
            new = str(new_sign)
        else:
            new = str(value)+str(new_sign)
        emission.part_text_set(part,new)

    def clear_signs_in(self,orig,orig_parent,emission, source, param):
        emission.part_text_set(param,'')

    def wait_seconds(self,orig,orig_parent,emission, source, param):
        data = [ param.split(',')[1] , emission]

        try:
            ecore.timer_add(float(param.split(',')[0]), self.arbitrary_signal,data)
        except Exception,e:
            logger.error("Error in wait_seconds %s", e)

    def arbitrary_signal(self,data):
        logger.debug("arbit sig")
        data[1].signal_emit(data[0],"*")
        return 0

    def close_extra_child(self,orig,orig_parent,emission, source, param):
        logger.debug("close extra child")
        if param != 'none':
            try:
                self.edj.part_swallow_get(param).visible_set(0)
            except Exception,e:
                logger.error("Error in close_extra_child : %s", e)

            try:
                self.edj.part_swallow_get(param).delete()
            except Exception,e:
                logger.error("Error in close_extra_child : %s", e)

        try:
            self.edj.delete()
        except Exception,e:
            logger.error("Error in close_extra_child : %s", e)

class edje_gui():
    """deprecated"""
    def __init__(self, parent, group, edje_file='../tichy/gui_paroli/design/paroli-in-tichy.edj'):

        self.parent = parent
        self.group = group
        self.edje_file = edje_file
        self.edj = edje.Edje(self.parent.etk_obj.evas, file=self.edje_file, group=group)
        self.edj.size = parent.etk_obj.evas.size
        parent.etk_obj.data["edje"] = self.edj
        edje.frametime_set(1.0/30)

    def get_evas(self):
        return self.parent.etk_obj.evas

    def show(self):
        edje.frametime_set(1.0/30)
        self.edje.layer_set(2)
        self.edje.show()
        self.parent.etk_obj.activate()
        self.parent.etk_obj.show()

    def add(self, child, box, part):
        embed = etk.Embed(self.parent.etk_obj.evas)
        embed.add(child)
        embed.show_all()
        self.edj.part_swallow(part, embed.object)
        try:
            box.box.show_all()
        except Exception,e:
            dir(e)

    def close_window(self,orig,orig_parent,emission, source, param):
        orig.edj.delete()
        orig_parent.etk_obj.visibility_set(0)

    ##more generic

    def del_sign_from(self,orig,orig_parent,emission, source, param):
        logger.debug("del_sign_from called")
        value = emission.part_text_get(param)
        emission.part_text_set(param,value[:-1])

    def add_sign_to(self,orig,orig_parent,emission, source, param):
        logger.debug("add_sign_to called")
        part = param.split(',')[0]
        new_sign = param.split(',')[1]
        value = emission.part_text_get(part)
        if value == None:
            new = str(new_sign)
        else:
            new = str(value)+str(new_sign)
        emission.part_text_set(part,new)

    def clear_signs_in(self,orig,orig_parent,emission, source, param):
        emission.part_text_set(param,'')

    def wait_seconds(self,emission, source, param):

        data = [ param.split(',')[1] , emission]

        try:
            ecore.timer_add(float(param.split(',')[0]), self.arbitrary_signal,data)
        except Exception,e:
            logger.error("error in wait_second : %s", e)

    def arbitrary_signal(self,data):
        logger.debug("arbit sig")
        data[1].signal_emit(data[0],"*")
        return 0

    def delete(self,emission, source, param):
        self.edj.delete()

    def close_extra_child(self,emission, source, param):
        logger.debug("close extra child")
        if param != 'none':
            try:
                self.edj.part_swallow_get(param).visible_set(0)
            except Exception,e:
                logger.error("Error in close_extra_child: %s", e)

            try:
                self.edj.part_swallow_get(param).delete()
            except Exception,e:
                logger.error("Error in close_extra_child: %s", e)

        try:
            self.edj.delete()
        except Exception,e:
            logger.error("Error in close_extra_child: %s", e)
