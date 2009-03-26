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
import ecore

class I_O_App(tichy.Application):
    name = 'I/O'
    icon = 'icon.png'
    category = 'main' # So that we see the app in the launcher
    launcher_info = [tichy.Service.get('GSM').missed_call_count]
    layer = 0
    
    def run(self, parent=None, standalone=False):
        self.standalone = tichy.config.getboolean('standalone',                                               'activated', False)
        
        self.main = parent
        if self.main.etk_obj.title_get() != 'Home':
            self.main.etk_obj.title_set('I/O')
            self.main.etk_obj.show()
        self.geometry = self.main.etk_obj.geometry_get()
        self.y = self.geometry[1]
        self.history_items = []
        self.edje_file = os.path.join(os.path.dirname(__file__), 'i-o.edj')
        self.layerdict = {}
        self.gsm_service = tichy.Service.get('GSM')
        self.callLogs = self.gsm_service.logs

        def comp(m1, m2):
            return cmp(m2.timestamp, m1.timestamp)

        #  We use Call object to represent call log 
        self.list_label = [('label', 'number'), ('subtext', 'description')]
        self.callLogsView = gui.EvasList(self.callLogs, self.main, self.edje_file, "history_item", self.list_label, comp)
        self.history_swallow = self.callLogsView.get_swallow_object()

        self.edje_obj = gui.EdjeWSwallow(self.main, self.edje_file, 'i-o', "history-items")
        self.edje_obj.add_callback("to_edit_mode", "*", self.to_edit_mode)
        self.edje_obj.add_callback("to_default_mode", "*", self.to_default_mode)
        
        self.edje_obj.add_callback("*", "paging", self.paging)
        
        self.edje_obj.embed(self.history_swallow, self.callLogsView.box, "history-items")
        if self.standalone:
            self.edje_obj.Edje.size_set(480,550)
            self.edje_obj.Edje.pos_set(0, 50)
        else:
            self.edje_obj.Edje.size_set(480,580)
              
        logger.info(self.edje_obj.Edje.size_get())    
        logger.info(self.edje_obj.Edje.pos_get())
        self.set_list(self.callLogsView)
        self.edje_obj.show()

        yield tichy.WaitFirst(tichy.Wait(self.main, 'back_I/O'),tichy.Wait(self.main, 'delete_request'))
        self.gsm_service.check_all_missed_call_logs()
        
        if self.standalone:
            self.edje_obj.delete()
            # XXX: This is wrong. We shouldn't use del to delete the object.
            #      and the signal emission should also be automatic.
            self.callLogsView.emit('destroyed')
            del self.callLogsView
            del self.history_swallow
        else:
            self.edje_obj.delete()
            if tichy.config.get('autolaunch','application') != 'Paroli-Launcher':
                    self.main.etk_obj.hide()   # Don't forget to close the window

    def set_list(self, list):
        for item in list.items:
            self.set_item(item)

    def paging(self, emission, signal, source):
        logger.info("paging called")
        if signal == "up":
            self.callLogsView.paging(-1)
        elif signal == "down":
            self.callLogsView.paging(1)
        
    def set_item(self, item):
        log = item[0]
        edjeObj = item[1]
        edjeObj.Edje.signal_emit("to_default_mode", "")
        edjeObj.Edje.signal_callback_add("new_call", "*", self.create_call, item[0])
        edjeObj.Edje.signal_callback_add("new_msg", "*", self.create_message, item[0])
        edjeObj.Edje.signal_callback_add("save_number", "*", self.save_number, item[0])
        edjeObj.Edje.signal_callback_add("delete_log", "*", self.delete_log, item[0])
        # Show button refresh
        if not log.number.get_contact():
            edjeObj.Edje.signal_emit("show_save_button", "*") 
    
    def to_edit_mode(self, emission, source, param):
        for item in self.callLogsView.items:
            item[1].Edje.signal_emit("to_edit_mode", "")
        
    def to_default_mode(self, emission, source, param):
        for item in self.callLogsView.items:
            item[1].Edje.signal_emit("to_default_mode", "")
    
    def create_call(self, emission, source, param, callLog):
        number = callLog.number.value
        name = unicode(callLog)
        caller_service = tichy.Service.get('TeleCaller')
        caller_service.call("window", number, name).start()
    
    def _on_number_saved(self, *args, **kargs):
        """ Make call log(Call) emit a modified signal to make the list refreshed 
            for the case saving the number to a contact)
        """
        # item[0]:Call object 
        # item[1]:EdjeObject object 
        modified_edje_item = args[1] 
        for item in self.callLogsView.items:
            log = item[0]
            edje = item[1].Edje
            if edje is modified_edje_item:
                log.emit("modified")
                break
        #XXX: Because _redraw_view will produce new Edje object for the whole list
        self.set_list(self.callLogsView)

    def save_number(self, emission, source, param, number):
        # Add a contact to contact list
        # Make call log item modified.
        try:
            contact = tichy.Service.get('Contacts').create(name="", tel=str(number))
        except Exception,e:
            print e
        contact_edit_service = tichy.Service.get('ContactEdit')
        edit_name_app = contact_edit_service.edit_name(self.main, contact)
        edit_name_app.connect('exit', self._on_number_saved, emission)
        edit_name_app.start()

    def delete_log(self, emission, source, param, log):
        print "Delete Log ", log
        self.callLogs.remove(log)
       
    def self_test(self, *args, **kargs):
        logger.info(args[1])
        logger.info(args[2])

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
            
        message_service = tichy.Service.get('SMS')
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
