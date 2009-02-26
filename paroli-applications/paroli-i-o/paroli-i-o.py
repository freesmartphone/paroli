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


import logging
logger = logging.getLogger('app.i-o')

import os
import tichy
from tichy import gui
import sys
from tichy.service import Service
import ecore

class CallLog(tichy.Item):
    """Class that represents a call log"""
    def __init__(self, number, direction, timestamp, type):
        self.number = number
        self.direction = direction
        self.timestamp = timestamp
        self.type = type
        self.description = self.type + " at " + unicode(self.timestamp.get_text())

    def get_text(self):
        return self.number.get_text()


class I_O_App(tichy.Application):
    name = 'Paroli-I/O'
    icon = 'icon.png'
    #category = 'main' # So that we see the app in the launcher
    category = 'launcher' # So that we see the app in the launcher
    layer = 0
    
    def run(self, parent=None, standalone=False):
        self.standalone = standalone
        self.main = parent
        if self.main.etk_obj.title_get() != 'Home':
            self.main.etk_obj.title_set('I/O')
            self.main.etk_obj.show()
        self.geometry = self.main.etk_obj.geometry_get()
        self.y = self.geometry[1]
        self.history_items = []
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-i-o.edj')
        self.layerdict = {}
        self.gsm_service = tichy.Service('GSM')
            
        self.history = self.gsm_service.logs
        self.callLogs = tichy.List()
        i = 0
        for call in self.history:
            if (i == 30): break
            if call.status == "inactive" and call.direction == "in":
                self.callLogs.append(CallLog(call.number, call.direction, call.timestamp, "Missed"))
            elif call.status != "inactive" and call.direction == "in":
                self.callLogs.append(CallLog(call.number, call.direction, call.timestamp, "Incoming"))
            else: 
                self.callLogs.append(CallLog(call.number, call.direction, call.timestamp, "Outgoing"))
            i = i + 1
        
        #history_box = gui.edje_box(self, 'V', 1)

        def comp(m1, m2):
            return cmp(m2.timestamp, m1.timestamp)

        #self.lists = gui.lists()

        #  We use Call object to represent call log 
        self.list_label = [('label', 'number'), ('subtext', 'description')]
        self.history_list = gui.EvasList(self.callLogs, self.main, self.edje_file, "history_item", self.list_label, comp)
        self.history_swallow = self.history_list.get_swallow_object()

        self.edje_obj = gui.EdjeWSwallow(self.main, self.edje_file, 'i-o', "history-items")
        self.edje_obj.add_callback("to_edit_mode", "*", self.to_edit_mode)
        self.edje_obj.add_callback("to_default_mode", "*", self.to_default_mode)
        self.edje_obj.embed(self.history_swallow, self.history_list.box, "history-items")
        if self.standalone:
            self.edje_obj.Edje.size_set(480,550)
            self.edje_obj.Edje.pos_set(0, 50)
        else:
            self.edje_obj.Edje.size_set(480,590)
              
        logger.info(self.edje_obj.Edje.size_get())    
        logger.info(self.edje_obj.Edje.pos_get())
        self.set_list(self.history_list)
        self.edje_obj.show()

        yield tichy.Wait(self.main, 'back_Paroli-I/O')
        if self.standalone:
            self.edje_obj.delete()
        else:
            self.edje_obj.delete()
            self.main.etk_obj.hide()   # Don't forget to close the window

    def set_list(self, list):
        for item in list.items:
            self.set_item(item)
        
    def set_item(self, item):
        item[1].Edje.signal_emit("to_default_mode", "")
        item[1].Edje.signal_callback_add("new_call", "*", self.create_call, item[0])
        item[1].Edje.signal_callback_add("new_msg", "*", self.create_message, item[0])
        item[1].Edje.signal_callback_add("save_number", "*", self.save_number, item[0])
        item[1].Edje.signal_callback_add("delete_log", "*", self.delete_log, item)
    
    def to_edit_mode(self, emission, source, param):
        for item in self.history_list.items:
            item[1].Edje.signal_emit("to_edit_mode", "")
        
    def to_default_mode(self, emission, source, param):
        for item in self.history_list.items:
            item[1].Edje.signal_emit("to_default_mode", "")
    
    def create_call(self, emission, source, param, contact):
        print "Create Call ", contact
        number = contact.number.value
        name = unicode(contact)
        #self.extra_child.edj.part_swallow_get('contacts-items').visible_set(0)
        #self.extra_child.edj.part_swallow_get('contacts-items').delete()
        caller_service = Service('Caller')
        my_call = caller_service.call(emission, number, name)
        my_call.start()
        #try:
            #self.extra_child.edj.delete()
        #except Exception,e:
            #print e
    
    def save_number(self, emission, source, param, contact):
        print "Save number ", contact

    def delete_log(self, emission, source, param, log):
        print "Delete Log ", log
        #TODO: delete log data
        self.history_list.items.remove(log)
        self.refresh_list()

    def refresh_list(self):
        print "refresh list"
        self.history_swallow = self.history_list.get_swallow_object()
        self.edje_obj = gui.EdjeWSwallow(self.main, self.edje_file, 'i-o', "history-items")
        self.edje_obj.add_callback("to_edit_mode", "*", self.to_edit_mode)
        self.edje_obj.add_callback("to_default_mode", "*", self.to_default_mode)
        self.edje_obj.embed(self.history_swallow, self.history_list.box, "history-items")
        if self.standalone:
            self.edje_obj.Edje.size_set(480,550)
            self.edje_obj.Edje.pos_set(0, 50)
        else:
            self.edje_obj.Edje.size_set(480,590)
              
        self.set_list(self.history_list)
        self.edje_obj.show()
        

    def remove_entry(self, entry):
        print "remove called"
        assert entry in self.history
        self.history.remove(entry)
    
    def load_phone_book(self,orig,orig_parent,emission, source, param):
        print "load phone book called"
        print dir(orig)
        print orig.group
        try:
          new_edje = gui.edje_window(orig_parent,'tele-people',orig.gsm,orig.phone_book)
        except Exception,e:
          print e
        orig.extra_child = new_edje
        #try:
          #orig_parent.add(new_edje)
        #except Exception,e:
          #print e
        print "done"
        try:
          contacts_edje = gui.edje_box(self,'V',1)
        except Exception,e:
          print e  
         
        #try: 
          #self.contacts_obj = gui.edje_window(orig_parent,'people',self)
        #except Exception,e:
          #print e 
        #self.contacts_obj.layer_set(17)
        try: 
          self.lists = gui.lists()
        except Exception,e:
          print e 
          
        try: 
          print "self.lists.generate_contacts_list(self,orig_parent,self.phone_book,contacts_edje,self.edje_obj)"
          self.lists.generate_contacts_list(self,orig_parent.etk_obj.evas,self.phone_book,contacts_edje,self.edje_obj,'tele-contacts_item')
        except Exception,e:
          print e 
        
        try: 
          to_2_swallowed = contacts_edje.scrolled_view
        except Exception,e:
          print e 
       
        try: 
          print "new_edje.add(to_2_swallowed,contacts_edje)"
          new_edje.add(to_2_swallowed,contacts_edje)
        except Exception,e:
          print e 
        
        try: 
          contacts_edje.box.show()
        except Exception,e:
          print e 
    
    def on_key(self, w, k):
        self.text.value += k  # The view will automatically be updated
        
    def on_del(self, w):
        self.text.value = self.text.value[:-1]
        
    def calling(self,orig,orig_parent,emission, source, param):  
        print "calling"
        number = emission.part_text_get("num_field-label")
        #print number
        #yield Caller(self.edje_obj, number)
        
    def on_call(self, b):
        yield Caller(self.window, self.text.value)
       
    def self_test(self, *args, **kargs):
        logger.info(args[1])
        logger.info(args[2])

    """
    def self_test(self,emission, source, param):
        print "emission: ", str(emission)
        print "source: ", str(source)
        print "param: ", str(param)
        #try:
            #eval(source + '(self,self.parent,emission, source, param)')
        #except Exception, e:
            #dir(e)
    """
    """
    def wait_mode(self,instance,edje_object, emission, source,param):
        emission.signal_emit('wait-mode',"*")
        #print dir(emission.part_object_get('layover'))
        print emission.part_object_get('layover').render_op_get()
        print "wait-mode emitted"
        emission.part_object_get('layover').render_op()
    """

    """ 
    def edit_btn_clicked(self,instance,edje_object, emission, source,param):
        #print "edit_btn in paroli-i-o"
        #print len(self.history_items)
        try:
            print "state: ",emission.part_state_get("edit-button")[0]
        except Exception,e:
            print e
        if emission.part_state_get("edit-button")[0] == 'default' or emission.part_state_get("edit-button")[0] == '':
            #print "edit detected"
            signal = 'edit'
            #emission.signal_emit('wait-mode',"*")
                  
            #print "after for"
            
            try:
              emission.signal_emit('edit-mode',"*")
            except Exception,e:
                  print e  
            
        else:
            #print "button pressed"
            #emission.signal_emit('edit_button_to_wait',"*")
            #print emission.part_state_get(edje_object)[0]
            signal = 'normal'
            #print "normal detected"
            for i in self.history_items:
                    
              #if edje object state edit
              if i[0].part_state_get('edit-base')[0] == 'edit':
                    #destroy text in info field (missed etc)
                    i[1].destroy()
                    
                    #remove all edje stuff from history item to be deleted
                    i[2].remove_all()
                    
              #TODO: add "real delete" on SIM  
                    
            emission.signal_emit('edit_button_to_default',"*")

        
        #print "after if/else"
        for i in self.history_items:
            print "# :",str(i)
            try:
              i[0].signal_emit(signal,"")
            except Exception,e:
              print e
        
        print "edit-mode emitted"
    """

    
     ## step two (enter message)    
    def create_message(self, emission, source, param, contact):
        print "Create message ", contact
        ##get numbers from dialpad
        numbers = contact.number
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
        #new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
    
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
        
    def close_keyboard(self,*args):
        print "close keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
    
    def open_keyboard(self,*args):
        print "open keyboard called"
        self.main.etk_obj.x_window_virtual_keyboard_state_set(ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_ON)
