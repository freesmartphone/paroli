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
logger = logging.getLogger('Launcher')

import os
import tichy
from tichy import gui
import sys
from tichy.service import Service
import ecore
import dbus
from tel_number import TelNumber

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
            self.main = gui.Window(None,480,640)
            logger.info('launcher running in standalone mode')
        else:
            self.main = gui.Window(None)
            logger.info('launcher running in windowed mode')

        self.main.show()

        self.active_app = None
        
        self.main.etk_obj.title_set('Home')
        
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.edje_obj = gui.EdjeObject(self.main,self.edje_file,'launcher')
        self.edje_obj.show(1)
        
        self.storage = tichy.Service('Storage')
        self.connector = self.storage.window
        self.connector.connect('call_active',self.set_caller)
        self.edje_obj.add_callback("launch_app", "*", self.launch_app)
        self.edje_obj.add_callback("test", "*", self.test)
        self.edje_obj.add_callback("quit_app", "*", self.quit_app)
        
        yield tichy.Wait(self.main, 'back')
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
        
        
    def launch_app(self, emission, source, name):
        logging = "launching :" + str(name)
        logger.info(str(logging))
        print name
        if name == 'Tele' and self.storage.call != None:
            self.storage.window.etk_obj.visibility_set(1)
        else:  
            for app in tichy.Application.subclasses:
                if app.name == name:
                    try:
                        app(self.main,self.standalone).start() 
                    except Exception, e:
                        dialog = tichy.Service('Dialog')
                        dialog.error(self.main, e)
            self.edje_obj.signal('app_active',"*")
        self.active_app = name
               
    def quit_app(self, emission, source, name):
    
        emitted = 'back_'+self.active_app    
        self.main.emit(emitted)
                
        self.edje_obj.signal("switch_clock_off","*")
        self.active_app = None
        
    def _status_modified(self,*args,**kargs):
        status = self.storage.status
        if status == 'active':
            self._on_call_activated()
            self.storage.call.connect('released',self._on_call_released())
        else:
            self._on_call_released()
    
    def set_caller(self, sender):
        logger.info('call logged')
        self.storage.call.connect('released', self._on_call_released)
        self.main.emit('hide_Tele')
        print "active app: ", self.active_app
        if self.active_app == 'Tele':
            self.edje_obj.signal('switch_clock_off',"*")
        self._on_call_activated() 
            
    def test(self, emission, source, param):
        logger.info('test called')
        try:
            self.connector.emit('call_active')
        except Exception, e:
            print e
    
    def _on_call_activated(self,*args,**kargs):
        
        number = TelNumber(self.storage.call.number)
        text = '<normal>Tele</normal> <small>' + str(number.get_text()) +'</small>'
        self.edje_obj.Edje.part_text_set('Teletesting_textblock',text)
    
    def _on_call_released(self,*args,**kargs):
        self.main.emit('show_Tele')
        if self.active_app == 'Tele':
            self.edje_obj.signal('app_active',"*")
            
        text = '<normal>Tele</normal> <small></small>'
        self.edje_obj.Edje.part_text_set('Teletesting_textblock',text)