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

import logging
logger = logging.getLogger('app.dialer')

import os
import tichy
from tichy import gui
import sys
from tichy.service import Service

class DialerApp(tichy.Application):
    name = 'Paroli-Dialer'
    icon = 'icon.png'
    category = 'main'
    
    def run(self, parent=None, text = ""):
        if isinstance(text, str):
            text = tichy.Text(text)
        #self.window = parent
        #print dir(parent.etk_obj)
        #self.window.etk_obj.hide()
        ##create main evas
        #self.main = gui.main_edje()
        self.main = parent
        ##set title
        self.main.etk_obj.title_set('Paroli Dialer')
        
        ##set edje_file
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-dialer.edj')
        
        ##connect to tichy's contacts service
        self.contact_service = Service('Contacts')
        
        ##get contacts list
        self.phone_book = self.contact_service.contacts
        
        ##create list for edje objects
        self.contact_objects_list = None
        
        ##create main window
        self.edje_obj = gui.edje_gui(self.main,'tele',self.edje_file)
        self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.name_set('main_dialer_window')
        self.edje_obj.edj.show()
        self.edje_obj.edj.signal_callback_add("func_btn", "*", self.func_btn)
        self.edje_obj.edj.signal_callback_add("top_bar", "*", self.top_bar)
        self.edje_obj.edj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.edj.signal_callback_add("num_field_pressed", "*", self.num_field)
     
        ##wait until main object emits back signal
        yield tichy.Wait(self.main, 'back')
        
        ##remove all children -- edje elements 
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
    
    def add_digit(self,emission,source,param):
        new_sign = param
        value = emission.part_text_get('num_field-text')
        if value == None:
          new = str(new_sign)
        else:
          new = str(value)+str(new_sign)
          
        emission.part_text_set('num_field-text',new)
    
    def num_field(self,emission,source,param):
        print "existence", emission.part_exists(param)
        number = emission.part_text_get(param)
        print "value", number
        if number == None or len(number) == 0:
            self.load_phone_book( emission, source, param)
        else :
            print "number found"
            self.add_contact( emission, source, param)
        print "num_field"
        
    def func_btn(self,emission,source,param):
        if param == 'call-button':
            self.call_btn_pressed(emission, source, param)
        elif param == 'del-button':
            self.number_edit_del(emission,source,param)
    
    def number_edit_del(self,emission, source, param):
        print "number_edit del called"
        value = emission.part_text_get("num_field-text")
        if len(value) != 0:
          emission.part_text_set("num_field-text",value[:-1])
    
    def call_btn_pressed(self,emission, source, param):
        number = emission.part_text_get("num_field-text")       
        emission.part_text_set("num_field-text","")       
        Caller(emission, number ).start()
    
    def top_bar(self,emission,source,param):
        #print dir(emission)
        element = emission.name_get()
        #if element == 'contacts_list' or element == 'save_contact':
          
          #try:
            #emission.part_swallow_get(param).delete()
          #except Exception,e:
            #print e
              
          #try:
            #emission.delete()
          #except Exception,e:
            #print e
            
        #if element == 'main_dialer_window':
        print element
        #emission.signal_emit('close_application','*')
        self.main.emit('back')
    
        #else:
          #print element
    
    def call_contact(self, emission, source, param):
        print "call contact called"
        number = emission.part_text_get('label-number')
        name = emission.part_text_get('label')
        self.extra_child.edj.part_swallow_get('contacts-items').visible_set(0)
        self.extra_child.edj.part_swallow_get('contacts-items').delete()
        Caller(None, number, name).start()
        try:
            self.extra_child.edj.delete()
        except Exception,e:
            print e
    
    def add_contact(self,emission, source, param):
        print "add contact in dialer"
        try:
            number = emission.part_text_get('num_field-text')
            print number
            new_edje = gui.edje_gui(self.main,'save-number',self.edje_file)
            new_edje.edj.name_set('save_contact')
            new_edje.edj.signal_callback_add("save_contact", "*", self.save_number)
            new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
            new_edje.edj.signal_callback_add("wait_seconds", "*", new_edje.wait_seconds)
            new_edje.edj.signal_callback_add("close_extra_child", "*", new_edje.close_extra_child)
            new_edje.edj.part_text_set('number',number)
            name_field = gui.entry('Name',False)
            new_edje.text_field = name_field.entry
            box = gui.edje_box(self,'V',1)
            box.box.append(name_field.entry, gui.etk.VBox.START, gui.etk.VBox.NONE,0)
            new_edje.add(box.scrolled_view,box,"name-box")
            box.box.show_all()
            new_edje.edj.layer_set(2)
            new_edje.edj.show()
            self.extra_child = new_edje
        except Exception,e:
          print e
            
    def save_number(self,emission, source, param):
         print "save number in dialer"
         name = self.extra_child.text_field.text_get()
         print name
         number = emission.part_text_get('number')
         print number
         contacts_service = tichy.Service('Contacts')
         try:
            contact = contacts_service.create(str(name),tel=str(number))
         except Exception,e:
            print e
         print contact
         self.edje_obj.edj.part_text_set('num_field-text','')
         emission.signal_emit('save-notice','*')
         try:
            emission.render_op_set(1)
         except Exception,e:
            print e
         self.contact_service.add(contact)
    
    def load_phone_book(self, emission, source, param):
        print "load phone book called"
        try:
            new_edje = gui.edje_gui(self.main,'tele-people',self.edje_file)
            new_edje.edj.signal_callback_add("top_bar", "*", self.top_bar)
            new_edje.edj.name_set('contacts_list')
        except Exception,e:
            print e
        self.extra_child = new_edje
        new_edje.edj.layer_set(3)
        new_edje.edj.show()
        print "done"
        try:
            contacts_box = gui.edje_box(self,'V',1)
        except Exception,e:
            print e
          
        try: 
            print "self.lists.generate_contacts_list(self,orig_parent,self.phone_book,contacts_edje,self.edje_obj)"
            self.contact_objects_list = gui.contact_list(self.phone_book,contacts_box,self.main.etk_obj.evas,self.edje_file,'tele-contacts_item',self)
        except Exception,e:
            print e 
        
        try: 
            to_2_swallowed = contacts_box.scrolled_view
        except Exception,e:
            print e 
        
        try: 
            print "new_edje.add(to_2_swallowed,contacts_edje)"
            new_edje.add(to_2_swallowed,contacts_box,"contacts-items")
        except Exception,e:
            print e 
        
        try: 
            contacts_box.box.show()
        except Exception,e:
            print e 
          
    def start_call(self,orig,orig_parent,emission, source, param):
        print "start call called"
        number = emission.part_text_get("num_field-text")
        
        caller_service = Service('Caller')
        yield caller_service.call(self.edje_obj, number)
       
    def self_test(self,emission, source, param):
        print "emission: ", str(emission)
        print "source: ", str(source)
        print "param: ", str(param)
        
# TODO: ??? make the Caller app better, using John idea : we define
#       for every call status the status of the gui.  Then we just
#       wait for status change and set up the gui in consequence It
#       means we have an automaton with a single state, much simpler
#       to deal with that what we have now


class Caller(tichy.Application):
    """This is the application that deal with the calling sequence
    """

    def run(self,parent, number, name=None):
        """show the Caller window

        :Parameters:
        
            parent : `tichy.gui.Widget`
                The parent window

            number : str | `tichy.Text` | Call object

                If the number is a string, we consider it to the
                number to call, otherwise we consider it to be a Call
                object that is already active.
        """
        # We open a new window for a call
        #logger.info("Caller run")
        
        print "caller run"
        print "in caller: ", name
        self.gsm_service = tichy.Service('GSM')
        
        #print parent
        #print dir(parent)
        main = parent
        #main = parent
        #main.etk_obj.visibility_set(1)
        #main = parent
        main.etk_obj.title_set('Paroli Call')
        
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-dialer.edj')
        self.edje_obj = gui.edje_gui(main,'tele',self.edje_file)
        self.edje_obj.edj.signal_callback_add("func_btn", "*", self.func_btn)
        self.edje_obj.edj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.edj.signal_callback_add("*", "*", self.gui_signals)
        #self.edje_obj.edj.signal_callback_add("num_field_pressed", "*", self.num_field_pressed)
        
        
        #self.window = gui.Window(parent)
        #frame = self.view(self.window, title='Dialer')
        #vbox = gui.Box(frame, axis=1)

        #text = tichy.Text("Initialization")
        #text.view(vbox)

        try:
            # The case when we have an incoming call
            # XXX: we should use an other way to check for a call object !
            if not isinstance(number, (basestring, tichy.Text)):
                call = number
                #print dir(call)
                self.edje_obj.edj.signal_emit('to_incoming_state',"*")
                #self.edje_obj.edj.part_text_set('active-call',call.__id)
                self.edje_obj.edj.part_text_set('num_field-text',str(call.number))
                self.edje_obj.edj.layer_set(2)
                self.edje_obj.edj.show()
                
                def make_active(emission, source, param):
                    call.activate()
                    print "making active"
                    
                self.edje_obj.edj.signal_callback_add("activate_call", "*", make_active)
                
            else:   # If not it means we want to initiate the call first
                if name :
                    self.edje_obj.edj.part_text_set('num_field-text',str(name))
                else:
                    self.edje_obj.edj.part_text_set('num_field-text',str(number))
                self.edje_obj.edj.signal_emit('to_dialing_state',"*")
                self.edje_obj.edj.layer_set(2)
                self.edje_obj.edj.show()
                #try:
                call = self.gsm_service.create_call(number)
                call.initiate()
                #except Exception,e :
                  #print e
                
                def call_release_pre(emission, source, param):
                    try:
                        call.release()
                    except Exception, e:
                        print "exception here in pre state"
                        call.emit('released')
                    
                self.edje_obj.edj.signal_callback_add("release_call", "*", call_release_pre)

            i, args = yield tichy.WaitFirst(tichy.Wait(call, 'activated'),tichy.Wait(call, 'released'))
            if i == 0: #activated
              print "call activated"
              self.edje_obj.edj.signal_emit('to_active_state',"*")
              self.edje_obj.edj.part_text_set('num_field-text',str(call.number))
              #print 'should be an active call here: ', self.gsm_service.gsm_call.ListCalls().__contains__('active')
              def call_release(emission, source, param):
                  print "call releasing"
                  try:
                    call.release() 
                  except Exception,e:
                    print e
                    print "exception here"
                    call.emit('released')
                    #self.edje_obj.edj.signal_emit('notfound',"*")
                    #yield tichy.Wait(call, 'released')
                    
              self.edje_obj.edj.signal_callback_add("release_call", "*", call_release)
              yield tichy.WaitFirst(tichy.Wait(call, 'released'))

            if call.status not in ['released', 'releasing']:
                #text.value = "releasing %s" % call.number
                try:
                  call.release()
                  yield tichy.Wait(call, 'released')
                except Exception, e:
                  print e
                  
        except Exception, e:
            print e
            #import traceback
            #logger.error("%s, %s", e, traceback.format_exc())
            #yield tichy.Dialog(self.window, "Error", e.message)

        self.edje_obj.edj.delete()
        main.etk_obj.visibility_set(0)

        
    def gui_signals(self,emission, source, param):
        print "gui_signals"
        print source
        print param
       
    def add_digit(self,emission, source, param):
        print "dtmf would be sent"
        
    def func_btn(self,emission, source, param):
        print "func btn called from ", source
        state = emission.part_state_get(param)
        print state[0]
        if param == 'call-button':
          
            if state[0] == 'default':
                #self.create_call()
                print "nothing to be done"
                
            elif state[0] == 'incoming':
                self.accept_call(emission)
                
            elif state[0] == 'dialing':  
                self.release_call(emission)
            
            elif state[0] == 'active':
                self.release_call(emission)
              
            elif state[0] == 'releasing':
                #self.accept_call()
                print "nothing to be done"
              
            else :
                print "unknown state for call button"
                
        elif param == 'del-button':
            
            if state[0] == 'default':
                print "nothing to be done"
                
            elif state[0] == 'incoming':
                #self.accept_call()
                print "nothing to be done"
                
            elif state[0] == 'dialing':  
                #self.release_call()
                print "nothing to be done"
                
            
            elif state[0] == 'active':
                #self.mute_call
                print "would be muting"
              
            elif state[0] == 'releasing':
                #self.accept_call()
                print "nothing to be done"
              
            else :
                print "unknown state for del button"
        else :
            print "unknown button"
    
    def release_call(self,emission):
        print "release call Caller called"
        emission.signal_emit("release_call", "*")
    
    def accept_call(self,emission):
        #call_id = emission.part_text_get('active_call')
        #print call_id
        #self.gsm.gsm_call.Activate(call_id)
        print "accept call Caller called"
        emission.signal_emit("activate_call", "*")
    
##Service called when incoming call detected
class MyCallerService(tichy.Service):
    service = 'Caller'
    def call(self, parent, number, name=None):
        #print "in mycallerservice: ", name
        return Caller(parent, number, name)
        

class TextEdit(tichy.Application):
  
    name = 'TextEdit'
    icon = 'icon.png'
    
    def run(self, window, text="", name=None, input_method=None):
      
        
        print "PIN called"
        print text
        print name
        print input_method
        
        ##set edje_file
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-dialer.edj')
        self.main = window
        
        self.edje_obj = gui.edje_gui(self.main,'tele',self.edje_file)
        self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.name_set('PIN')
        self.edje_obj.edj.part_text_set('call-button-text','Enter')
        self.edje_obj.edj.signal_callback_add("func_btn", "*", self.func_btn)
        self.edje_obj.edj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.edj.show()
        
        yield tichy.Wait(self.main, 'value_received')
        
        number = self.edje_obj.edj.part_text_get("active-call")       
        self.edje_obj.edj.delete()
        self.main.etk_obj.visibility_set(0)
        yield number
        
        
    def func_btn(self,emission,source,param):
        if param == 'call-button':
              self.call_btn_pressed(emission, source, param)
        elif param == 'del-button':
              self.number_edit_del(emission,source,param)
              
    def call_btn_pressed(self,emission, source, param):
        self.main.emit('value_received')
        
    def add_digit(self,emission,source,param):
        new_sign = param
        value = emission.part_text_get('active-call')
        if value == None:
          new = str(new_sign)
          new_stars = '*'
        else:
          new = str(value)+str(new_sign)
          new_stars = str(emission.part_text_get('num_field-text')) + '*'
        
        emission.part_text_set('active-call',new)
        emission.part_text_set('num_field-text',new_stars)
        
    def number_edit_del(self,emission, source, param):
        print "number_edit del called"
        value = emission.part_text_get("active-call")
        star_value = emission.part_text_get("num_field-text")
        if len(value) != 0:
          emission.part_text_set("num_field-text",star_value[:-1])
          
          emission.part_text_set("active-call",value[:-1])
          
          
class MyTextEditService(tichy.Service):
    """Service to edit text

    By creating this service class, we allow any application in need
    of a text editor to use the applicaton we defined previously.
    """

    service = 'TextEdit'

    def edit(self, parent, text="", name=None, input_method=None):
        """The only function defined in the TextEditService"""
        return TextEdit(parent, text, name=name, input_method=input_method)
