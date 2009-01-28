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
logger = logging.getLogger('app.paroli-msgs')

import tichy
from tichy import gui
import sys
#import dbus
#from dbus.mainloop.glib import DBusGMainLoop
#DBusGMainLoop(set_as_default=True)
from tichy.service import Service
import dbus
import ecore
import ecore.evas

#class message_obj:
    #def __init__(self,dbus_obj):
      #self.id = dbus_obj[0]
      #self.status = dbus_obj[1]
      #self.sender = dbus_obj[2]
      #self.text = dbus_obj[3].encode('utf8')
      #if self.status in ['read','unread']:
        #self.time = dbus_obj[4]['timestamp']
      #self.direction = dbus_obj[4]['direction']
      

class ContactsApp(tichy.Application):
    name = 'Paroli-Msgs'
    icon = 'icon.png'
    category = 'launcher' # So that we see the app in the launcher
    
    def run(self, parent, text = ""):
        self.standalone = tichy.Text.as_type(text)
        
        ##create main edje object, the evas object used to generate edje objects
        self.main = parent
        
        ##set the title of the window
        if self.main.etk_obj.title_get() != 'Home':
            self.main.etk_obj.title_set('Paroli Msgs')
        
        self.edje_objects = []
        ##direct connection to framework -- ONLY for TESTING
        
        #bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        #self.gsm = bus.get_object('org.freesmartphone.ogsmd','/org/freesmartphone/GSM/Device')
        #self.gsm_service = tichy.Service('GSM')
        self.msgs_service = tichy.Service('Messages')
        inbox = self.msgs_service.inbox
        outbox = self.msgs_service.outbox
        all_list = self.msgs_service.messages
        
        def comp(m1, m2):
            return cmp(m2.timestamp, m1.timestamp)
        
        all_list.sort(comp)
        #for e in all_list:
          #print e
          
        messages = all_list
        
        ##connect to tichy's contacts service
        self.contact_service = Service('Contacts')
        
        ##get contacts list
        self.phone_book = self.contact_service.contacts
        
        ## list used for messages TODO : Rename
        self.contact_objects_list = None
        
        ##set edje file to be used
        ##TODO: make one edje file per plugin
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-msgs.edj')
        
        ##create application main window
        self.edje_obj = gui.edje_gui(self.main,'messages',self.edje_file)
        
        ##create scrollable box for contacts list
        contacts_box = gui.edje_box(self,'V',1)
        
        ##create list and populate box
        #print dir(self.phone_book)
        self.contact_objects_list = gui.contact_list(messages,contacts_box,self.main.etk_obj.evas,self.edje_file,'message_item',self,'msgs')
        
        ##add populated box to main window
        self.edje_obj.add(contacts_box.scrolled_view,contacts_box,"message-items")
        
        self.edje_obj.edj.signal_callback_add("create_message", "*", self.create_message)
        #self.edje_obj.edj.signal_callback_add("add_contact", "*", self.add_number_new_contact)
        self.edje_obj.edj.signal_callback_add("top_bar", "*", self.top_bar)
        self.edje_obj.edj.layer_set(2)
        if self.standalone == 1:
            self.edje_obj.edj.size_set(480,600)
        self.edje_obj.edj.pos_set(0,40)
        self.edje_obj.edj.show()
        self.edje_objects.append(self.edje_obj)
        
        try: 
            contacts_box.box.show()
        except Exception,e:
            logger.error(e)      
             
        yield tichy.Wait(self.main, 'back_Paroli-Msgs')
        ##remove all children -- edje elements 
        if self.standalone == 1:
            for i in self.edje_objects:
                i.delete(None,None,None)
        else:    
            for i in self.main.children:
                  i.remove()
            self.main.etk_obj.hide()   # Don't forget to close the window  
    
    ##functions for message app
    ##create new message
    ## step one (enter recipients)
    def create_message(self, emission, source, param, original_message=None, text=''):
        #print dir(emission)
        print "create message called"
        ##load main gui
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        
        ##set dialpad value to '' to not have NoneType problems
        new_edje.edj.part_text_set('num_field-text','')
        ## show main gui
        new_edje.edj.layer_set(3)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()   
        ##add num-pad actions
        ##delete digit
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        ##add digit
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        ##add window actions
        ##close window
        new_edje.edj.signal_callback_add("close_details", "*", self._close)
        ##add contact from phonebook
        new_edje.edj.signal_callback_add("num_field_pressed", "*", self.load_phone_book)
        ##go to next step
        new_edje.edj.signal_callback_add("next-button", "*", self.create_message_2, new_edje,'num_field-text',text, original_message)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
        
    ## step two (enter message)    
    def create_message_2(self, emission, source, param, step_1, part_text_field='num_field-text',message='', original_message=''):
        ##get numbers from dialpad
        numbers = emission.part_text_get(part_text_field).split(' ')
        print numbers
        ##load main gui
        new_edje = gui.edje_gui(self.main,'create_message',self.edje_file)
        ## show main gui
        new_edje.edj.layer_set(3)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()  
        self.open_keyboard()
        text = message
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
        new_edje.edj.signal_callback_add("send", "*", self._on_send_message, numbers, textbox, step_1, new_edje, original_message)
        new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
    
    
    
    ##show message details
    def show_details(self, emission, source, param, message, canvas_obj):
        print "show details called"
        time = message.timestamp
        text = str(message.text).encode('utf8')
        print text
        new_edje = gui.edje_gui(self.main,'message_details',self.edje_file)
        new_edje.edj.part_text_set('name-text',str(message.peer).encode('utf8'))
        new_edje.edj.part_text_set('name-info',str(time))
        new_edje.edj.part_text_set('number-text',str(message.peer.value).encode('utf8'))
        new_edje.edj.part_text_set('message-text',text)
        new_edje.edj.signal_callback_add("reply", "*", self.reply, message, new_edje)
        new_edje.edj.signal_callback_add("forward", "*", self.forward, message, new_edje)
        new_edje.edj.signal_callback_add("close_details", "*", self._close)
        new_edje.edj.signal_callback_add("delete_message", "*", self.delete_message, message, new_edje,emission, canvas_obj)
        new_edje.edj.signal_callback_add("top-bar", "*", self.top_bar)
        message.read()
        new_edje.edj.layer_set(3)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()   

    def _on_send_message(self, emission, source, param, numbers, textbox, step_1, step_2, original_message=None):
        """Called when the user click the send button

        The function will simply start the send_message tasklet
        """
        self.send_message(emission, source, param, numbers, textbox, step_1, step_2, original_message).start()
    
    @tichy.tasklet.tasklet
    def send_message(self, emission, source, param, numbers, textbox, step_1, step_2, original_message=None):
        """tasklet that performs the sending process"""
        logger.debug("send message called")
        numbers = numbers
        text = textbox.textblock_get().text_get(0)

        try:
            step_2.close_extra_child(emission,source,param)
            step_1.delete(emission,source,param)
            if original_message != None:
                original_message.delete(emission, source, param)
            
            message_service = tichy.Service('SMS')
            for i in numbers:
                message = message_service.create(number=i, text=text, direction='out')
                logger.info("would send message: %s to : %s", text, i)
                yield message_service.send(message)
                self.contact_objects_list.generate_single_item_obj(i,text,message)

            self.contact_objects_list.box.box.redraw_queue()
            self.contact_objects_list.box.box.show_all()
            self.close_keyboard()
        except Exception, ex:
            logger.error("Got error %s", ex)
            # XXX: at this point we should show an error box or do something
        
    ##delete message INCOMPLETE
    def delete_message(self,emission, source, param, message, details_window, messages_edje_obj, canvas_obj):
        print "delete message called"
        canvas_obj.remove_all()
        details_window.edj.delete()
        messages_service = Service('Messages')
        #if message.direction == 'in':
        messages_service.delete_message(message)
        #else:
            #messages_service.outbox.remove(message)
    
    ##reply to message INCOMPLETE
    def reply(self, emission, source, param, message, details_window):
        print "reply called, to number: ", str(message.peer).encode('utf8')
        self.create_message_2(emission, source, param, details_window, 'number-text')
    
    ##forward message INCOMPLETE
    def forward(self, emission, source, param, message, original_message):
        text = str(message.text).encode('utf8')
        print "forward called, of message: ", text
        self.create_message(emission, source, param, original_message, text)
    
    ##general functions on module
    ##close window
    def _close(self,emission, source, param):
        emission.delete()
    
    ##load phonebook
    def load_phone_book(self, emission, source, param):
        print "load phone book called"
        self.close_keyboard()
        try:
            new_edje = gui.edje_gui(self.main,'messages-people',self.edje_file)
            #new_edje.name = 'messages_phonebook'
            new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
            new_edje.edj.name_set('contacts_list')
        except Exception,e:
            print e
        try:
            self.extra_child = new_edje
            new_edje.edj.layer_set(3)
            if self.standalone == 1:
                new_edje.edj.size_set(480,600)
            new_edje.edj.edj.pos_set(0,40)
            new_edje.edj.show()
        except Exception,e:
            print e
        print "done"
        try:
            contacts_box = gui.edje_box(self,'V',1)
        except Exception,e:
            print e
        print "done2"
          
        try: 
            self.contact_objects_list = gui.contact_list(self.phone_book,contacts_box,self.main.etk_obj.evas,self.edje_file,'message-contacts_item',self, 'contacts' , emission)
        except Exception,e:
            print e 
        print "done3"
        
        try: 
            to_2_swallowed = contacts_box.scrolled_view
        except Exception,e:
            print e 
        print "done4"
        
        try: 
            #print "new_edje.add(to_2_swallowed,contacts_edje)"
            new_edje.add(to_2_swallowed,contacts_box,"items")
        except Exception,e:
            print e 
        print "done5"
        
        try: 
            contacts_box.box.show()
        except Exception,e:
            print e 
        print "done6"
    
    ##add contact to recipients
    def add_recipient(self, emission, source, param, contact, dial_pad):
        print "add recipient called"
        old = dial_pad.part_text_get('num_field-text')
        if len(old) == 0:
            new = str(contact.tel)
        else:
            new = old + ' ' + str(contact.tel)
        
        dial_pad.part_text_set('num_field-text', new)
        self.extra_child.close_extra_child(emission, source, param)
        #self.open_keyboard()
        #self.top_bar(self.extra_child.edj, source, param)
    
    ##add digit on dialpad like window
    def add_digit(self,emission, source, param):
        print "add digit called"
        new_sign = param
        value = emission.part_text_get('num_field-text')
        if value == None:
            new = str(new_sign)
        else:
            new = str(value)+str(new_sign)
          
        emission.part_text_set('num_field-text',new)
    
    ##delete digit on dialpad like window
    def number_edit_del(self,emission, source, param):
        print "number_edit del called"
        value = emission.part_text_get("num_field-text")
        if len(value) != 0:
            emission.part_text_set("num_field-text",value[:-1])
    
    ##top bar delete calls
    def top_bar(self,emission,source,param):
        self.main.emit('back')
    
    def close_keyboard(self,*args):
        print "close keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
    
    def open_keyboard(self,*args):
        print "open keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)
    
    
    def listen(self, emission, source, param):
        print source
        print param
        print emission.part_drag_value_get('clickable_blocker')
    
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

    def edit_number_type(self,emission, source, param, contact, details_window):
        print "edit number type called"
    
        number = emission.part_text_get('number-text')
        
        new_edje = gui.edje_gui(self.main,'edit-number-type',self.edje_file)
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("num_type_clicked", "*", self.edit_number, number, contact, details_window,new_edje)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        #new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()
    
    def edit_number(self,emission, source, param, number, contact, details_window,first_window):
        print "edit number called"
        
        #number = emission.part_text_get('number-text')
        #last_window = emission
        number_type = param
        new_edje = gui.edje_gui(self.main,'dialpad_numbers',self.edje_file)
        new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        new_edje.edj.signal_callback_add("back", "*", new_edje.delete)
        new_edje.edj.signal_callback_add("add_digit", "*", self.add_digit)
        new_edje.edj.signal_callback_add("save-button", "*", self.save_contact_number, 'number' , number_type, contact, details_window)
        new_edje.edj.signal_callback_add("save_successful", "*", first_window.delete)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
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
        new_edje.edj.signal_callback_add("next-button", "*", self.add_name_new_contact,first_window=new_edje)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()
    

    
    def edit_name(self,emission, source, param, contact, first_window):
        print "edit name called"
        
        name = emission.part_text_get('name-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        name_field = gui.entry(name,False)
        new_edje.text_field = name_field.entry
        box = gui.edje_box(self,'V',1)
        box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        new_edje.edj.signal_emit('new_contact_mode','*')
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("next_step", "*", self.edit_name_info, contact, first_window,new_edje)
        new_edje.edj.signal_callback_add("close_w_textfield", "*", new_edje.close_extra_child)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()
    
    def edit_name_info(self,emission, source, param, contact, first_window, last_window):
        print "edit info called"
        
        #name = emission.part_text_get('name-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        info_field = gui.entry('info',False)
        new_edje.text_field = info_field.entry
        box = gui.edje_box(self,'V',1)
        box.box.append(info_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.part_text_set('name-text','info')
        info = new_edje.text_field
        name = last_window.text_field
        #print name.text_get()
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_contact_number, 'name' , new_edje.text_field, contact, first_window, name)
        new_edje.edj.signal_callback_add("close_w_textfield", "*", last_window.close_extra_child)
        new_edje.edj.signal_callback_add("save_successful", "*", new_edje.close_extra_child)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()
    
    def add_name_new_contact(self,emission, source, param,first_window=None):
        print "add new name called"
        #print name
        number = emission.part_text_get('num_field-text')
        
        new_edje = gui.edje_gui(self.main,'edit-name',self.edje_file)
        name_field = gui.entry('Name',False)
        new_edje.text_field = name_field.entry
        box = gui.edje_box(self,'V',1)
        box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
        new_edje.add(box.scrolled_view,box,"name-box")
        #new_edje.edj.part_text_set('num_field-text',number)
        new_edje.edj.signal_callback_add("close_w_textfield", "*", new_edje.close_extra_child)
        new_edje.edj.signal_callback_add("save_contact", "*", self.save_new_contact,name_object=new_edje,number=number,first_window=first_window)
        #new_edje.edj.signal_callback_add("del-button", "*", self.number_edit_del)
        
        new_edje.edj.layer_set(4)
        if self.standalone == 1:
            new_edje.edj.size_set(480,600)
        new_edje.edj.edj.pos_set(0,40)
        new_edje.edj.show()
    
    def save_contact_number(self,emission,source,param, switch ,info, contact, details_window,name=None):
        if switch == 'number':
            number = emission.part_text_get('num_field-text')
            contact.tel = number
            details_window.edj.part_text_set('number-text', number)
            details_window.edj.part_text_set('number-info', info)
            emission.signal_emit('contact_saved','*')
        elif switch == 'name':
            cinfo = info.text_get()
            cname = name.text_get()
            print dir(emission)
            # contact.name = name
            details_window.edj.part_text_set('name-text', cname)
            details_window.edj.part_text_set('name-info', cinfo)
            emission.signal_emit('contact_name_edit_saved','*')
    
    def save_new_contact(self,emission, source, param,name_object=None,number=None,first_window=None):
        print "save new contact called"
        name = name_object.text_field.text_get()
        number = number
        
        try:
            contact = tichy.Service('Contacts').create(name=str(name), number=str(number))
        except Exception,e:
            print e
        #emission.signal_emit('save-notice','*')
        name_object.edj.delete()
        #contacts_service = Service('Contacts')
        #contacts_service.add(contact)
        #print dir (self.contact_objects_list)
        self.contact_objects_list.generate_single_item_obj(name,number,contact)
        print self.contact_objects_list.box.box.children_get()
        self.contact_objects_list.box.box.redraw_queue()
        self.contact_objects_list.box.box.show_all()
        first_window.edj.delete()
        #print contacts_service.contacts
     
    def on_key(self, w, k):
        self.text.value += k  # The view will automatically be updated
        
    def on_del(self, w):
        self.text.value = self.text.value[:-1]
        
    #def calling(self,orig,orig_parent,emission, source, param):  
        #print "calling"
        #number = emission.part_text_get("num_field-label")
        #print number
        #yield Caller(self.edje_obj, number)
        
    def on_call(self, b):
        yield Caller(self.window, self.text.value)
       
    def self_test(self,emission, source, param):
        print "emission: ", str(emission)
        print "source: ", str(source)
        print "param: ", str(param)
