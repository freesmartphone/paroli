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
logger = logging.getLogger('applications.calculator')

from os.path import join, dirname
from paroli.gui import ElementaryLayoutWindow
from tichy.service import Service
from tichy.application import Application
from tichy.tasklet import WaitFirst, Wait, tasklet

class CalculatorApp(Application):
    name = 'Calculator'
    icon = 'icon.png'
    category = 'launcher'  # So that we see the app in the launcher

    def run(self, parent=None, standalone=False):

        ##set edje_file
        self.edje_file = join(dirname(__file__),'calculator.edj')

        ## edje_file, group, x=1.0, y=1.0, topbar=False, onclick=None
        self.window = ElementaryLayoutWindow(self.edje_file, "main", None, None, False)
        self.edje_obj = self.window.main_layout

        ## close the Calculator app, with the back button
        self.edje_obj.add_callback("back", "edje", self.signal) 
        
        parent.emit("unblock")

        ##wait until main object emits back signal or delete is requested
        i, args = yield WaitFirst(Wait(self.window, 'delete_request'),
                                  Wait(self.window, 'back'),
                                  Wait(self.window.window,'closing'),
                                  Wait(self.edje_obj, 'back'))
        logger.info('Calculator closing')
        
        if i != 2:
            self.window.delete()

    def signal(self, emission, signal, source):
        """ Callback function. It invokes, when the "back" button clicked."""
        logger.info("calculator.py:signal() emmision: %s, signal: %s, source: %s", 
                    str(emission), str(signal), str(source))
        self.window.emit('back')

    ##DEBUG FUNCTIONS
    ## general output check
    def self_test(self, *args, **kargs):
        txt = "self test called with args: ", args, "and kargs: ", kargs
        logger.info(txt)

    ## callback one (used?)
    def callback(self,*args,**kargs):
        txt = "callback called with args: ", args, "and kargs: ", kargs
        logger.info(txt)
