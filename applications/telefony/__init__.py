# -*- coding: utf-8 -*-
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

from logging import getLogger
logger = getLogger('applications.telefony')

from os.path import join, dirname
from tichy.application import Application
from tichy.tasklet import Wait, WaitFirst, tasklet
from tichy.service import Service
from tichy.text import Text
from tichy import mainloop
from paroli.gui import ElementaryLayoutWindow, ElementaryLayout
from paroli.tel_number import TelNumber

class TelefonyDialer(Application):
    name = 'Dialer'
    icon = 'icon.png'
    category = 'launcher'
    launcher_info = ['TeleCom2',"caller"]

    def run(self, parent=None, standalone=False):

        ##set edje_file
        self.edje_file = join(dirname(__file__),'tele.edj')

        self.window = ElementaryLayoutWindow(self.edje_file, "main", None, None, True)
        self.edje_obj = self.window.main_layout

        ##connect to tichy's contacts service
        self.contact_service = Service.get('Contacts')

        ##connect to tichy's ussd service
        self.ussd_service = Service.get('Ussd')
        self.edje_obj.add_callback("num_field_pressed", "*", self.num_field_action)

        self.edje_obj.add_callback("*", "embryo", self.embryo)
        self.edje_obj.add_callback("*", "call", self.call)

        ## close the Tele app, with the back button
        self.edje_obj.add_callback("back", "edje", self.signal) 
        
        parent.emit("unblock")

        ##wait until main object emits back signal or delete is requested
        i, args = yield WaitFirst(Wait(self.window, 'delete_request'),
                                  Wait(self.window, 'back'),
                                  Wait(self.window.window,'closing'),
                                  Wait(self.edje_obj, 'back'))
        logger.info('Tele closing')

        if i != 2:
            self.window.delete()

    def signal(self, emission, signal, source):
        """ Callback function. It invokes, when the "back" button clicked."""
        logger.info("tele2.py:signal() emmision: %s, signal: %s, source: %s", 
                    str(emission), str(signal), str(source))
        self.window.emit('back')
        
    ##DEBUG FUNCTIONS 
    ## msgs from embryo
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + signal)

    ##DEBUG FUNCTIONS
    def test(self, *args, **kargs):
        logger.info('test called')
        try:
            logger.info("test called with %s and %s", args, kargs)
        except Exception, e:
            logger.exception('test')

    ## CALL FUNCTIONS
    ## call from numpad
    def call(self, emission, signal, source):
        number = TelNumber(signal)
        if ((number[0].isdigit() or (number[0] == '+' and number[1] != '0')) and number[1:].isdigit()):
            emission.part_text_set('num_field-text','')
            TeleCaller2(self.window, number, None, self.edje_obj).start(err_callback=self.throw)
        elif signal[0] in ['*'] :
            emission.part_text_set('num_field-text','')
            self.ussd_service.send_ussd(signal)
        else :
            pass

    ## callback one (used?)
    def callback(self,*args,**kargs):
        txt = "callback called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    ## general output check
    def self_test(self, *args, **kargs):
        txt = "self test called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    ## MISC FUNCTIONS
    ## switch to either open contacts or save number
    def num_field_action(self, emission, signal, source):
        self.num_field(emission, signal, source).start()

    @tasklet
    def num_field(self, emission, signal, source):
        logger.info("num field pressed")
        number = emission.part_text_get(source)
        if number == None or len(number) == 0:
            logger.info("no number found")
            createService = Service.get('ContactCreate')
            num = yield  createService.contactList(self.window,self.window.main_layout)
            emission.part_text_set('num_field-text', str(num.tel))
        else :
            logger.info("number found")
            service = Service.get('ContactCreate')
            service.create(self.window, str(number)).start()
            emission.part_text_set('num_field-text', "")

class TeleCaller2(Application):
    """This is the application that deal with the calling sequence
    """

    def run(self, parent, number, name=None, layout=None):
        """show the Caller window

        :Parameters:

            parent : `paroli.gui.Widget`
                The parent window

            number : str | `tichy.Text` | Call object

                If the number is a string, we consider it to the
                number to call, otherwise we consider it to be a Call
                object that is already active.
        """
        logger.debug("caller run, names : %s", name)

        self.storage = Service.get('TeleCom2')
        self.gsm_service = Service.get('GSM')
        self.dialog = Service.get('Dialog')
        self.audio_service = Service.get('Audio')
        self.usage_service = Service.get('Usage')
        self.edje_file = join(dirname(__file__),'tele.edj')
        logger.info("occupy cpu")
        self.usage_service.occupy_cpu().start()
        if layout:
            self.main = parent
            self.main.topbar.onclick = 'hide'
            layout.elm_obj.hide()
            self.layout = ElementaryLayout(self.main.window, self.edje_file, "main")
            self.main.bg.elm_obj.content_set("content-swallow", self.layout.elm_obj)

        else:
            self.main = ElementaryLayoutWindow(self.edje_file, "main", None, None, True)
            self.main.topbar.onclick = 'hide'
            self.layout = self.main.main_layout

        self.storage.window = self.main

        if self.audio_service.muted == 1:
            self.audio_service.audio_toggle()

        self.button = Service.get('Buttons')
        self.button_oid = self.button.connect('aux_button_pressed', self.audio_rotate)

        self.TopBarService = Service.get("TopBar")
        self.TopBarService.volume_change(self.audio_service.get_speaker_volume())

        self.main.connect("dehide", self.dehide_call)
        self.main.connect("hide", self.hide_call)

        self.edje_obj = self.layout.elm_obj.edje_get()
        self.edje_obj.signal_callback_add("*", "embryo", self.embryo)
        self.edje_obj.signal_callback_add("add_digit", "*", self.add_digit)
        self.edje_obj.signal_callback_add("*", "dtmf", self.send_dtmf)
        self.edje_obj.signal_callback_add("mute-toggle", "del-button", self.mute_toggle)
        self.edje_obj.signal_callback_add("audio-toggle", "del-button", self.speaker_toggle)
        self.SoundsService = Service.get("Sounds")


        try:
            # The case when we have an incoming call
            # XXX: we should use an other way to check for a call object !
            if not isinstance(number, (basestring, Text)):
                call = number
                try:
                    self.SoundsService.call()
                except Exception,e:
                    logger.exception("TeleCaller2 %s", e)
                self.main.window.connect("close",call.release().start)
                self.storage.call = call
                self.main.emit('call_active')
                self.edje_obj.signal_emit('to_incoming_state',"*")
                self.edje_obj.part_text_set('num_field-text',unicode(call.number.get_text()).encode('utf-8'))
                self.edje_obj.layer_set(2)
                self.edje_obj.show()

                def make_active(emission, source, param):
                    # XXX: we should connect to the error callback
                    self.SoundsService.Stop()
                    call.activate().start()

                self.storage.caller.value = call.number.get_text()

                self.edje_obj.signal_callback_add("activate", "call", make_active)

            else:   # If not it means we want to initiate the call first
                display = unicode(TelNumber(number).get_text()).encode("utf-8")
                logger.info("display is %s", display)
                self.edje_obj.part_text_set('num_field-text', display)
                self.edje_obj.signal_emit('to_dialing_state',"*")
                self.edje_obj.layer_set(2)
                self.edje_obj.show()
                call = self.gsm_service.create_call(number)
                call.connect("error", self.dialog.error)
                self.main.window.connect("close",call.release().start)
                self.storage.caller.value = call.number.get_text()
                self.storage.call = call
                self.main.emit('call_active')
                yield call.initiate()

                def call_release_pre(emission, source, param):
                    # XXX: we should connect to the error callback

                    logger.info('call_release_pre')
                    self.edje_obj.signal_callback_del("release", "call", call_release_pre)
                    call.release().start()
                    self.storage.call = None
                    logger.info('call_release_pre done')

                self.edje_obj.signal_callback_add("release", "call", call_release_pre)

            i, args = yield WaitFirst(Wait(call, 'activated'),Wait(call, 'released'),Wait(self.main, 'call_error'))
            if i == 0: #activated
                logger.debug("call activated")

                if self.audio_service.muted == 1:
                    self.audio_service.audio_toggle()

                self.edje_obj.signal_emit('to_active_state',"*")

                def call_release(emission, source, param):
                    logger.info("releasing call")
                    # XXX: we should connect to the error callback
                    self.edje_obj.signal_callback_del("release", "call", call_release)
                    try:
                        call.release().start()
                    except Exception, e:
                        logger.exception('TeleCaller2')
                        self.main.emit('call_error')

                self.edje_obj.signal_callback_add("release", "call", call_release)

                yield WaitFirst(Wait(call, 'released'),Wait(self.main, 'call_error'))

            if call.status not in ['released', 'releasing']:
                try:
                    try:
                        logger.info("call not in released or releasing")
                        call.release().start()
                        yield Wait(call, 'released')
                    except Exception, e:
                        logger.exception('TeleCaller2')
                        self.main.emit('call_error')
                except Exception, e:
                    logger.exception("Got error in caller : %s", e)
                    self.SoundsService.Stop()


            #logger.info("releasing cpu")
            self.usage_service.release_cpu().start()
            self.SoundsService.Stop()        
            self.storage.caller.value = ""
            self.storage.call = None

            if self.main.window.elm_obj.is_deleted() == False:
                if layout:
                    layout.elm_obj.show()
                    self.layout.elm_obj.delete()
                    self.main.restore_orig()
                    self.main.topbar.onclick = 'back'
                else:
                    self.main.delete()
            self.storage.window = None
        except Exception, e:
            logger.exception("Got error in caller : %s", e)
            self.SoundsService.Stop()
            if self.main.window.elm_obj.is_deleted() == False:
                if layout:
                    layout.elm_obj.show()
                    self.main.restore_orig()
                    self.main.topbar.onclick = 'back'
                else:
                    self.main.delete()
            self.storage.window = None
            raise
        try:
            self.TopBarService.profile_change()
        except:
            pass
        self.button.disconnect(self.button_oid)

    def hide_call(self, *args, **kargs):
        logger.info("hiding caller")
        self.main.window.elm_obj.hide()
        self.main.topbar.onclick = 'back'

    def dehide_call(self, *args, **kargs):
        self.main.window.elm_obj.show()
        self.main.topbar.onclick = 'hide'

    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + signal)

    def audio_rotate(self, *args, **kargs):
        try:
            current = self.audio_service.get_speaker_volume()
            all_values = [20, 40, 60, 80, 100]
            if all_values.count(current) == 0:
              current = 40

            current_index = all_values.index(current)

            if len(all_values)-1 == current_index:
                new = all_values[0]
            else:
                new = all_values[current_index + 1]
            self.audio_service.set_speaker_volume(new)
            self.TopBarService.volume_change(str(new))
            logger.info("current: %s new: %s", current, self.audio_service.get_speaker_volume())
        except Exception, e:
            logger.exception('audio_service %s', e)

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
class TeleCallerService(Service):
    service = 'TeleCaller2'

    def __init__(self):
        super(TeleCallerService, self).__init__()

    @tasklet
    def init(self):
        yield self._do_sth()

    def call(self, parent, number, name=None):
        self.storage = Service.get('TeleCom2')
        if self.storage.call == None:
            return TeleCaller2('nothing', number, name)
        else:
            self.dialog = Service.get('Dialog')
            return self.dialog.dialog(None, "Error", "there is already an active call")

    def _do_sth(self):
        pass

##Service to store some info
class TeleComService(Service):
    service = 'TeleCom2'

    def __init__(self):
        #dir(self)
        super(TeleComService, self).__init__()

    @tasklet
    def init(self):
        self.window = None
        self.status = Text('None')
        self.call = None
        self.caller = Text(" ")
        self.main_window = None
        yield self._do_sth()

    def _do_sth(self):
        dir(self)

    def add_launcher(self, launcher):
        self.main_window = launcher

    def get_active(self):
        return self.window

    def set_active(self,call):
        self.call = call

class PINApp2(Application):

    name = 'PINApp2'
    icon = 'icon.png'

    def run(self, window, text="", name=None, input_method=None, variable=None):

        logger.info("PIN2 called")
        ##set edje_file
        self.edje_file = join(dirname(__file__),'tele.edj')

        self.main = ElementaryLayoutWindow(self.edje_file, "pin_enter")
        #logger.info("PIN2 main generated")

        if hasattr(self.main.topbar, "tb"):
            tb = self.main.topbar.tb.edje
            tb.signal_emit("hide_clock", "*")
            tb.signal_emit("show_pin_title", "*")

        self.edje_obj = self.main.main_layout.edje

        if text != "":
            tb.part_text_set("title",  text)

        self.edje_obj.signal_callback_add("*", "sending_pin", self.call_btn_pressed)
        #self.edje_obj.signal_callback_add("*", "embryo", self.embryo)

        i, args = yield WaitFirst(Wait(self.main, 'value_received'),Wait(self.main.window,'closing'))

        if i == 0: #value_received
            number = self.edje_obj.part_text_get("pin-text")
            if variable != None:
                variable.value = number
            self.main.delete()
            yield number
        elif i == 1:
            mainloop.quit()

    def embryo(self, emission, signal, source):
        logger.info('embryo says: XXXX')

    def call_btn_pressed(self,emission, signal, source):
        self.main.emit('value_received')


class MyTextEditService(Service):
    """Service to edit text

    By creating this service class, we allow any application in need
    of a text editor to use the applicaton we defined previously.
    """

    service = 'TelePIN2'

    def edit(self, parent, text="", name=None, input_method=None):
        """The only function defined in the TextEditService"""
        return PINApp2(parent, text, name=name, input_method=input_method)
