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
import ecore
import dbus
from tel_number import TelNumber
import subprocess
import re

class Launcher_App(tichy.Application):
    name = 'Paroli-Launcher'
    icon = 'icon.png'
    category = 'hidden' # So that we see the app in the launcher
    
    def run(self, parent=None, standalone=False):
        #logger.info('launcher launching')
        self.standalone = standalone
        self.advanced = tichy.config.getboolean('advanced-mode',
                                                'activated', False)

        self.w = 480
        if self.standalone:
            self.h = 640
            logger.info('launcher running in standalone mode')
        else:
            self.h = 590
            logger.info('launcher running in windowed mode')

        self.main = gui.Window(None, self.w, self.h)

        self.main.show()

        self.active_app = None
        
        self.main.etk_obj.title_set('Home')
        
        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.edje_obj = gui.EdjeWSwallow(self.main, self.edje_file, 'launcher', 'link-box')
        
        if self.advanced == False:
            ##create list of apps from list of registered apps
            apps = ['Paroli-I/O',"Msgs","Paroli-Dialer","Pixels","Paroli-Contacts"]
        else:
            apps = []
            for app in tichy.Application.subclasses:
                if app.category == 'launcher':
                    logger.info("adding - %s to launcher", app.name)
                    apps.append(app)
            
        box = gui.edje_box(self,'V',1)
        box.box.show()
        self.app_objs = {}
        for app in apps:
            canvas = gui.etk.Canvas()
            link_obj = gui.EdjeObject(self.main,self.edje_file,'link')
            canvas.object_add(link_obj.Edje)
            box.box.append(canvas, gui.etk.VBox.START, gui.etk.VBox.NONE, 0)
            link_obj.Edje.part_text_set("texter",app.name)
            link_obj.Edje.part_text_set("testing_textblock","<normal>" + app.name + "</normal><small></small>")
            if hasattr(app,'launcher_info'):
                attr = app.launcher_info
            else:
                attr = 0
            link_obj.Edje.layer_set(5)
            link_obj.Edje.show()
            link_obj.add_callback("*", "launch_app", self.launch_app)
            app_obj = [canvas,link_obj,attr]
            self.app_objs[app.name] = app_obj
        self.edje_obj.embed(box.scrolled_view,box,"link-box")
        box.box.show()
            ##create list of apps according to specs
        
        self.edje_obj.Edje.size_set(self.w, self.h)
        
        self.storage = tichy.Service.get('TeleCom')
        self.connector = self.storage.window
        self.connector.connect('call_active',self.set_caller)
        self.edje_obj.add_callback("*", "launch_app", self.launch_app)
        self.edje_obj.add_callback("*", "embryo", self.embryo)
        self.edje_obj.add_callback("test", "*", self.test)
        self.edje_obj.add_callback("quit_app", "*", self.quit_app)
        #self.battery_capacity(0, 50)
        ##current hack
        self.standalone = True
        
        self.msg = tichy.Service.get('Messages')
        if self.msg.ready == False :
            self.msg.connect('ready',self.unblock_screen)
        else:
            self.unblock_screen()
        
        self.gsm = tichy.Service.get('GSM')
        self.gsm.connect('network-strength', self.network_strength)
        
        self.power = tichy.Service.get('Power')
        self.power.connect('battery_capacity', self.battery_capacity)
        self.power.connect('battery_status', self.battery_status)
        self.battery_capacity(0,10)
        
        self.button = tichy.Service.get('Buttons')
        self.button.connect('aux_button_pressed', self.switch_profile)
        
        self.prefs = tichy.Service.get('Prefs')
        self.audio_service = tichy.Service.get('Audio')
        
        self.ussd = tichy.Service.get('Ussd')
        self.ussd.connect('incoming', self.incoming_ussd)
        self._get_paroli_version()
        
        #elm = gui.elm_test()
        
        self.edje_obj.show(1)
        #print dir(self.edje_obj.Edje.evas_get())
        yield tichy.Wait(self.main, 'back')
        for i in self.main.children:
          i.remove()
        self.main.etk_obj.hide()   # Don't forget to close the window

    def unblock_screen(self, *args, **kargs):
        logger.info('unblocking screen')
        for app in self.app_objs:
            if self.app_objs[app][2] != 0:
                connector = self.app_objs[app][2][0]
                connector.connect('modified', self._set_subtext, app)
                self._set_subtext(self.app_objs[app][2][0].value, app)
                
        self.edje_obj.signal("ready","*")

    def _set_subtext(self, *args, **kargs):
        if args[0] != "0":
          value = args[0]
        else:
          value = ''
        app = args[1]
        edje_obj = self.app_objs[app][1]
        text = '<normal>' + app + '</normal> <small>' + str(value) +'</small>'
        edje_obj.Edje.part_text_set('testing_textblock',text)

    def launch_app(self, emmision, signal, source):
        """connected to the 'launch_app' edje signal"""
        self._launch_app(str(signal)).start()

    @tichy.tasklet.tasklet
    def _launch_app(self, name):
        """launch an application, and wait for it to either quit,
        either raise an exception.
        """
        logger.info("launching %s", name)
        # XXX: The launcher shouldn't know anything about this app
        if name == 'Tele' and self.storage.call != None:
            self.storage.window.etk_obj.visibility_set(1)
        else:
            app = tichy.Application.find_by_name(name)
            try:
                self.active_app = name
                self.edje_obj.signal('app_active',"*")
                # minus top-bar, 50, magic number here for now. 
                #self.main.etk_obj.move_resize(0, 50, self.w, self.h-50)
                yield app(self.main, standalone=self.standalone)
            except Exception, ex:
                logger.error("Error from app %s : %s", name, ex)
                yield tichy.Service.get('Dialog').error(self.main, ex)
            finally:
                self.edje_obj.signal("switch_clock_off","*")
    
    def incoming_ussd(self, stuff, msg):
        """connected to the 'incoming_message' edje signal"""
        print stuff
        print msg
        self._incoming_ussd(str(msg[1])).start()
    
    @tichy.tasklet.tasklet
    def _incoming_ussd(self, msg):
        logger.info('incoming ussd registered')
        yield tichy.Service.get('Dialog').dialog(self.main, 'Ussd', msg)
        
    
    def quit_app(self, emission, source, name):
    
        emitted = 'back_'+str(self.active_app)    
        logger.debug('closing' + str(self.active_app))
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
        logger.info("active app: %s", self.active_app)
        if self.active_app == 'Tele':
            self.edje_obj.signal('switch_clock_off',"*")
        self._on_call_activated() 
        
    ##MAIN FUNCTIONS
    
    def _on_call_activated(self, *args, **kargs):
        
        number = TelNumber(self.storage.call.number)
        text = '<normal>Tele</normal> <small>' + str(number.get_text()) +'</small>'
        self.app_objs['Tele'][1].Edje.part_text_set('testing_textblock',text)
    
    def _on_call_released(self, *args, **kargs):
        self.main.emit('show_Tele')
        if self.active_app == 'Tele':
            self.edje_obj.signal('app_active',"*")
            
        text = '<normal>Tele</normal> <small></small>'
        self.app_objs['Tele'][1].Edje.part_text_set('testing_textblock',text)

    def network_strength(self, *args, **kargs):
        self.edje_obj.Edje.signal_emit(str(args[1]), "gsm_change")
        
    def battery_capacity(self, *args, **kargs):
        logger.info("capacity change in launcher")
        self.edje_obj.Edje.signal_emit(str(args[1]), "battery_change")

    def battery_status(self, *args, **kargs):
        logger.info("battery status change in launcher")
        if args[1] == "charging":
            self.edje_obj.Edje.signal_emit(args[1], "battery_status_charging")
        elif args[1] == "discharging":
            bat_value = self.power.get_battery_capacity() 
            self.edje_obj.Edje.signal_emit(str(bat_value), "battery_change")
        elif args[1] == "full":
            #TODO: We may do something here.
            pass
            
    
    def switch_profile(self, *args, **kargs):
        logger.debug("switch_profile called with args: %s and kargs: %s", args, kargs)
        if self.storage.call == None:
            current = self.prefs.get_profile()
            available = self.prefs.get_profiles()
            current_index = available.index(current)
            if len(available)-1 == int(current_index):
                new = available[0]
            else:
                new = available[current_index+1]
            edje_obj = gui.EdjeObject(self.main, self.edje_file, 'profile')    
            edje_obj.Edje.part_text_set('text',new)
            edje_obj.Edje.signal_callback_add('erase', '*', edje_obj.delete)
            edje_obj.Edje.size_set(480, 600)
            edje_obj.show()
            self.prefs.set_profile(new)
            
            logger.info("current: %s new: %s", current, new)
    
    def audio_rotate(self, *args, **kargs):
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
        logger.info("current: %s new: %s", current, self.audio_service.get_speaker_volume())
    
    ##DEBUG FUNCTIONS
    def test(self, emission, source, param):
        logger.info('test called')
        try:
            self.connector.emit('call_active')
        except Exception, e:
            print e
    
            
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))
    
    def general_test(self, *args, **kargs):
        logger.info("general test called with args: %s and kargs: %s", args, kargs)
    
    #write version number on home-screen
    def _get_paroli_version(self):
        try:
            wo = subprocess.Popen(["opkg", "info", "paroli"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error= wo.communicate()
            m = re.search('Version:\s.*[+].*[+](.*)-[r5]',output)
            self.edje_obj.Edje.part_text_set('version',m.group(1))
        except Exception, ex:
            logger.warning("Can't get paroli version : %s", ex)
            self.edje_obj.Edje.part_text_set('version', '????')
    
