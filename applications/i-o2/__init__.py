# -*- coding: utf-8 -*-
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

from tichy.tasklet import Wait, WaitFirst

class I_O2_App(tichy.Application):
    name = 'Call-Log'
    icon = 'icon.png'
    category = 'launcher' # So that we see the app in the launcher
    launcher_info = ['GSM',"missed_call_count"]
    
    def run(self, parent=None, standalone=False):
        ##to be standardized
        self.edje_file = os.path.join(os.path.dirname(__file__), 'i-o.edj')

        self.gsm_service = tichy.Service.get('GSM')
        self.callLogs = self.gsm_service.logs

        ##get message service and list of all messages
        self.contact_service = tichy.Service.get('Contacts')
        self.contacts = self.contact_service.contacts
        ##sort contact by date
        def comp2(m1, m2):
            return cmp(str(m1.name).lower(), str(m2.name).lower())
         
        self.contacts.sort(comp2) 

        ##generate app-window
        self.window = gui.elm_list_window(self.edje_file, "main", "list", None, None, True)
        self.edje_obj = self.window.main_layout
        
        def comp(m1, m2):
            return cmp(m2.timestamp, m1.timestamp)

        #  We use the Call object to as items in the call log 
        self.list_label = [('label', 'number'), ('subtext', 'description')]
        self.item_list = gui.elm_list(self.callLogs, self.window, self.edje_file, "item", self.list_label, comp)
        
        self.edje_obj.add_callback("to_edit_mode", "*", self.to_edit_mode)
        self.edje_obj.add_callback("to_default_mode", "*", self.to_default_mode)

        self.oid = self.contacts.connect('inserted', self.item_list._redraw_view)

        if len(self.callLogs) == 0:
            self.edje_obj.Edje.signal_emit("ListEmpty", "python")
            self.oid2 = self.callLogs.connect('inserted', self.restore_edit)

        self.item_list.add_callback("new_call", "*", self.create_call)
        self.item_list.add_callback("new_msg", "*", self.create_msg)
        self.item_list.add_callback("save_number", "*", self.create_contact)

        self.item_list.Elm_win = self.window.window

        i, args = yield tichy.WaitFirst(tichy.Wait(self.window, 'back'),tichy.Wait(self.window, 'delete_request'), tichy.Wait(self.window.window,'closing'))
        
        for i in self.callLogs:
            i.missed = False
            i.check()
        
        self.callLogs.emit("modified")
        
        if i != 2:
            self.contacts.disconnect(self.oid)
            self.window.delete()
            del self.item_list
    
    def restore_edit(self, *args, **kargs):
        self.edje_obj.Edje.signal_emit("ListFilled", "python")
    
    def to_edit_mode(self, emission, source, param):
        for item in self.item_list.items:
            item[1].signal_emit("to_edit_mode", "*")
        
    def to_default_mode(self, emission, source, param):
    
        deleting = []
    
        for i in range(len(self.item_list.items)):
            if self.item_list.items[i][1].part_text_get("delete-flag") == "1":
                deleting.append(self.item_list.items[i][0])
            else:
                logger.debug('to_default_mode %s', self.item_list.items[i][1].part_text_get("delete-flag"))
        
        deleting.reverse()
        
        self.item_list.model.remove_group(deleting)
                
        for item in self.item_list.items:
                item[1].signal_emit("to_default_mode", "*")
    
        if len(self.callLogs) == 0:
            self.edje_obj.Edje.signal_emit("ListEmpty", "python")
    
    def create_call(self, emission, source, param, callLog):
        number = callLog[0].number.value
        name = unicode(callLog[0])
        caller_service = tichy.Service.get('TeleCaller2')
        caller_service.call("window", number, name).start()
    
    def create_msg(self, emission, source, param, callLog):
        service = tichy.Service.get('MessageCreate')
        service.write(self.window, 'reply', callLog[0].number).start()
    
    def create_contact(self, emission, source, param, callLog):
        service = tichy.Service.get('ContactCreate')
        service.create(self.window, callLog[0].number).start()

    def printer(self, *args, **kargs):
        logger.debug('printer %s %s', args, kargs)
