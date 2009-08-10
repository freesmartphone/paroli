# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2009 Laszlo KREKACS
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
logger = logging.getLogger('Calculator')

import os
import tichy
from tichy import gui
import sys
from tel_number import TelNumber
from dialog import Dialog

class CalculatorApp(tichy.Application):
    name = 'Calculator'
    icon = ''
    category = 'launcher'

    def run(self, parent=None, standalone=False):

        ##set edje_file
        self.edje_file = os.path.join(os.path.dirname(__file__),'calculator.edj')

        ## edje_file, group, x=1.0, y=1.0, topbar=False, onclick=None
        self.window = gui.elm_layout_window(self.edje_file, "main", None, None, False)
        self.edje_obj = self.window.main_layout

        ## close the Tele app, with the back button
        self.edje_obj.add_callback("back", "edje", self.signal) 
        
        parent.emit("unblock")

        ##wait until main object emits back signal or delete is requested
        i, args = yield WaitFirst(Wait(self.window, 'delete_request'),tichy.Wait(self.window, 'back'),tichy.Wait(self.window.window,'closing'),tichy.Wait(self.edje_obj, 'back'))
        logger.info('Calculator closing')
        
        if i != 2:
            self.window.delete()

    def signal(self, emission, signal, source):
        """ Callback function. It invokes, when the "back" button clicked."""
        logger.info("calculator.py:signal() emmision: %s, signal: %s, source: %s", 
                    str(emission), str(signal), str(source))
        self.window.emit('back')
        
    ##DEBUG FUNCTIONS 
    ## msgs from embryo
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))

    ##DEBUG FUNCTIONS
    def test(self, *args, **kargs):
        logger.info('test called')
        try:
            logger.info("test called with %s and %s", args, kargs)
        except Exception, e:
            print e

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
    
    @tichy.tasklet.tasklet
    def num_field(self, emission, signal, source):
        logger.info("num field pressed")
        number = emission.part_text_get(source)
        if number == None or len(number) == 0:
            logger.info("no number found")
            createService = tichy.Service.get('ContactCreate')
            num = yield  createService.contactList(self.window,self.window.main_layout)
            emission.part_text_set('num_field-text', str(num.tel))
        else :
            logger.info("number found")
            service = tichy.Service.get('ContactCreate')
            service.create(self.window, str(number)).start()
            emission.part_text_set('num_field-text', "")
