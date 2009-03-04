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
logger = logging.getLogger('Tele')

import os
import tichy
from tichy import gui
import sys
from tel_number import TelNumber
from dialog import Dialog

class DialerApp(tichy.Application):
    name = 'Tele'
    icon = 'icon.png'
    category = 'launcher'

    def run(self, parent=None, standalone=False):
        logger.info("loading")
        self.standalone = standalone
        self.main = parent

        # XXX: We whouldn't have to use this big try block if the
        #      launcher app automatically removed the parent window.
        try:
            ##set title if not in launcher mode
            if self.main.etk_obj.title_get() != 'Home':
                self.main.etk_obj.title_set('Tele')
                self.main.etk_obj.show()

            ##set edje_file
            self.edje_file = os.path.join(os.path.dirname(__file__),'tele.edj')

            ##connect to tichy's contacts service
            self.contact_service = tichy.Service.get('Contacts')
            
            ##connect to tichy's ussd service
            self.ussd_service = tichy.Service.get('Ussd')
  
            ##get contacts list
            self.phone_book = self.contact_service.contacts

            ##cmp function for list sorting
            def comp(m1, m2):
                return cmp(str(m1.name).lower(), str(m2.name).lower())
            
            self.list_label = [('label','name'),('label-number','tel')]
            self.phone_book_list = gui.EvasList(self.phone_book, self.main, self.edje_file, "tele-contacts_item", self.list_label, comp)

            ##create list for edje objects
            self.contact_objects_list = None

            ##create main window
            self.edje_obj = gui.EdjeObject(self.main,self.edje_file,'tele')
            #self.edje_obj.data_add('windows',self.edje_obj)

            if self.standalone:
                self.edje_obj.Edje.size_set(480,520)
                self.edje_obj.Edje.pos_set(0, 50)
            else:
                self.edje_obj.Edje.size_set(480,590)
                
            logger.info(self.edje_obj.Edje.size_get())    
            logger.info(self.edje_obj.Edje.pos_get())
            self.edje_obj.Edje.name_set('main_tele_window')
            self.edje_obj.show()
            self.main.connect('hide_Tele',self.edje_obj.hide)
            self.main.connect('show_Tele',self.edje_obj.dehide)
            self.edje_obj.add_callback("num_field_pressed", "*", self.num_field)

            self.edje_obj.add_callback("*", "embryo", self.embryo)
            self.edje_obj.add_callback("*", "call", self.call)

            ##wait until main object emits back signal or delete is requested
            yield tichy.WaitFirst(tichy.Wait(self.main, 'delete_request'),tichy.Wait(self.main, 'back_Tele'))
            logger.info('Tele closing')

        finally:
            ##remove all children -- edje elements if not in launcher mode
            if self.standalone:
                self.edje_obj.delete()

            else:
                self.edje_obj.delete()
                self.main.etk_obj.hide()   # Don't forget to close the window

    ##DEBUG FUNCTIONS 
    ## msgs from embryo
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))
        
    ## callback one (used?)
    def callback(self,*args,**kargs):
        txt = "callback called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    ## general output check
    def self_test(self, *args, **kargs):
        txt = "self test called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    ## WINDOW FUNCTIONS
    ## close window
    def delete_request(self, *args, **kargs):
        self.main.emit('back_Tele')
        logger.info('delete_request' + str(args))

    ## topbar clicked 
    def top_bar(self,emission,source,param):
        self.main.emit('back_Tele')

    ## MISC FUNCTIONS
    ## switch to either open contacts or save number
    def num_field(self, emission, source, param):
        number = emission.part_text_get(param)
        if number == None or len(number) == 0:
            self.load_phone_book( emission, source, param )
        else :
            logger.debug("number found")
            self.add_contact_window( emission, source, param )

    def save_contact(self, *args, **kargs ):
        name = kargs['name_field'].etk_obj.text
        number = kargs['number']
        logger.info('saving contact: name: ' + name + " number: " + number)
        args[0].signal_emit('save-notice','*')
        args[0].render_op_set(1)
        try:
            contact = self.contact_service.create(str(name),tel=str(number))
            self.contact_service.add(contact)
            ## clear number field on success
            self.edje_obj.Edje.part_text_set('num_field-text','')
        except Exception,e:
            logger.error("Got error in save_number : %s", e)
        args[0].signal_emit('mouse,clicked,1','back-button')
        
    def change_text(self, entry, edje):
        edje.Edje.part_text_set('name-text-field',entry.text) 

    ## SUBWINDOW FUNCTIONS
    ## open subwindow showing contact-list
    def load_phone_book(self, emission, signal, source):
        logger.debug("load phone book called")
        new_edje = gui.EdjeWSwallow(self.main, self.edje_file, 'tele-people', "contacts-items", self.edje_obj.Windows)
        new_edje.Edje.name_set('contacts_list')
        new_edje.Edje.size_set(480,590)
        new_edje.Edje.pos_set(0,50)
        new_edje.show(3)
        swallow = self.phone_book_list.get_swallow_object()
        new_edje.embed(swallow,self.phone_book_list.box,"contacts-items")
        #self.phone_book_list.add_callback("*", "*",self.self_test)
        self.phone_book_list.add_callback("call_contact", "tele", self.call_contact)
        self.phone_book_list.add_callback("call_contact", "tele", new_edje.delete)

    def load_phone_book_elm(self, emission, signal, source):
        logger.info("load phone book elm called")
        ##generate window
        win = gui.elementary.Window("phonebook", gui.elementary.ELM_WIN_BASIC)
        win.title_set("Layout")
        win.autodel_set(True)
        main_layout = gui.elementary.Layout(win)
        main_layout.file_set("/usr/share/nfs-paroli/paroli-applications/tele/tele.edj", "tele-people")
        main_layout.size_hint_weight_set(1.0, 1.0)
        win.resize_object_add(main_layout)
        main_layout.show()
        
        #fr = gui.elementary.Frame(win.elm_obj)
        #fr.label_set("Information")
        #box0.pack_end(fr)
        #fr.show()
        
        sc = gui.elementary.Scroller(win)
        sc.size_hint_weight_set(1.0, 1.0)
        sc.size_hint_align_set(-1.0, -1.0)
        main_layout.content_set("contacts-items", sc)
        #box0.pack_end(sc)
        sc.show()
        
        box0 = gui.elementary.Box(win)
        box0.size_hint_weight_set(1.0, 1.0)
        sc.content_set(box0)
        box0.show()

        #box1 = gui.elementary.Box(win)
        #box1.size_hint_weight_set(1.0, 1.0)
        #sc.content_set(box1)
        #box1.show()
        
        buttons = [("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked'),("Bg Plain", 'bg_plain_clicked'), 
               ("Bg Image", 'bg_image_clicked')]
        
        #for btn in buttons:
            #bt = gui.elementary.Button(win)
            ####bt.clicked = btn[1]
            #bt.label_set(btn[0])
            #bt.size_hint_align_set(-1.0, 0.0)
            #box0.pack_end(bt)
            #bt.show()
    
        for i in self.phone_book_list.model:
            logger.info(i)
            #layout = gui.elm_layout(win, "/usr/share/nfs-paroli/paroli-applications/tele/tele.edj", "tele-contacts_item")
            layout = gui.elementary.Layout(win)
            layout.file_set("/usr/share/nfs-paroli/paroli-applications/tele/tele.edj", "tele-contacts_item")
            layout.resize(400,60)
            #layout.elm_obj.size_set(0.5, 0.5)
            layout.size_hint_align_set(-1.0, 0.0)
            #logger.info(layout.elm_obj.size_get())
            #obj = gui.EdjeObject(self.main, self.edje_file, "tele-contacts_item")
            #obj.Edje.show()
            #layout.elm_obj.content_set('base', obj.Edje)
            box0.pack_end(layout)
            layout.show()
            box0.show()
            
            
            
        
    
        #win.elm_obj.resize(320,520)
        win.show()
        
        ##generate big layout
        
        
        #main_layout = gui.elm_layout(win.elm_obj, self.edje_file, 'tele-people')
        ###generate box to go into big layout
        #box = gui.elementary.Box(win.elm_obj)
        ###big layout into win
        
        
        ##for i in self.phone_book_list.model:
            ##logger.info(i)
            ##layout = gui.elm_layout(win.elm_obj, self.edje_file, "pseudo")
            ##layout.elm_obj.size_get()
        #obj = gui.EdjeObject(self.main, self.edje_file, "tele-contacts_item")
        #obj.show()
            ##layout.elm_obj.content_set('base', obj.Edje)
            ##layout.elm_obj.show()
        #box.pack_end(obj.Edje)
        
        #sc = gui.elementary.Scroller(win.elm_obj)
        #sc.size_hint_weight_set(1.0, 1.0)
        #sc.size_hint_align_set(-1.0, -1.0)
        #sc.content_set(box)
        #sc.show()
        
        #box1 = gui.elementary.Box(win.elm_obj)
        #box1.pack_end(sc)
        #main_layout.elm_obj.content_set("contacts-items", box1)
        #main_layout.elm_obj.show()
        #box.show()
        #box1.show()
        #win.elm_obj.resize_object_add(main_layout.elm_obj)
        #win.elm_obj.show()
        
        #new_edje = gui.EdjeWSwallow(self.main, self.edje_file, 'tele-people', "contacts-items", self.edje_obj.Windows)
        #new_edje.Edje.name_set('contacts_list')
        #new_edje.Edje.size_set(480,560)
        #new_edje.Edje.pos_set(0,40)
        #new_edje.show(3)
        #swallow = self.phone_book_list.get_swallow_object()
        #new_edje.embed(swallow,self.phone_book_list.box,"contacts-items")
        ##self.phone_book_list.add_callback("*", "*",self.self_test)
        #self.phone_book_list.add_callback("call_contact", "tele", self.call_contact)
        #self.phone_book_list.add_callback("call_contact", "tele", new_edje.delete)

    ## open subwindow showing save-contact-window
    def add_contact_window(self,emission, source, param):
        logger.info("add contact in dialer")
        number = emission.part_text_get('num_field-text')
        logger.info("number is %s", number)
        new_edje = gui.EdjeWSwallow(self.main,self.edje_file,'save-number',"name-box", self.edje_obj.Windows, True)
        new_edje.Edje.size_set(480,590)
        new_edje.Edje.pos_set(0,50)
        new_edje.show(3)
        new_edje.Edje.part_text_set('number',number)
        name_field = gui.Edit(None)
        name_field.etk_obj.on_text_changed(self.change_text, new_edje)
        name_field.set_text('')
        box = gui.Box(None,1)
        box.add(name_field)
        new_edje.embed(box.etk_obj,box,"name-box")
        box.etk_obj.show_all()
        name_field.etk_obj.focus()
        
        new_edje.add_callback('close_window','*', new_edje.delete)
        new_edje.add_callback('save_contact','*', self.save_contact, **{'name_field':name_field,'number':number})
        
        
    ## CALL FUNCTIONS
    ## call from numpad
    def call(self, emission, signal, source):
        number = TelNumber(signal)
        #if ((number[0] in ['0', '1', '6'] or (number[0] == '+' and number[1] != '0')) and number[1:].isdigit()):
        #if ((number[0] in ['0', '1', '6'] or (number[0] == '+' and number[1] != '0')) and )
        if ((number[0].isdigit() or (number[0] == '+' and number[1] != '0')) and number[1:].isdigit()):
            logger.info(number.get_text())
            emission.part_text_set('num_field-text','')
            TeleCaller(self.main, number).start(err_callback=self.throw)
        elif signal[0] in ['*'] :
            self.ussd_service.send_ussd(signal)
        else :
            pass
            
    ## call from contact list
    def call_contact(self, emission, source, param, item = None):
        contact = item[0]
        logger.debug("call contact called")
        number = str(contact.tel)
        name = unicode(contact)
        TeleCaller("window", number, name).start(self.callback,self.callback)

# TODO: ??? make the Caller app better, using John idea : we define
#       for every call status the status of the gui.  Then we just
#       wait for status change and set up the gui in consequence It
#       means we have an automaton with a single state, much simpler
#       to deal with that what we have now


class TeleCaller(tichy.Application):
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
        logger.debug("caller run, names : %s", name)
        self.gsm_service = tichy.Service.get('GSM')
        self.dialog = tichy.Service.get('Dialog')
        self.storage = tichy.Service.get('TeleCom')
        self.main = self.storage.window
        self.audio_service = tichy.Service.get('Audio')
        self.main.etk_obj.visibility_set(1)
        self.main.etk_obj.title_set('Paroli Call')
        if self.audio_service.muted == 1:
            self.audio_service.audio_toggle()
            
        self.edje_file = os.path.join(os.path.dirname(__file__),'tele.edj')
        self.edje_obj_top_bar = gui.edje_gui(self.main,'tb',self.edje_file)
        self.edje_obj_top_bar.edj.size_set(480,40)
        self.edje_obj_top_bar.edj.pos_set(0,0)
        self.edje_obj = gui.edje_gui(self.main,'tele',self.edje_file)
        self.edje_obj.edj.size_set(480,550)
        self.edje_obj_top_bar.edj.show()
        self.edje_obj.edj.pos_set(0,40)
        self.edje_obj.edj.signal_callback_add("*", "embryo", self.embryo)
        self.edje_obj.edj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.edj.signal_callback_add("*", "dtmf", self.send_dtmf)
        self.edje_obj.edj.signal_callback_add("mute-toggle", "del-button", self.mute_toggle)
        self.edje_obj.edj.signal_callback_add("audio-toggle", "del-button", self.speaker_toggle)
        self.edje_obj_top_bar.edj.signal_callback_add("top-bar", "*", self.top_bar)
        #self.edje_obj.edj.signal_callback_add("*", "*", self.gui_signals)

        try:
            # The case when we have an incoming call
            # XXX: we should use an other way to check for a call object !
            if not isinstance(number, (basestring, tichy.Text)):
                call = number
                self.storage.call = call
                self.main.emit('call_active')
                self.edje_obj.edj.signal_emit('to_incoming_state',"*")
                self.edje_obj.edj.part_text_set('num_field-text',str(call.number.get_text()))
                self.edje_obj.edj.layer_set(2)
                self.edje_obj.edj.show()

                def make_active(emission, source, param):
                    # XXX: we should connect to the error callback
                    call.activate().start()

                self.edje_obj.edj.signal_callback_add("activate", "call", make_active)

            else:   # If not it means we want to initiate the call first
                display = str(TelNumber(number).get_text())
                self.edje_obj.edj.part_text_set('num_field-text',display)
                self.edje_obj.edj.signal_emit('to_dialing_state',"*")
                self.edje_obj.edj.layer_set(2)
                self.edje_obj.edj.show()
                call = self.gsm_service.create_call(number)
                call.connect("error", self.dialog.error)
                self.storage.call = call
                self.main.emit('call_active')
                yield call.initiate()

                def call_release_pre(emission, source, param):
                    # XXX: we should connect to the error callback
                    logger.info('call_release_pre')
                    call.release().start()
                    self.storage.call = None
                        
                self.edje_obj.edj.signal_callback_add("release", "call", call_release_pre)

            i, args = yield tichy.WaitFirst(tichy.Wait(call, 'activated'),tichy.Wait(call, 'released'),tichy.Wait(self.main, 'call_error'))
            if i == 0: #activated
                logger.debug("call activated")
                #self.storage.status.__set_value("activated")
                if self.audio_service.muted == 1:
                    self.audio_service.audio_toggle()
                
                
                #self.storage.main_window.emit('call_activated')
                self.edje_obj.edj.signal_emit('to_active_state',"*")
                #self.edje_obj.edj.part_text_set('num_field-text',TelNumber(call.number).get_text())

                def call_release(emission, source, param):
                    logger.info("releasing call")
                    # XXX: we should connect to the error callback
                    try:
                        call.release().start()
                    except Exception, e:
                        self.main.emit('call_error')

                self.edje_obj.edj.signal_callback_add("release", "call", call_release)
                yield tichy.WaitFirst(tichy.Wait(call, 'released'),tichy.Wait(self.main, 'call_error'))

            if call.status not in ['released', 'releasing']:
                try:
                    try:
                        call.release().start()
                        yield tichy.Wait(call, 'released')
                    except Exception, e:
                        self.main.emit('call_error')
                except Exception, e:
                    logger.error("Got error in caller : %s", e)
                    
            self.storage.call = None
            
            self.edje_obj.edj.delete()
            self.main.etk_obj.visibility_set(0)
            
        except Exception, e:
            logger.error("Got error in caller : %s", e)
            self.edje_obj.edj.delete()
            self.edje_obj_top_bar.edj.delete()
            self.main.etk_obj.visibility_set(0)
            raise    
    
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))

    def gui_signals(self,emission, source, param):
        pass

    def top_bar(self,emission, source, param):
        self.main.etk_obj.visibility_set(0)

    def add_digit(self,emission, source, param):
        logger.debug("dtmf would be sent")

    def send_dtmf(self, emission, signal, source):
        logger.info('sending dtmf')
        call = self.storage.call
        call.send_dtmf(signal).start()

    def mute_toggle(self, emission, signal, source):
        """mute/unmute the ringtone"""
        self.storage.call.mute_ringtone()

    def speaker_toggle(self, emission, signal, source):
        """Toggle the mic output - (un)mute mic"""
        self.storage.call.mute_toggle()

    def func_btn(self,emission, source, param):
        logger.debug("func btn called from %s", source)
        state = emission.part_state_get(param)
        logger.debug("%s", state[0])
        if param == 'call-button':

            if state[0] == 'default':
                logger.debug("nothing to be done")

            elif state[0] == 'incoming':
                self.accept_call(emission)

            elif state[0] == 'dialing':
                self.release_call(emission)

            elif state[0] == 'active':
                self.release_call(emission)

            elif state[0] == 'releasing':
                logger.debug("nothing to be done")

            else :
                logger.debug("unknown state for call button")

        elif param == 'del-button':

            if state[0] == 'default':
                logger.debug("nothing to be done")

            elif state[0] == 'incoming':
                logger.debug("nothing to be done")

            elif state[0] == 'dialing':
                logger.debug("nothing to be done")


            elif state[0] == 'active':
                logger.debug("would be muting")

            elif state[0] == 'releasing':
                logger.debug("nothing to be done")

            else :
                logger.debug("unknown state for del button")
        else :
            logger.debug("unknown button")

    def release_call(self,emission):
        logger.debug("release call Caller called")
        emission.signal_emit("release_call", "*")

    def accept_call(self,emission):
        logger.debug("accept call Caller called")
        emission.signal_emit("activate_call", "*")

##Service called when incoming call detected
class TeleCallerService(tichy.Service):
    service = 'TeleCaller'
    
    def __init__(self):
        super(TeleCallerService, self).__init__()
    
    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
    
    def call(self, parent, number, name=None):
        return TeleCaller('nothing', number, name)

    def _do_sth(self):
        pass

##Service to store some info
class TeleComService(tichy.Service):
    service = 'TeleCom'

    def __init__(self):
        dir(self)
        super(TeleComService, self).__init__()
    
    @tichy.tasklet.tasklet
    def init(self):
        #super(MyStorageService, self).__init__()
        self.window = gui.Window(None)
        #self.window.etk_obj.visibility_set(0)
        #self.window.etk_obj.lower()
        self.status = tichy.Text('None')
        self.call = None
        self.main_window = None
        yield self._do_sth()
    
    def _do_sth(self):
        #print "_do_sth called ", self
        #print self.window.etk_obj.visibility_get()
        dir(self.window.etk_obj)
    
    def add_launcher(self, launcher):
        self.main_window = launcher

    def get_active(self):
        return self.window
        
    def set_active(self,call):
        self.call = call

class PINApp(tichy.Application):

    name = 'PINApp'
    icon = 'icon.png'

    def run(self, window, text="", name=None, input_method=None):


        logger.info("PIN called")
        ##set edje_file
        self.edje_file = os.path.join(os.path.dirname(__file__),'tele.edj')
        self.main = window
        self.main.show()

        self.edje_obj = gui.edje_gui(self.main, 'pin_enter', self.edje_file)
        self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.signal_callback_add("*", "sending_pin", self.call_btn_pressed)
        self.edje_obj.edj.signal_callback_add("*", "embryo", self.embryo)
        self.edje_obj.edj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.edj.show()

        yield tichy.Wait(self.main, 'value_received')

        number = self.edje_obj.edj.part_text_get("pin-text")
        self.edje_obj.edj.delete()
        self.main.etk_obj.visibility_set(0)
        yield number


    def embryo(self, emission, signal, source):
        logger.info('embryo says: ' + signal)

    def func_btn(self,emission,source,param):
        if param == 'call-button':
              self.call_btn_pressed(emission, source, param)
        elif param == 'del-button':
              self.number_edit_del(emission,source,param)

    def call_btn_pressed(self,emission, signal, source):
        logger.info(signal)
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
        logger.debug("number_edit del called")
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

    service = 'TelePIN'

    def edit(self, parent, text="", name=None, input_method=None):
        """The only function defined in the TextEditService"""
        return PINApp(parent, text, name=name, input_method=input_method)
