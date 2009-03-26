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
    name = 'I/O'
    icon = 'icon.png'
    category = 'launcher' # So that we see the app in the launcher
    launcher_info = [tichy.Service.get('GSM').missed_call_count]
    
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

        #  We use Call object to represent call log 
        self.list_label = [('label', 'number'), ('subtext', 'description')]
        self.item_list = gui.elm_list(self.callLogs, self.window, self.edje_file, "item", self.list_label, comp)
        
        self.edje_obj.add_callback("to_edit_mode", "*", self.to_edit_mode)
        self.edje_obj.add_callback("to_default_mode", "*", self.to_default_mode)

        self.contacts.connect('inserted', self.item_list._redraw_view)

        self.item_list.add_callback("new_call", "*", self.create_call)
        self.item_list.add_callback("new_msg", "*", self.create_msg)
        self.item_list.add_callback("save_number", "*", self.create_contact)

        self.item_list.Elm_win = self.window.window

        yield tichy.WaitFirst(tichy.Wait(self.window, 'back_I/O'),tichy.Wait(self.window, 'delete_request'))
        
        del self.item_list
        self.window.delete()
    
    def to_edit_mode(self, emission, source, param):
        for item in self.item_list.items:
            item[1].signal_emit("to_edit_mode", "*")
        
    def to_default_mode(self, emission, source, param):
    
        deleting = []
    
        for i in range(len(self.item_list.items)):
            if self.item_list.items[i][1].part_text_get("delete-flag") == "1":
                deleting.append(self.item_list.items[i][0])
            else:
                print self.item_list.items[i][1].part_text_get("delete-flag")
        
        deleting.reverse()
        
        self.item_list.model.remove_group(deleting)
                
        for item in self.item_list.items:
                item[1].signal_emit("to_default_mode", "*")
    
    def create_call(self, emission, source, param, callLog):
        number = callLog[0].number.value
        name = unicode(callLog[0])
        caller_service = tichy.Service.get('TeleCaller')
        caller_service.call("window", number, name).start()
    
    def create_msg(self, emission, source, param, callLog):
        service = tichy.Service.get('MessageCreate')
        service.write(self.window, callLog[0].number).start()
    
    def create_contact(self, emission, source, param, callLog):
        service = tichy.Service.get('ContactCreate')
        service.create(self.window, callLog[0].number).start()

    def printer(self, *args, **kargs):
        print args
        print kargs

##move to msgs app later

##Service to store some info
class MessageCreate(tichy.Service):
    service = 'MessageCreate'

    def __init__(self):
        super(MessageCreate, self).__init__()
    
    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
        
    def _do_sth(self):
        pass    
        
    def write(self, window, number="", txt=""):
        sms_service = tichy.Service.get('SMS')
        sms = sms_service.create(number, txt)
        return MsgsWrite(window, sms)

class MsgsWrite(tichy.Application):
    
    name = 'MsgsWriteApp'
    
    def run(self, parent, sms, *args, **kargs):
        try:
          self.edje_file = os.path.join(os.path.dirname(__file__), 'i-o.edj')
          number_layout = 0
          send = 0
          
          if sms.peer == "":
              full = True
          else:
              full = False
          
          while True:
          
              if full:
                  pass
                  
              if sms.text == "":
                
                  print "in text edit"
                  
                  text_layout = gui.elm_layout(parent.window, self.edje_file, "CreateText")
                  
                  text_layout.elm_obj.layer_set(99)
                  
                  edje_obj = text_layout.elm_obj.edje_get()
                  
                  text_layout.elm_obj.show()
                  
                  parent.main_layout.elm_obj.hide()
                  
                  parent.bg.elm_obj.content_set("content-swallow", text_layout.elm_obj)
                  
                  textbox = gui.elementary.Entry(parent.window.elm_obj)
          
                  textbox.color_set(255, 255, 255, 255)
          
                  textbox.entry_set("Just a stupid test text")
                  
                  textbox.size_hint_weight_set(1.0, 1.0)
                  text_layout.elm_obj.content_set('entry', textbox)
                  
                  textbox.editable_set(True)        
                  
                  textbox.focus()
                  textbox.show()
                  #try:
                      #parent.window.elm_obj.keyboard_win_set(False)
                      #parent.window.elm_obj.keyboard_mode_set(gui.elementary.ELM_WIN_KEYBOARD_ON)
                  #except Exception, e:
                      #print e
                      #print Exception
                  
              
              #print dir(parent.window.elm_obj.evas_get())
              
              logger.info("just before waiting")
              i, args = yield tichy.WaitFirst(Wait(text_layout, 'back'), Wait(text_layout, 'send'))
              
              print "full: ", full
              if i == 0: #back
                  if full:
                      continue
                  else:
                      print "breaking"
                      break
              if i == 1: #send
                  send = 1
                  break
          
          logger.info("broke loop")
          if send == 1:
              text = str(textbox.entry_get()).replace("<br>","")
              sms.text = text.strip()
              text_layout.elm_obj.edje_get().signal_emit("save-notice","*")
              yield self.send_sms(sms)
              print "sending"
        
          if number_layout:
              number_layout.delete()
              
          if text_layout:
              text_layout.delete()
              parent.window.elm_obj.keyboard_win_set(0)
          
          parent.restore_orig()    
          
          ret = "done"
          
          yield ret
          
        except Exception, e:
            print e
            print Exception
    
    @tichy.tasklet.tasklet
    def send_sms(self, sms):
        """tasklet that performs the sending process

        connects to SIM service and tries sending the sms, if it fails it opens an error dialog, if it succeeds it deletes the edje window it it given
        """
        logger.info("send message called")
        try:
            message_service = tichy.Service.get('Messages')
            message = message_service.create(number=sms.peer, text=sms.text, direction='out')
            logger.info("sending message: %s to : %s", sms.text, sms.peer)
            yield message.send()
        except Exception, ex:
            logger.error("Got error %s", ex)
            #yield tichy.Service.get('Dialog').error(self.main, "%s", ex)
    
    def callback(self, *args, **kargs):
        print args
        print kargs
    
    def err_callback(self, *args, **kargs):
        print args
        print kargs

## move to launcher app later

##Service to generate and store the topbar
class TopBar(tichy.Service):
    service = 'TopBar'

    def __init__(self):
        super(TopBar, self).__init__()
        self.edje_file = os.path.join(os.path.dirname(__file__), 'i-o.edj')
    
    
    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
    
    def _do_sth(self):
        pass
    
    def create(self):
        self.window = gui.elm_window()
        self.layout = gui.elm_layout(self.window, self.edje_file, "tb")
        
        return self.layout
        
    #def create(self, window, number=""):
        #return CreateContact(window, number)

##move to people app later

##Service to store some info
class ContactCreate(tichy.Service):
    service = 'ContactCreate'

    def __init__(self):
        super(ContactCreate, self).__init__()
    
    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
        
    def _do_sth(self):
        pass    
        
    def create(self, window, number=""):
        return CreateContact(window, number)

class CreateContact(tichy.Application):
    
    name = 'CreateContactApp'
    
    def run(self, parent, number, *args, **kargs):
        try:
          self.edje_file = os.path.join(os.path.dirname(__file__), 'i-o.edj')
          number_layout = 0
          send = 0
          contact = None
          
          if number == "":
              full = True
          else:
              full = False
          
          while True:
          
              if full:
                  pass
              
              text_layout = gui.elm_layout(parent.window, self.edje_file, "CreateContact")
              
              edje_obj = text_layout.elm_obj.edje_get()
              
              text_layout.elm_obj.show()
              
              parent.main_layout.elm_obj.hide()
              
              parent.bg.elm_obj.content_set("content-swallow", text_layout.elm_obj)
              
              textbox = gui.elementary.Entry(parent.window.elm_obj)
              textbox.single_line_set(True)
      
              textbox.color_set(255, 255, 255, 255)
              
              textbox.size_hint_weight_set(1.0, 1.0)
              text_layout.elm_obj.content_set('entry', textbox)
              textbox.editable_set(True)        
              
              textbox.focus()
              textbox.show()
              
              i, args = yield tichy.WaitFirst(Wait(text_layout, 'back'), Wait(text_layout, 'save'))
              
              print "full: ", full
              if i == 0: #back
                  if full:
                      continue
                  else:
                      print "breaking"
                      break
              if i == 1: #save
                  send = 1
                  break
          
          logger.info("broke loop")
          
          if send == 1:
              print "saving"
              text_layout.elm_obj.edje_get().signal_emit("save-notice","*")
              contacts_service = tichy.Service.get('Contacts')
              if contact not in contacts_service.contacts:
                  name = str(textbox.entry_get()).replace("<br>","")
                  new_contact = contacts_service.create(name.strip(),tel=str(number))
                  contacts_service.add(new_contact)
                  contacts_service.contacts.emit('inserted')
          
          if number_layout:
              number_layout.delete()
              
          if text_layout:
              text_layout.delete()
          
          parent.restore_orig()    
          
          ret = "done"
          
          yield ret
          
        except Exception, e:
            print e
            print Exception
    
    def callback(self, *args, **kargs):
        print args
        print kargs
    
    def err_callback(self, *args, **kargs):
        print args
        print kargs