#    Paroli
#
#    copyright 2008 OpenMoko
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

import os
import logging
logger = logging.getLogger('app.contacs')

import ecore.x
import tichy
from tichy import gui
import sys
#import dbus
#from dbus.mainloop.glib import DBusGMainLoop
#DBusGMainLoop(set_as_default=True)
from tichy.service import Service

class ContactsApp(tichy.Application):
    name = 'Paroli-Contacts'
    icon = 'icon.png'
    category = 'main' # So that we see the app in the launcher
    
    def run(self, parent=None, standalone=False):
        self.standalone = standalone
        
        ##create main edje object, the evas object used to generate edje objects
        #self.main = gui.main_edje()
        self.main = parent
        #self.main.show()
        ##set the title of the window
        self.main.etk_obj.title_set('Paroli Contacts')
        
        ##connect to tichy contacts service
        self.contact_service = Service('Contacts')
        self.phone_book = self.contact_service.contacts
        def cmp_by_name(x, y):
            return cmp(x.name, y.name)
        self.phone_book.sort(cmp_by_name)
        
        ##create empty contacts objects list
        self.contact_objects_list = None
        
        ##set edje file to be used
        ##TODO: make one edje file per plugin
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-contacts.edj')
        
        ##create application main window
        self.edje_obj = gui.edje_gui(self.main,'people',self.edje_file)
        
        ##create scrollable box for contacts list
        contacts_box = gui.edje_box(self,'V',1)
        
        ##create list and populate box
        #print dir(self.phone_book)
        self.contact_objects_list = gui.contact_list(self.phone_book,contacts_box,self.main.etk_obj.evas,self.edje_file,'contacts_item',self)
        
        ##add populated box to main window
        self.edje_obj.add(contacts_box.scrolled_view,contacts_box,"contacts-items")
        
        #self.edje_obj.edj.signal_callback_add("add_contact", "*", self.add_number_new_contact)
        self.edje_obj.edj.signal_callback_add("add_contact", "*", self.add_number_new_contact)
        self.edje_obj.edj.signal_callback_add("top_bar", "*", self.top_bar)
        #self.edje_obj.edj.signal_callback_add("mouse,move", "*", self.listen)
        if self.standalone:
            self.edje_obj.edj.size_set(480,600)
        self.edje_obj.edj.pos_set(0,40)
        self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.show()
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
        
        try: 
            contacts_box.box.show()
        except Exception,e:
            print e      
             
        yield tichy.Wait(self.main, 'back_Paroli-Contacts')
        
        ##remove all children -- edje elements 
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
    
    def listen(self, emission, source, param):
        print source
        print param
        print emission.part_drag_value_get('clickable_blocker')
    
    def top_bar(self,emission,source,param):
        print "doing self.main.emit('back')"
        self.main.emit('back')
    
    def call_contact(self, emission, source, param):
        number = emission.part_text_get('number-text')
        name = emission.part_text_get('name-text')
        caller_service = Service('Caller')
        my_call = caller_service.call(emission, number, name)
        my_call.start()
        try:
            emission.delete()
        except Exception,e:
            print e
    
    def show_details(self, emission, source, param, contact, graphic_objects):
        print "show details called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
        #number = emission.part_text_get('label-number')
        #name = emission.part_text_get('label')
        number = str(contact.tel)
        name = str(contact.name)
        info = str(contact.note) if hasattr(contact, 'note') else "" # The sim contact don't have a note
        new_edje = gui.edje_gui(self.main,'contacts_details',self.edje_file)
        new_edje.edj.part_text_set('number-text',number)
        new_edje.edj.part_text_set('name-text',name)
        
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        new_edje.edj.signal_callback_add("call_contact", "*", self.call_contact)
        new_edje.edj.signal_callback_add("close_details", "*", self._close)
        new_edje.edj.signal_callback_add("edit_number", "*", self.edit_number_type, contact,new_edje, graphic_objects)
        new_edje.edj.signal_callback_add("edit_name", "*", self.edit_name, contact, new_edje, graphic_objects)
        new_edje.edj.signal_callback_add("delete_contact", "*", self.delete_contact, contact, new_edje,emission, graphic_objects)
        new_edje.edj.layer_set(3)
        new_edje.edj.show()   
    
    def delete_contact(self,emission, source, param, contact, details_window,contacts_edje_obj, graphic_objects):
        print "delete contact called"
        graphic_objects[0].remove_all()
        details_window.edj.delete()
        contacts_service = Service('Contacts')
        contacts_service.remove(contact)
        
        
    def edit_number_type(self,emission, source, param, contact, details_window, graphic_objects):
        print "edit number type called"
        print str(graphic_objects)
        number = emission.part_text_get('number-text')
        
        new_edje = gui.edje_gui(self.main,'edit-number-type',self.edje_file)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("num_type_clicked", "*", self.edit_number, number, contact, details_window,new_edje, graphic_objects)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        #new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def edit_number(self,emission, source, param, number, contact, details_window, first_window, graphic_objects):
        print "edit number called"
        
        #number = emission.part_text_get('number-text')
        #last_window = emission
        name_dummy = None
        number_type = param
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        new_edje.edj.signal_callback_add("save-button", "*", self.save_contact_number, 'number' , number_type, contact, details_window, name_dummy, graphic_objects)
        new_edje.edj.signal_callback_add("save_successful", "*", first_window.delete)
        
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def add_number_new_contact(self,emission, source, param):
        print "add new number called"
        
        #number = emission.part_text_get('number-text')
        #me = 'mirko'
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_emit('new_contact_mode','*')
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        new_edje.edj.signal_callback_add("next-button", "*", self.add_name_new_contact,first_window=new_edje)
        
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def add_digit(self,emission,source,param):
        print "add digit called"
        new_sign = param
        value = emission.part_text_get('num_field-text')
        if value == None:
          new = str(new_sign)
        else:
          new = str(value)+str(new_sign)
          
        emission.part_text_set('num_field-text',new)
    
    def edit_name(self,emission, source, param, contact, first_window, graphic_objects):
        print "edit name called"
        
        name = emission.part_text_get('name-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        name_field = gui.entry(name,False)
        new_edje.text_field = name_field.entry
        box = gui.edje_box(self,'V',1)
        name_field.entry.focus()
        box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        new_edje.edj.signal_emit('new_contact_mode','*')
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("next_step", "*", self.edit_name_info, contact, first_window,new_edje, graphic_objects)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        new_edje.edj.signal_callback_add("save_successful", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", self.close_keyboard)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def edit_name_info(self,emission, source, param, contact, first_window, last_window, graphic_objects):
        print "edit info called"
        
        #name = emission.part_text_get('name-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        info_field = gui.entry('info',False)
        new_edje.text_field = info_field.entry
        box = gui.edje_box(self,'V',1)
        info_field.entry.focus()
        box.box.append(info_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.part_text_set('name-text','info')
        info = new_edje.text_field
        name = last_window.text_field
        #print name.text_get()
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_contact_number, 'name' , new_edje.text_field, contact, first_window, name, graphic_objects)
        new_edje.edj.signal_callback_add("close_w_textfield", "*", last_window.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", self.close_keyboard)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def add_name_new_contact(self,emission, source, param,first_window=None):
        print "add new name called"
        #print name
        number = emission.part_text_get('num_field-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        name_field = gui.entry('Name',False)
        name_field.entry.focus()
        new_edje.text_field = name_field.entry
        box = gui.edje_box(self,'V',1)
        box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("close_w_textfield", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_new_contact,name_object=new_edje,number=number,first_window=first_window)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        
        new_edje.edj.layer_set(4)
        new_edje.edj.show()
    
    def save_contact_number(self,emission,source,param, switch ,info, contact, details_window,name=None, graphic_objects=None):
        print "save_contact_number called"
        print name
        print str(graphic_objects)
        if switch == 'number':
          number = emission.part_text_get('num_field-text')
          contact.tel = number
          contact.tel.type = info
          details_window.edj.part_text_set('number-text', number)
          details_window.edj.part_text_set('number-info', info)
          graphic_objects[1].part_text_set('label-number', number)
          emission.signal_emit('contact_saved','*')
        elif switch == 'name':
          cinfo = info.text_get()
          cname = name.text_get()
          print dir(emission)
          contact.info = cinfo
          contact.name = cname
          details_window.edj.part_text_set('name-text', cname)
          details_window.edj.part_text_set('name-info', cinfo)
          graphic_objects[1].part_text_set('label', cname)
          emission.signal_emit('contact_name_edit_saved','*')
    
    def save_new_contact(self,emission, source, param,name_object=None,number=None,first_window=None):
        print "save new contact called"
        name = name_object.text_field.text_get()
        number = number
        contacts_service = Service('Contacts')
        
        try:
            contact = contacts_service.create(name=str(name),tel=str(number))
        except Exception,e:
            print e
        #emission.signal_emit('save-notice','*')
        name_object.edj.delete()
        contacts_service.add(contact)
        #print dir (self.contact_objects_list)
        self.contact_objects_list.generate_single_item_obj(name,number,contact)
        print self.contact_objects_list.box.box.children_get()
        self.contact_objects_list.box.box.redraw_queue()
        self.contact_objects_list.box.box.show_all()
        first_window.edj.delete()
        #print contacts_service.contacts
    
    def number_edit_del(self,emission, source, param):
        print "number_edit del called"
        value = emission.part_text_get("num_field-text")
        if len(value) != 0:
          emission.part_text_set("num_field-text",value[:-1])
    
    def _close(self,emission, source, param):
        emission.delete()
    
    def close_keyboard(self,*args):
        print "close keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
    
    def open_keyboard(self,*args):
        print "open keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)
        
    def on_del(self, w):
        self.text.value = self.text.value[:-1]
    
     ## step two (enter message)    
    def create_message(self, emission, source, param, contact):
        ##get numbers from dialpad
        numbers = contact.tel
        print numbers
        ##load main gui
        new_edje = gui.edje_gui(self.main,'create_message',self.edje_file)
        ## show main gui
        new_edje.edj.layer_set(3)
        new_edje.edj.show()  
        self.open_keyboard()
        text = ''
        textbox = gui.etk.TextView()
        textbox.size_request_set(200,180)
        textbox.textblock_get().text_set(text,0)
        #textbox.theme_file_set(self.edje_file)
        box = gui.edje_box(self,'V',1)
        box.box.append(textbox, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"message")
        textbox.focus()
        box.box.show_all()
        
        ##set window actions
        ##close window
        new_edje.edj.signal_callback_add("back", "*", new_edje.close_extra_child)
        ##go to next step
        new_edje.edj.signal_callback_add("send", "*", self.send_message, numbers, textbox, new_edje)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
    
    ##send message INCOMPLETE
    def send_message(self, emission, source, param, numbers, textbox, step_2):
        print "send message called"
        number = numbers
        text = textbox.textblock_get().text_get(0)
        try:
            step_2.close_extra_child(emission,source,param)
        except Exception,e : 
            print e
            
        message_service = tichy.Service('SMS')
        #for i in numbers:
        message = message_service.create(number,text,'out')
          #print type(message)
        send = message_service.send(message)
          #print type(send)
        send.start()
          #print "would send message: ", text, "to :", i
          #self.contact_objects_list.generate_single_item_obj(i,text,message)

        self.close_keyboard()
    
    def self_test(self,emission, source, param):
        print "emission: ", str(emission)
        print "source: ", str(source)
        print "param: ", str(param)
