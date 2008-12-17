
import e_dbus
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.evas
import etk

import tichy

#import os
#import sys
#import e_dbus
#import evas
#import evas.decorators
#import edje
#import edje.decorators
#import ecore
#import ecore.evas
#import cairo
#from dbus import SystemBus, Interface
#from dbus.exceptions import DBusException
#from optparse import OptionParser
#import time
#import math

def Vect(x,y):
    return (x,y)
    
def Rect(pos, size):
    return (pos, size)

class Widget(tichy.Object):
    def __init__(self, parent, etk_obj = None, item = None, expand = False, **kargs):
        self.etk_obj = etk_obj or etk.VBox()
        self.item = item
        self.parent = parent
        self.children = []
        self.expand = expand
        if self.parent:
            self.parent.get_contents_child().add(self)
        self.show()
    def add(self, child):
        self.etk_obj.add(child.etk_obj)
        self.children.append(child)
    def get_evas(self):
        return self.parent.get_evas()
    def show(self):
        try: 
          self.etk_obj.show_all()
        except Exception, e :
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
        print "destroy called"
        
    # No tags for this implementation
    def add_tag(self, tag):
        pass
    def remove_tag(self, tag):
        pass
        
class Window(Widget):
    #def __init__(self, parent, **kargs):
        #etk_obj = etk.Window(w=480, h=640)
        #Widget.__init__(self, None, etk_obj=etk_obj)
    #def show(self):
        #self.etk_obj.show()
        #super(Window, self).show()

    def __init__(self, parent, **kargs):
        #etk_obj = etk.Window(w=480, h=640)
        etk_obj = ecore.evas.SoftwareX11(w=480, h=575)
        Widget.__init__(self, None, etk_obj=etk_obj)
    
    def show(self):
        self.etk_obj.show()
        super(Window, self).show()

    def destroy(self):
        pass

        
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
        # self.etk_obj = Canvas()
        # edje_obj = edje.Edje(parent.get_evas(), file='test.edj', group="frame")
        # self.etk_obj.object_add(edje_obj)
        super(Frame, self).__init__(parent, **kargs)
        # edje_obj.show()
        
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
    def __init__(self, size, fullscreen = None):
        pass
        
        
class EventsLoop(object):

    def __init__(self):
        self.dbus_loop = e_dbus.DBusEcoreMainLoop()

    def run(self):
        ecore.main_loop_begin()

    def timeout_add(self, time, callback, *args):
        return ecore.timer_add(time / 1000., callback, *args)

    def source_remove(self, timer):
        timer.delete()

    def quit(self):
        ecore.main_loop_quit()

####ADDED by mirko

class entry:
    def __init__(self,text='Unknown',pw=False):
        self.entry = etk.Entry()
        self.entry.text = text
        self.entry.password_mode_set(False)

class edje_box:
  
    def __init__(self,instance,dimension,scrollable):
        self.box = eval('etk.' + dimension + 'Box()')
        
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
      
    def embed (self,instance,box,embed_object='instance.window_embed'):
        eval(embed_object + '.add(box)')
        eval(embed_object + '.show_all()')
        
class contact_list:
    
    def __init__(self,items,box,main,edje_file,item_group,app_window,kind='contacts', arbit_window=None):
        #print items
        self.items = items
        self.item_list = []
        self.edje_file = edje_file
        self.app_window = app_window
        self.item_group = item_group
        self.main = main
        self.box = box
        self.arbit_window = arbit_window
        
        if kind == 'contacts':
            for i in items:
                #print dir(i)
                name = i.name
                tel = i.tel
                self.generate_single_item_obj(name,tel,i)
        elif kind == 'msgs':
            for i in items:
                #print dir(i)
                #if i[1] in ['read','unread']:
                name = str(i.peer).encode('utf8')
                #elif i[1] in ['sent','unsent']  :
                  #name = i[2]
                if str(i.status) == 'unread' and str(i.direction) == 'in':
                    tel = 'NEW! ' + str((i.text)).encode('utf8')
                elif str(i.status) == 'read' and str(i.direction) == 'out':
                    tel = '> ' + str((i.text)).encode('utf8')
                else :
                    tel = str((i.text)).encode('utf8')
                #[0:30]
                self.generate_single_item_obj(name,tel,i)
        elif kind == 'history':
            for i in items:
                #print dir(i)
                name = i
                tel = i.timestamp
                self.generate_single_item_obj(name,tel,i)


        box.box.show()
        #return item_list

    def generate_single_item_obj(self,title,subtitle,contact):
        print "generate_single_item_obj called"
        #if self.app_window.name == 'Paroli-Contacts':
          #label_list = [(unicode(name),'name-text'),(str(tel),'tel-mobile-text')]
        #else:
        label_list = [(unicode(title),'label'),(str(subtitle),'label-number')]
        
        canvas_obj = etk.Canvas()
        edje_obj = edje.Edje(self.main, file=self.edje_file, group=self.item_group)
        canvas_obj.object_add(edje_obj)
        
        #print str(tel)
        
        for e,i in label_list:
          edje_obj.part_text_set(i,e)
          
        self.box.box.append(canvas_obj, etk.VBox.START, etk.VBox.NONE, 0)

        #edje_obj.signal_callback_add("*", "*", self.app_window.self_test)
        if self.app_window.name == 'Paroli-Contacts':
          edje_obj.signal_callback_add("contact_details", "*", self.app_window.show_details, contact, [canvas_obj,edje_obj])
          
        elif self.app_window.name == 'Paroli-Msgs':
            if self.item_group == 'message-contacts_item':
              edje_obj.signal_callback_add("add_contact", "*", self.app_window.add_recipient, contact, self.arbit_window)
            else:
              edje_obj.signal_callback_add("contact_details", "*", self.app_window.show_details, contact, canvas_obj)
          
        elif self.app_window.name == 'Paroli-I/O':
            #import 
            edje_obj.signal_callback_add("call_contact", "*", self.app_window.call_contact, contact)
            #edje_obj.signal_callback_add("remove_self", "*", )
            #canvas_obj.on_destroyed(self.app_window.remove_entry, contact)
        else:
          edje_obj.signal_callback_add("call_contact", "*", self.app_window.call_contact)
          
        edje_obj.layer_set(5)
        edje_obj.show()
        
        if self.app_window.name == 'Paroli-I/O':
            self.item_list.append([unicode(title),edje_obj,canvas_obj,contact])
        else:
            self.item_list.append([unicode(title),edje_obj,canvas_obj])
        
        
class lists:
    def generate_contacts_list(self,instance,main,scroller,box,app_window,item_group):
        #scroller = eval('instance.' + list_type + '_scroller')
        #box = eval('instance.' + list_type + '_box.box')
        item_list = []
        edje_file = '../tichy/gui_paroli/edje/paroli-in-tichy.edj'
        for i in scroller:
            #label_list = [(i[1].encode('utf8'),'label'),(i[2].encode('utf8'),'label-number')]
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
        #eval('instance.' + list_type  +'_box_outer_edje.object.part_swallow("' + list_type  +'-items", instance.' + list_type  +'_embed.object)')
        #eval('instance.' + list_type  +'_box.box.show()')

    def generate_list(self,instance,main,scroller,box,app_window,item_group):
        #scroller = eval('instance.' + list_type + '_scroller')
        #box = eval('instance.' + list_type + '_box.box')
        edje_file = '../tichy/gui_paroli/edje/paroli-in-tichy.edj'
        for i in range(len(scroller)):
            #print i
            label_list = [('testos'+str(i+1),'label')]
            canvas_obj = etk.Canvas()
            edje_obj = edje.Edje(main, file=edje_file, group=item_group)
            canvas_obj.object_add(edje_obj)
            
            for e,i in label_list:
                edje_obj.part_text_set(i,e)
              #print e + i
              
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
    
            #if list_type == 'contacts':
            edje_obj.signal_callback_add("*", "*", app_window.self_test)
            #elif edje_group == 'history_item':
            #edje_obj.signal_callback_add("mouse,clicked,1", "*", instance.self_test)
            edje_obj.layer_set(5)
            edje_obj.show()
            
        box.box.show()

class main_edje(Widget):
    def __init__(self, **kargs):
        #etk_obj = etk.Window(w=480, h=640)
        etk_obj = ecore.evas.SoftwareX11(w=480, h=575)
        Widget.__init__(self, None, etk_obj=etk_obj)
    def show(self):
        self.etk_obj.show()
        super(main_edje, self).show()

class edje_window():
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
        print "scroller"

    def add(self, child,box, part):
        #print dir(child)
        embed = etk.Embed(self.parent.etk_obj.evas)
        embed.add(child)
        embed.show_all()
        #print dir(embed)
        print embed.is_visible()
        #print dir(child)
        #print dir(self.edj)
        print self.edj.part_exists(part)
        #print self.edj.part_exists("contacts-it")
        self.edj.part_swallow(part,embed.object)
        #for i in child.children:
          #print dir(i)
          #i.show_all()
          #i.show()
          #for e in i.children :
            #print "child of child"
            #print dir(e)
            #print e.is_visible()
            #for f in i.children :
              #print "child of childs child"
              #print dir(f)
              #print f.is_visible()
        #self.edj.part_swallow('contacts-items',box.box)
        try:
          box.box.show_all()
        except Exception,e:
          dir(e)
        
    def self_test(self,emission, source, param):
        #print "self test in init called"
        print source
        #print param
        #print emission
        #print dir(self.app)
        #print dir(emission)
        #source = source.startswith('self.') and source[5:] or source
        #if hasattr(self,source):
            #getattr(self,source)(self,self.parent,emission, source, param) 
        try:
            eval(source + '(self,self.parent,emission, source, param)')
        except Exception, e:
            dir(e)
            #print e
        
    
    
    def open_edje(self,orig,orig_parent,emission, source, param):
        print "open_edje called"
        
        new_edje = edje_window(orig_parent,param,orig.gsm,orig.phone_book)
        orig_parent.add(new_edje)
        orig.delete()
        
    def open_edje_above(self,orig,orig_parent,emission, source, param):
        print "open_edje called"
        
        new_edje = edje_window(orig_parent,param,orig.gsm,orig.phone_book)
        orig_parent.add(new_edje)
        
    def close_edje_above(self,orig,orig_parent,emission, source, param):
        emission.delete()
        
    def number_edit(self,orig,orig_parent,emission, source, param):
        print "number_edit called"
        value = emission.part_text_get("num_field-label")
        if value == None:
          new = str(param)
        else:
          new = str(value)+str(param)
        emission.part_text_set('num_field-label',new)    
        
    def number_edit_del(self,orig,orig_parent,emission, source, param):
        print "number_edit called"
        value = emission.part_text_get("num_field-label")
        emission.part_text_set("num_field-label",value[:-1])
        
    def number_edit_add(self,orig,orig_parent,emission, source, param):
        print "number_edit_add called"
    
    def close_window(self,orig,orig_parent,emission, source, param):
        orig.edj.delete()
        orig_parent.etk_obj.visibility_set(0)
    
    def start_call(self,orig,orig_parent,emission, source, param):
        print "start call called"
        number = emission.part_text_get("num_field-text")
        try:
            call = self.gsm.create_call(number)
            call_id = call.initiate()
            emission.part_text_set("active_call",str(call.id))
            print emission.part_text_get("active_call")
            print "start_call called to:", number
        except Exception, e:
            print e
          
    def end_call(self,orig,orig_parent,emission, source, param):
        print "end call called"
        call_id = emission.part_text_get("active_call")
        self.gsm.gsm_call_iface.Release(int(call_id))

    def save_contact(self,orig,orig_parent,emission, source, param):
        try:
          self.app.save_number(orig,orig_parent,emission, source, param)
        except Exception,e:
          print e
        

    def num_field_pressed(self,orig,orig_parent,emission, source, param):
        curr_num = self.edj.part_text_get('num_field-text')
        if curr_num == None or len(curr_num) == 0:
          orig.app.load_phone_book(orig,orig_parent,emission, source, param)
        else:
          print "num_field not empty"
          #number = emission.part_text_get('num_field-text')
          #print number
          orig.app.add_contact(orig,orig_parent,emission, source, param)
          #try:
            #new_edje = edje_window(orig_parent,'save-number',orig.gsm,orig.phone_book)
            #new_edje.edj.part_text_set('number',number)
            #entry = etk.Entry()
            #entry.text = "Name"
            #entry.password_mode_set(False)
            #new_edje.text_field = entry
            #box = edje_box(self,'V',1)
            #box.box.append(entry, etk.VBox.START, etk.VBox.NONE,0)
            #new_edje.add(box.scrolled_view,box,"name-box")
            #box.box.show_all()
            #orig_parent.add(new_edje)
          #except Exception,e:
            #print e

    def call_pressed(self,orig,orig_parent,emission, source, param):
        curr_num = self.edj.part_text_get('num_field-text')
        if curr_num == None or len(curr_num) == 0:
          #orig.app.load_phone_book(orig,orig_parent,emission, source, param)
          print "num_field empty"
        else:
          print "num_field not empty"
          #number = emission.part_text_get('num_field-text')
          #print number
          try:
            orig.app.calling(orig,orig_parent,emission, source, curr_num)
          except Exception, e:
            print e
          #try:
            #new_edje = edje_window(orig_parent,'save-number',orig.gsm,orig.phone_book)
            #new_edje.edj.part_text_set('number',number)
            #entry = etk.Entry()
            #entry.text = "Name"
            #entry.password_mode_set(False)
            #new_edje.text_field = entry
            #box = edje_box(self,'V',1)
            #box.box.append(entry, etk.VBox.START, etk.VBox.NONE,0)
            #new_edje.add(box.scrolled_view,box,"name-box")
            #box.box.show_all()
            #orig_parent.add(new_edje)
          #except Exception,e:
            #print e

    ##more generic
    
    def del_sign_from(self,orig,orig_parent,emission, source, param):
        print "del sign from called"
        value = emission.part_text_get(param)
        emission.part_text_set(param,value[:-1])
      
    def add_sign_to(self,orig,orig_parent,emission, source, param):
        print "add_sign_to called"
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

    #def save_contact(self,orig,orig_parent,emission, source, param):
        #print "save contacts called"
        #number = emission.part_text_get('number')
        #print number
        #print dir(orig)
        #print dir(orig.text_field)
        #name = orig.text_field.text_get()
        #print name
        
        #print dir(name)
        
    #def call_contact(self,orig,orig_parent,emission, source, param):
        #if param == 'tele':
          #number = emission.part_text_get('label-number')
          #name = emission.part_text_get('label')
          ##print name, number
          ##print "self: ",dir(self.extra_child)
          ##print self.group
          ##print "self x-child", dir(self.extra_child.edj)
          ##print self.extra_child.edj.part_swallow_get('contacts-items')
          ##print dir(self.extra_child.edj.part_swallow_get('contacts-items'))
          #self.extra_child.edj.part_swallow_get('contacts-items').visible_set(0)
          #self.extra_child.edj.part_swallow_get('contacts-items').delete()
          ##print "emission.parent.parent: ",dir(emission.parent.parent)
          ##print "emission.parent.parent.parent: ",dir(emission.parent.parent.parent)
          ##print orig.group
          ##print "orig.edj: ",dir(orig.edj)
          #orig.edj.part_text_set('num_field-text',name)
          #print "dialing ", number
          ##emission.parent.parent.delete()
          ##try:
            ##self.extra_child.edj.hide()
          ##except Exception,e:
            ##print e
          
          ##try:
            ##obj = self.extra_child.edj.part_object_get('contacts-items')
            ##self.extra_child.edj.part_unswallow(obj)
            ##print dir(obj)
            ##obj.delete()
          ##except Exception,e:
            ##print e
          #orig.edj.signal_emit('call_begin',"*")
          ##try:
            ##self.close_extra_child(orig,orig_parent,emission, source, 'contacts-items')
          ##except Exception,e:
            ##print e
            
          #try:
              #self.extra_child.edj.delete()
          #except Exception,e:
              #print e
          
          #caller_service = Service('Caller')
          #yield caller_service.call(self.edj, number)
          
          #print dir(orig_parent)
    
    def wait_seconds(self,orig,orig_parent,emission, source, param):
        
        #print param.split(',')[0]
        #print param.split(',')[1]
        #print param.split(',')[2]
          
        #print emission.data
        
        data = [ param.split(',')[1] , emission]
        
        try:
          ecore.timer_add(float(param.split(',')[0]), self.arbitrary_signal,data)  
        except Exception,e:
          print e
    
    def arbitrary_signal(self,data):
        print "arbit sig"
        data[1].signal_emit(data[0],"*")
        #emission.signal_emit('close_save_window','*')
        return 0
    
    def close_extra_child(self,orig,orig_parent,emission, source, param):
        print "close extra child"
        if param != 'none':
          print "param != none"
          #for i in param.split(','):
          print param
          try:
            self.edj.part_swallow_get(param).visible_set(0)
          except Exception,e:
            print e
          
          try:
            self.edj.part_swallow_get(param).delete()
          except Exception,e:
            print e
              
        try:
          self.edj.delete()
        except Exception,e:
          print e
          
          
class edje_gui():
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
        print "del sign from called"
        value = emission.part_text_get(param)
        emission.part_text_set(param,value[:-1])
      
    def add_sign_to(self,orig,orig_parent,emission, source, param):
        print "add_sign_to called"
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
          print e
    
    def arbitrary_signal(self,data):
        print "arbit sig"
        data[1].signal_emit(data[0],"*")
        return 0
    
    def delete(self,emission, source, param):
        self.edj.delete()
        
    def close_extra_child(self,emission, source, param):
        print "close extra child"
        if param != 'none':
          print "param != none"
          print param
          try:
            self.edj.part_swallow_get(param).visible_set(0)
          except Exception,e:
            print e
          
          try:
            self.edj.part_swallow_get(param).delete()
          except Exception,e:
            print e
              
        try:
          self.edj.delete()
        except Exception,e:
          print e
