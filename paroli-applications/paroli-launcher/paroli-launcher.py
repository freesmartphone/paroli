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
logger = logging.getLogger('app.launcher')

import os
import tichy
from tichy import gui
import sys
from tichy.service import Service
import ecore
import dbus
from subprocess import call

class I_O_App(tichy.Application):
    name = 'Paroli-Launcher'
    icon = 'icon.png'
    category = 'main' # So that we see the app in the launcher
    
    def run(self, parent=None, text = ""):
        if isinstance(text, str):
            text = tichy.Text(text)
        self.main = parent
        self.main.etk_obj.title_set('Home')
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.edje_obj = gui.edje_gui(self.main,'launcher',self.edje_file)
        self.edje_obj.edj.layer_set(2)
        self.edje_obj.edj.show()
        
        #self.edje_obj.edj.signal_callback_add("edit_btn_clicked", "*", self.edit_mode)
        self.edje_obj.edj.signal_callback_add("launch_app", "*", self.launch_app)
        
        yield tichy.Wait(self.main, 'back')
        #print dir(self.main.children)
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
        
        
    def launch_app(self, emission, source, name):
        logging = "launching :" + str(name)
        logger.info(str(logging))
        
        try:
            retcode = call("python" + " /usr/share/paroli.git/paroli-scripts/paroli-launcher --launch Paroli-I/O", shell=True)
            if retcode < 0:
                print "Child was terminated by signal", -retcode
            else:
                print "Child returned", retcode
        except OSError, e:
            print "Execution failed:", e

        
        
        #bus = dbus.SystemBus()
        
        #try:
            #launcher = bus.get_object('org.tichy.launcher', '/Launcher')
            #launcher_2 = dbus.Interface(launcher, 'org.tichy.Launcher')
        #except Exception, e:
            #print e
          
        #launcher_2.Launch(name)