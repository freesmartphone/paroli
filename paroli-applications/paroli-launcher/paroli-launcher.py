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

class Launcher_App(tichy.Application):
    name = 'Paroli-Launcher'
    icon = 'icon.png'
    category = 'main' # So that we see the app in the launcher
    
    def run(self, parent=None, text = ""):
        #logger.info('launcher launching')
        if isinstance(text, str):
            text = tichy.Text(text)
        self.standalone = text
        if self.standalone == 1:
            self.main = gui.main_edje()
            logger.info('launcher running in standalone mode')
        else:
            self.main = gui.Window(None)
            logger.info('launcher running in windowed mode')
        #self.storage = tichy.Service('Storage')
        #self.storage.main_window = self.main
        self.active_app = None
        self.main.etk_obj.title_set('Home')
        self.main.etk_obj.fullscreen = 0
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.edje_obj = gui.edje_gui(self.main,'launcher',self.edje_file)
        self.edje_obj.edj.layer_set(1)
        self.edje_obj.edj.show()
        
        #self.storage.status.connect('modified', self._status_modified)
        #self.storage.main_window.connect('released', self._on_call_released)
        self.edje_obj.edj.signal_callback_add("launch_app", "*", self.launch_app)
        self.edje_obj.edj.signal_callback_add("quit_app", "*", self.quit_app)
        
        yield tichy.Wait(self.main, 'back')
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
        
        
    def launch_app(self, emission, source, name):
        logging = "launching :" + str(name)
        logger.info(str(logging))
        
        for app in tichy.Application.subclasses:
            if app.name == name:
                app(self.main,self.standalone).start() 
        
        self.active_app = name
               
    def quit_app(self, emission, source, name):
    
        emitted = 'back_'+self.active_app    
        self.main.emit(emitted)
                
        self.edje_obj.edj.signal_emit("switch_clock_off","*")
        
    def _status_modified(self,*args,**kargs):
        status = self.storage.status
        if status == 'active':
            self._on_call_activated()
            self.storage.call.connect('released',self._on_call_released())
        else:
            self._on_call_released()
            
    def _on_call_activated(self,*args,**kargs):
        text = '"<normal>Tele</normal><small>' + self.storage.call.peer +'</small>"'
        self.edje_obj.edj.part_text_set('Teletesting_textblock','')
    
    def _on_call_released(self,*args,**kargs):
        text = '"<normal>Tele</normal><small></small>"'
        self.edje_obj.edj.part_text_set('Teletesting_textblock','')