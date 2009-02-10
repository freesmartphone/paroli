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
    layer = 0
    
    def run(self, parent=None, standalone=False):
        self.standalone = standalone
        
        ##create main edje object, the evas object used to generate edje objects
        #self.main = gui.main_edje()
        self.main = parent
        self.geometry = self.main.etk_obj.geometry_get()
        self.y = self.geometry[1]
        self.layerdict = {}
        
        ##connect to tichy contacts service
        self.contact_service = Service('Contacts')
        self.phone_book = self.contact_service.contacts
        def cmp_by_name(x, y):
            return cmp(x.name, y.name)
        self.phone_book.sort(cmp_by_name)
        
        ##create empty contacts objects list
        self.contact_objects_list = None
        
        ##set edje file to be used
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-contacts.edj')
        
        ##create application main window
        self.edje_obj = gui.edje_gui(self.main,'people',self.edje_file)
        
        ##create scrollable box for contacts list
        contacts_box = gui.edje_box(self,'V',1)
        
        ##create list and populate box
        self.contact_objects_list = gui.contact_list(self.phone_book, contacts_box, self.main.etk_obj.evas, self.edje_file, 'contacts_item', self)
        
        ##add populated box to main window
        self.edje_obj.add(contacts_box.scrolled_view,contacts_box,"contacts-items")
        self.edje_obj.edj.signal_callback_add("add_contact", "*", self.add_number_new_contact)
        self.edje_obj.edj.pos_set(0, self.y)
        #self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.layer_set(1)
        self.edje_obj.edj.show()
        self.close_keyboard()
        try: 
            contacts_box.box.show()
        except Exception,e:
            print e      
             
        yield tichy.Wait(self.main, 'back_Paroli-Contacts')
        
        ##remove all children -- edje elements 
        if self.main.etk_obj.title_get() != 'Home':
            for i in self.main.children:
                i.remove()
            self.main.etk_obj.hide()   
        else:
            print "Deleting Paroli-Contacts...."
            for i in self.layerdict:
                if i <= self.layer:
                    edj_obj = self.layerdict[i]
                    edj_obj.edj.delete()
            self.edje_obj.delete(None, None, None)
        self.close_keyboard()
        

#----------------------------------------------------------------------------#
    #
    # Layer control API
    #
    """ This is like treat the layer as the states for an application. 
        The state increases and decreases as the UI screen flows.
        Basically one state stands for a certain screen and an edje obj.
        By using a layerdict dictionary to keeping track of what layer the 
        application is at. then when the app being closed, it knows what 
        edje objs it's going to be deleted. 
        I think this is kind state machine mechanism. Though layer value is
        magic number. this can be improved. Even we can just use one layer
        for one application. That depends on whether the app needs or not. 
    """
    def show_on_layer(self, edje_obj, layer_no):
        self.layer = layer_no
        #self.layerdict[layer_no] = edje_obj
        edje_obj.layer_set(layer_no)
        edje_obj.pos_set(0, self.y)
        edje_obj.show()   

    def get_current_layer(self):
        return self.layer

    def get_current_ui_obj(self):
        return self.layerdict[self.layer]

    def get_ui_obj_by_index(self, layer_no):
        return self.layerdict[layer_no]

    def back_to_last_layer(self, emission, source, param):
        """ Pop out from the layer dict and Delete the edje on the current layer """
        edj_obj = self.layerdict.pop(self.layer)
        edj_obj.delete(None, None, None)
        self.layer = self.layer - 1 
        print "back to last layer ", self.layer

    def jump_back_to_layer(self, layer_no):
        """ Pop out from the layer dict and Delete the edje objs for multiple layers """
        for i in self.layerdict:
            if i > layer_no:
                edj_obj = self.layerdict[i]
                edj_obj.delete(None, None, None)
        for i in range(layer_no + 1, self.layer + 1):
            self.layerdict.pop(i)
        print "jump back to", layer_no        
        self.layer = layer_no
#----------------------------------------------------------------------------#
    

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

    # This is called by gui backend. 
    def show_details(self, emission, source, param, contact, contact_list_item):
        print "show details called"
        self.close_keyboard()
        number = str(contact.tel)
        name = str(contact.name)
        info = str(contact.note) if hasattr(contact, 'note') else "" # The sim contact don't have a note
        new_edje = gui.edje_gui(self.main,'contacts_details',self.edje_file)
        new_edje.edj.part_text_set('number-text',number)
        new_edje.edj.part_text_set('name-text',name)
        new_edje.edj.signal_callback_add("call_contact", "*", self.call_contact)
        new_edje.edj.signal_callback_add("close_details", "*", self.back_to_last_layer)
        new_edje.edj.signal_callback_add("edit_number", "*", self.edit_number_type, contact, new_edje, contact_list_item)
        new_edje.edj.signal_callback_add("edit_name", "*", self.edit_name, contact, contact_list_item)
        new_edje.edj.signal_callback_add("delete_contact", "*", self.delete_contact, contact, new_edje,emission, contact_list_item)
        self.layerdict[2] = new_edje
        self.show_on_layer(new_edje.edj, 2)
    
    def delete_contact(self,emission, source, param, contact, details_window,contacts_edje_obj, contact_list_item):
        print "delete contact called"
        contact_list_item[0].remove_all()
        details_window.edj.delete()
        contacts_service = Service('Contacts')
        contacts_service.remove(contact)
        
    def edit_number_type(self,emission, source, param, contact, details_window, contact_list_item):
        print "edit number type called"
        number = emission.part_text_get('number-text')
        new_edje = gui.edje_gui(self.main,'edit-number-type',self.edje_file)
        new_edje.edj.signal_callback_add("num_type_clicked", "*", self.edit_number, number, contact, details_window,new_edje, contact_list_item)
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        self.layerdict[3] = new_edje
        self.show_on_layer(new_edje.edj, 3)
    
    def edit_number(self,emission, source, param, number, contact, details_window, first_window, contact_list_item):
        print "edit number called"
        number_type = param
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        new_edje.edj.signal_callback_add("save-button", "*", self.save_contact_number_type, number_type, contact)
        new_edje.edj.signal_callback_add("save_successful", "*", first_window.delete)
        self.layerdict[4] = new_edje
        self.show_on_layer(new_edje.edj, 4)
    
    def add_number_new_contact(self,emission, source, param):
        print "add new number called"
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        new_edje.edj.signal_emit('new_contact_mode','*')
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        new_edje.edj.signal_callback_add("next-button", "*", self.add_name_new_contact)
        self.layerdict[2] = new_edje
        self.show_on_layer(new_edje.edj, 2)
    
    def add_digit(self,emission,source,param):
        print "add digit called"
        new_sign = param
        value = emission.part_text_get('num_field-text')
        if value == None:
          new = str(new_sign)
        else:
          new = str(value)+str(new_sign)
        emission.part_text_set('num_field-text',new)
    
    def edit_name(self,emission, source, param, contact, contact_list_item):
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
        new_edje.edj.signal_callback_add("next_step", "*", self.edit_name_info, contact, new_edje, contact_list_item)
        new_edje.edj.signal_callback_add("save_successful", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", self.close_keyboard)
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        self.layerdict[3] = new_edje
        self.show_on_layer(new_edje.edj, 3)
        self.open_keyboard()
    
    def edit_name_info(self,emission, source, param, contact, last_window, contact_list_item):
        print "edit info called"
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        info_field = gui.entry('info',False)
        new_edje.text_field = info_field.entry
        box = gui.edje_box(self, 'V', 1)
        info_field.entry.focus()
        box.box.append(info_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE, 0)
        new_edje.add(box.scrolled_view,box,"name-box")
        new_edje.edj.part_text_set('name-text','info')
        info = new_edje.text_field
        name = last_window.text_field
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_contact_name, contact, contact_list_item)
        new_edje.edj.signal_callback_add("save_successful", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", self.close_keyboard)
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        self.layerdict[4] = new_edje
        self.show_on_layer(new_edje.edj, 4)
    
    def add_name_new_contact(self,emission, source, param):
        print "add new name called"
        number = emission.part_text_get('num_field-text')
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        name_field = gui.entry('Name',False)
        name_field.entry.focus()
        new_edje.text_field = name_field.entry
        box = gui.edje_box(self,'V',1)
        box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_new_contact, number=number)
        self.layerdict[3] = new_edje
        self.show_on_layer(new_edje.edj, 3)
        self.open_keyboard()
    
    def save_contact_name(self, emission, source, param, contact, contact_list_item=None):
        print "save_contact_name called"
        info = self.get_current_ui_obj().text_field
        name = self.get_ui_obj_by_index(3).text_field
        cinfo = info.text_get()
        cname = name.text_get()
        contact.info = cinfo
        contact.name = cname
        details_window = self.get_ui_obj_by_index(2)
        details_window.edj.part_text_set('name-text', cname)
        details_window.edj.part_text_set('name-info', cinfo)
        contact_list_item[1].part_text_set('label', cname)
        self.jump_back_to_layer(2)
        self.close_keyboard()
    
    def save_contact_number_type(self, emission, source, param, type, contact):
        print "save_contact_number_type called"
        number = emission.part_text_get('num_field-text')
        contact.tel = number
        contact.tel.type = type
        details_window = self.get_ui_obj_by_index(2)
        details_window.edj.part_text_set('number-text', number)
        details_window.edj.part_text_set('number-info', type)
        emission.signal_emit('contact_saved','*')
        self.jump_back_to_layer(2)
        self.close_keyboard()

    def save_new_contact(self,emission, source, param, number=None):
        print "save new contact called"
        ui_obj = self.get_current_ui_obj()
        name = ui_obj.text_field.text_get()
        number = number
        contacts_service = Service('Contacts')
        try:
            contact = contacts_service.create(name=str(name),tel=str(number))
        except Exception,e:
            print e
        #emission.signal_emit('save-notice','*')
        contacts_service.add(contact)
        self.contact_objects_list.generate_single_item_obj(name,number,contact)
        print self.contact_objects_list.box.box.children_get()
        self.contact_objects_list.box.box.redraw_queue()
        self.contact_objects_list.box.box.show_all()
        self.jump_back_to_layer(1)
        self.close_keyboard()
    
    def number_edit_del(self,emission, source, param):
        print "number_edit del called"
        value = emission.part_text_get("num_field-text")
        if len(value) != 0:
          emission.part_text_set("num_field-text",value[:-1])
    
    def close_keyboard(self,*args):
        print "close keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
    
    def open_keyboard(self,*args):
        print "open keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)
        
    
     ## step two (enter message)    
    def create_message(self, emission, source, param, contact):
        print "create_message called"
        numbers = contact.tel
        print numbers
        ##load main gui
        new_edje = gui.edje_gui(self.main,'create_message',self.edje_file)
        self.open_keyboard()
        text = ''
        textbox = gui.etk.TextView()
        textbox.size_request_set(400,180)
        textbox.textblock_get().text_set(text,0)
        box = gui.edje_box(self,'V',1)
        box.box.append(textbox, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"message")
        textbox.focus()
        box.box.show_all()
        new_edje.edj.signal_callback_add("back", "*", self.back_to_last_layer)
        new_edje.edj.signal_callback_add("send", "*", self.send_message, numbers, textbox)
        self.layerdict[2] = new_edje
        self.show_on_layer(new_edje.edj, 2)
    
    ##send message INCOMPLETE
    def send_message(self, emission, source, param, numbers, textbox):
        print "send message called"
        number = numbers
        text = textbox.textblock_get().text_get(0)
        message_service = tichy.Service('SMS')
        #for i in numbers:
        message = message_service.create(number,text,'out')
        #print type(message)
        send = message_service.send(message)
        #print type(send)
        send.start()
        #self.contact_objects_list.generate_single_item_obj(i,text,message)
        self.close_keyboard()
        self.jump_back_to_layer(1)

