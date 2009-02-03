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
    category = 'hidden' # So that we see the app in the launcher
    
    def run(self, parent=None, standalone=False):
        #logger.info('launcher launching')
        self.standalone = standalone
        self.advanced = tichy.config.getboolean('advanced-mode',
                                                'activated', False)
        self.x = 480
        if self.standalone:
            self.y = 640
            logger.info('launcher running in standalone mode')
        else:
            self.y = 580
            logger.info('launcher running in windowed mode')

        self.main = gui.Window(None,self.x,self.y)

        self.main.show()

        self.active_app = None
        
        self.main.etk_obj.title_set('Home')
        
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.edje_obj = gui.EdjeWSwallow(self.main,self.edje_file,'launcher','link-box')
        
        if self.advanced == False:
            ##create list of apps from list of registered apps
            apps = ['Paroli-I/O',"Msgs","Paroli-Dialer","Pixels","Paroli-Contacts"]
            
            
        else:
            apps = []
            for app in tichy.Application.subclasses:
                if app.category == 'launcher':
                    logger.info("adding - %s to launcher", app.name)
                    apps.append(app.name)
            
        box = gui.edje_box(self,'V',1)
        box.box.show()
        self.app_objs = {}
        for a in apps:
            canvas = gui.etk.Canvas()
            link_obj = gui.EdjeObject(self.main,self.edje_file,'link')
            canvas.object_add(link_obj.Edje)
            box.box.append(canvas, gui.etk.VBox.START, gui.etk.VBox.NONE, 0)
            link_obj.Edje.part_text_set("texter",a)
            link_obj.Edje.part_text_set("testing_textblock","<normal>" + a + "</normal><small></small>")
            link_obj.Edje.layer_set(5)
            link_obj.Edje.show()
            link_obj.add_callback("*", "launch_app", self.launch_app)
            app_obj = [canvas,link_obj]
            self.app_objs[a] = app_obj
        self.edje_obj.embed(box.scrolled_view,box,"link-box")
        box.box.show()
            ##create list of apps according to specs
          
        self.edje_obj.show(1)
        
        self.edje_obj.Edje.size_set(480,580)
        
        self.storage = tichy.Service('TeleCom')
        self.connector = self.storage.window
        self.connector.connect('call_active',self.set_caller)
        self.edje_obj.add_callback("*", "launch_app", self.launch_app)
        self.edje_obj.add_callback("*", "embryo", self.embryo)
        self.edje_obj.add_callback("test", "*", self.test)
        self.edje_obj.add_callback("quit_app", "*", self.quit_app)
        
        ##current hack
        self.standalone = True
        
        yield tichy.Wait(self.main, 'back')
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window
        
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))
    
    def launch_app(self, emission, signal, source):
        logging = "launching :" + str(signal)
        logger.info(str(logging))
        if signal == 'Tele' and self.storage.call != None:
            self.storage.window.etk_obj.visibility_set(1)
        else:  
            for app in tichy.Application.subclasses:
                if app.name == signal:
                    try:
                        app(self.main, standalone=self.standalone).start() 
                    except Exception, e:
                        dialog = tichy.Service('Dialog')
                        dialog.error(self.main, e)
            self.edje_obj.signal('app_active',"*")
        self.active_app = signal
               
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
        self.app_objs['Tele'][1].Edje.part_text_set('testing_textblock',text)
    
    def _on_call_released(self,*args,**kargs):
        self.main.emit('show_Tele')
        if self.active_app == 'Tele':
            self.edje_obj.signal('app_active',"*")
            
        text = '<normal>Tele</normal> <small></small>'
        self.app_objs['Tele'][1].Edje.part_text_set('testing_textblock',text)
