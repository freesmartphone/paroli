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
import time

class Launcher_App2(tichy.Application):
    name = 'Paroli-Launcher2'
    icon = 'icon.png'
    category = 'hidden' # So that we see the app in the launcher
    
    def run(self, parent=None, standalone=False):
        #logger.info('launcher launching')
        self.ready = 0
        self.standalone = tichy.config.getboolean('standalone',
                                                'activated', False)
        self.advanced = tichy.config.getboolean('advanced-mode',
                                                'activated', False)

        self.settings = tichy.config.getboolean('settings','activated', False)

        self.edje_file = os.path.join(os.path.dirname(__file__),'paroli-launcher.edj')

        self.window = gui.elm_layout_window(self.edje_file, "main", None, None, True)
        self.window.window.elm_obj.on_del_add(self._remove_link_signals)
        self.edje_obj = self.window.main_layout
        if hasattr(self.window.bg_m, "tb"):

            self.window.bg_m.tb.elm_obj.edje_get().signal_emit("hide_clock","*")

        self.active_app = None
        
        if self.advanced == False:
            ##create list of apps from list of registered apps
            apps = ['Paroli-I/O',"Msgs","Paroli-Dialer","Pixels","Paroli-Contacts"]
        else:
            apps = []
            for app in tichy.Application.subclasses:
                if app.category == 'launcher':
                    logger.info("adding - %s to launcher", app.name)
                    apps.append(app)
            
        box = gui.elm_box(self.window.window.elm_obj)
        self.app_objs = {}
        for app in apps:
            link_obj = gui.elm_layout(self.window.window, self.edje_file, 'link')        
            link_obj.elm_obj.size_hint_min_set(400, 60)
            box.elm_obj.pack_end(link_obj.elm_obj)
            link_obj.elm_obj.show()
            link_obj.Edje.part_text_set("texter",app.name)
            link_obj.Edje.part_text_set("testing_textblock","<normal>" + app.name + "</normal><small></small>")
            if hasattr(app,'launcher_info'):
                attr = app.launcher_info
            else:
                attr = 0
            link_obj.elm_obj.show()
            link_obj.add_callback("*", "launch_app", self.launch_app)
            app_obj = [link_obj,attr]
            self.app_objs[app.name] = app_obj
            
        box.elm_obj.show()
        self.edje_obj.elm_obj.content_set("link-box",box.elm_obj)
        self.storage = tichy.Service.get('TeleCom2')
        self.edje_obj.add_callback("*", "launch_app", self.launch_app)
        self.edje_obj.add_callback("*", "embryo", self.embryo)
        self.edje_obj.add_callback("quit_app", "*", self.quit_app)
        ##current hack
        #self.standalone = True
        
        self.msg = tichy.Service.get('Messages')
        if self.msg.ready == False :
            self.msg.connect('ready',self.unblock_screen)
        else:
            self.unblock_screen()
        
        self.busywin = tichy.Service.get('BusyWin')
        
        self.button = tichy.Service.get('Buttons')
        self.aux_btn_profile_conn = self.button.connect('aux_button_pressed', self.switch_profile)
        
        if self.settings:
            self.aux_btn_settings_conn = self.button.connect('aux_button_held', self.open_settings)
          
        self.prefs = tichy.Service.get('Prefs')
        self.audio_service = tichy.Service.get('Audio')
        
        self.ussd = tichy.Service.get('Ussd')
        self.ussd.connect('incoming', self.incoming_ussd)
        self.systime = tichy.Service.get('SysTime')
        self.alarm = tichy.Service.get('Alarm')
        
        self.edje_obj.Edje.signal_callback_add("time_setting_on", "*", self.time_setting_start)
        self.edje_obj.Edje.signal_callback_add("time_setting_off", "*", self.time_setting_stop)
        
        self.ready = 1
        
        yield tichy.Wait(self.window, 'backs')
        self._remove_link_signals()
        self.window.delete()   # Don't forget to close the window
        

    def unblock_screen(self, *args, **kargs):
        logger.info('unblocking screen')
        for app in self.app_objs:
            if self.app_objs[app][1] != 0:
                service = tichy.Service.get(self.app_objs[app][1][0])
                attr = self.app_objs[app][1][1]
                if hasattr(service,attr):
                    connector = getattr(service,attr)
                    connector.connect('modified', self._set_subtext, app)
                    self._set_subtext(connector.value, app)
                
        self.edje_obj.Edje.signal_emit("ready","*")

    def _set_subtext(self, *args, **kargs):
        if args[0] != "0" and args[0] != 0:
          value = args[0]
        else:
          value = ''
        app = args[1]
        edje_obj = self.app_objs[app][0]
        text = '<normal>' + app + '</normal> <small>' + str(value) +'</small>'
        if hasattr(self.storage.window, "window"):
            self.storage.window.window.elm_obj.on_hide_add(self._recreate_link_signals)
            #self.storage.window.window.elm_obj.on_show_add(self._remove_link_signals)
        edje_obj.Edje.part_text_set('testing_textblock',text)

    def launch_app(self, emmision, signal, source):
        """connected to the 'launch_app' edje signal"""
        logger.info("launching %s", str(signal))
        if self.ready != 0:
            self._remove_link_signals()
            self._launch_app(str(signal)).start()

    @tichy.tasklet.tasklet
    def _launch_app(self, name):
        """launch an application, and wait for it to either quit,
        either raise an exception.
        """
        logger.info("launching %s", name)
        # XXX: The launcher shouldn't know anything about this app
        if name == 'Tele' and self.storage.call != None:
            self.storage.window.emit("dehide")
        elif self.active_app == None or self.active_app == "Tele":
            #self.edje_obj.Edje.signal_emit("unready","*")
            app = tichy.Application.find_by_name(name)
            self.active_app = name
            yield app(self.window, standalone=self.standalone)
            self._recreate_link_signals()
            #self.edje_obj.Edje.signal_emit("ready","*")
            self.active_app = None
        else:
            logger.info("blocked %s", name)
    
    def incoming_ussd(self, stuff, msg):
        """connected to the 'incoming_message' edje signal"""
        self._incoming_ussd(str(msg[1])).start()
    
    @tichy.tasklet.tasklet
    def _incoming_ussd(self, msg):
        logger.info('incoming ussd registered')
        yield tichy.Service.get('Dialog').dialog("window", 'Ussd', msg)
    
    def _remove_link_signals(self, *args, **kargs):
        if self.settings:
            logger.info("disconnecting settings")
            self.button.disconnect(self.aux_btn_settings_conn)
        for i in self.app_objs:
            self.app_objs[i][0].Edje.signal_callback_del("*", "launch_app", self.launch_app)
            logger.debug("some callback wasn't found")
    
    def _recreate_link_signals(self, *args, **kargs):
        if self.settings:
            self.aux_btn_settings_conn = self.button.connect('aux_button_held', self.open_settings)
        for i in self.app_objs:
            self.app_objs[i][0].Edje.signal_callback_add("*", "launch_app", self.launch_app)
    
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
        if self.window.bg_m.tb:
            self.window.bg_m.tb.Edje.signal_emit(str(args[1]), "gsm_change")
        
    def battery_capacity(self, *args, **kargs):
        if self.window.bg_m.tb:
            logger.info("capacity change in launcher to %s", str(args[1]))
            self.window.bg_m.tb.Edje.signal_emit(str(args[1]), "battery_change")

    def battery_status(self, *args, **kargs):
        if self.window.bg_m.tb:
            logger.info("battery status change in launcher")
            if args[1] == "charging":
                self.window.bg_m.tb.Edje.signal_emit(args[1], "battery_status_charging")
            elif args[1] == "discharging":
                bat_value = self.power.get_battery_capacity() 
                self.window.bg_m.tb.Edje.signal_emit(str(bat_value), "battery_change")
            elif args[1] == "full":
                #TODO: We may do something here.
                pass

    def time_setting_start(self, emission, signal, source):
        logger.info("time setting called")
        self.button.disconnect(self.aux_btn_profile_conn)
        self.edje_obj.Edje.signal_emit("stop_clock_update", "*")
        self.aux_btn_time_set_conn = self.button.connect('aux_button_pressed', self.adjust_time, emission, 1)
        self.aux_btn_held_conn = self.button.connect('aux_button_held', self.adjust_time, emission, 10)

    def time_setting_stop(self, emission, signal, source):
        edje = emission
        #time = time.localtime()
        #time_text = edje.part_text_get('clock')
        
        time_text = edje.part_text_get('home-clock-hour-digit-1') + edje.part_text_get('home-clock-hour-digit-0') + ":" + edje.part_text_get('home-clock-minute-digit-1') + edje.part_text_get('home-clock-minute-digit-0')
        
        self.button.disconnect(self.aux_btn_time_set_conn)
        self.button.disconnect(self.aux_btn_held_conn)
        numbers = str(time_text).split(':') 
        timepart = time.asctime().split()
        hour_min_sec = timepart[3].split(':') 
        hour_min_sec[0] = str(numbers[0])
        hour_min_sec[1] = numbers[1]
        timepart[3] = hour_min_sec[0] + ":" + hour_min_sec[1] + ":" + hour_min_sec[2]
        time_string = timepart[0] + " " + timepart[1] + " " + timepart[2] \
                      + " " + timepart[3] + " " + timepart[4]
        # Transfer from localtime to GMT time
        new_time = tichy.Time.as_type(time.mktime(time.strptime(time_string)))
        if source == "alarm":
            self.set_alarm(new_time).start() 
            logger.info("Set alarm at %s", new_time)
        elif source == "time":
            logger.info("Set time to %s", new_time)
            self.set_time(new_time).start() 
            
        self.aux_btn_profile_conn = self.button.connect('aux_button_pressed', self.switch_profile)
        self.edje_obj.Edje.signal_emit("start_clock_update", "*")

    @tichy.tasklet.tasklet
    def set_time(self, new_time):
        yield self.systime.set_current_time(new_time) 

    @tichy.tasklet.tasklet
    def set_alarm(self, alarm_time):
        sound_dir = os.path.join(sys.prefix, "share/paroli/data/sounds") 
        alarm_path = os.path.join(sound_dir, "alarm.wav") 
        yield self.alarm.set_alarm(alarm_time, self.alarm_reaction, alarm_path) 

    def alarm_reaction(self, *args, **kargs):
        # Get Alarm file through settings ? 
        # TODO?: Turn on backlight  
        try:
            alarm_file = args[0]
            self.audio_service.play(alarm_file)
        except Exception, ex:
            logger.info( "Play alarm audio %s exception: %s", alarm_file, ex )

    def adjust_time(self, *args, **kargs):
        edje = args[2]
        nmin = args[3]
        time_text = edje.part_text_get('home-clock-hour-digit-1') + edje.part_text_get('home-clock-hour-digit-0') + ":" + edje.part_text_get('home-clock-minute-digit-1') + edje.part_text_get('home-clock-minute-digit-0')
        #time_text = edje.part_text_get('clock')
        numbers = time_text.split(':') 
        hour = int(numbers[0])
        min = int(numbers[1])
        if (min + nmin) < 60:
            min = min + nmin
        else:
            min = min + nmin - 60
            hour = hour + 1
            if hour == 24:
                hour = 0

        if hour < 10:
            hour_digit_1 = "0"
        else:
            hour_digit_1 = str( hour/10 )
        hour_digit_0 = str( hour%10 ) 

        if min < 10:
            min_digit_1 = "0"
        else:
            min_digit_1 = str( min/10 ) 
        min_digit_0 = str( min%10 ) 

        if hour < 10:
            hour = "0" + str(hour)
        if min < 10:
            min = "0" + str(min)
        time_text = str(hour) + ":" + str(min) 
        edje.part_text_set('home-clock-hour-digit-1', hour_digit_1)
        edje.part_text_set('home-clock-hour-digit-0', hour_digit_0)
        edje.part_text_set('home-clock-minute-digit-1', min_digit_1)
        edje.part_text_set('home-clock-minute-digit-0', min_digit_0)
        edje.part_text_set('clock', time_text)
    
    def open_settings(self, *args, **kargs):
        if self.settings == True:
            self.launch_app(None, 'Settings', None)
    
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
            yield self.prefs.set_profile(new)
            
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
    
    ###DEBUG FUNCTIONS
    #def test(self, emission, source, param):
        #logger.info('test called')
        #try:
            #self.connector.emit('call_active')
        #except Exception, e:
            #print e
    
            
    def embryo(self, emission, signal, source):
        logger.info("embryo says:" + str(signal))
    
    def general_test(self, *args, **kargs):
        logger.info("general test called with args: %s and kargs: %s", args, kargs)
    
    ##write version number on home-screen
    #def _get_paroli_version(self):
        #try:
            #wo = subprocess.Popen(["opkg", "info", "paroli"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #output, error= wo.communicate()
            #m = re.search('Version:\s.*[+].*[+](.*)-[r5]',output)
            #self.edje_obj.Edje.part_text_set('version',m.group(1))
        #except Exception, ex:
            #logger.warning("Can't get paroli version : %s", ex)
            #self.edje_obj.Edje.part_text_set('version', '????')
 
##Service to generate and store the loading window
class BusyWin(tichy.Service):
    service = 'BusyWin'

    def __init__(self):
        super(BusyWin, self).__init__()
        self.edje_file = os.path.join(os.path.dirname(__file__), 'paroli-launcher.edj')
        self.win = None

    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
    
    def _do_sth(self):
        pass

    @tichy.tasklet.tasklet
    def create_win(self):
        if self.win == None:
            self.win = gui.elm_window()
            self.layout = gui.elm_layout(self.win, self.edje_file, "busywin")
            self.win.elm_obj.resize_object_add(self.layout.elm_obj)
            self.win.elm_obj.show()
        yield "me"

    def delete_win(self):
        if self.win != None:
            self.win.elm_obj.delete()
            self.win = None

##Service to generate and store the topbar
class TopBar(tichy.Service):
    service = 'TopBar'

    def __init__(self):
        super(TopBar, self).__init__()
        self.edje_file = os.path.join(os.path.dirname(__file__), 'paroli-launcher.edj')
        self.tb_list = []    
    
    @tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('Prefs').wait_initialized()
        yield tichy.Service.get('Power').wait_initialized()
        yield tichy.Service.get('Gprs').wait_initialized()
        self.gsm = tichy.Service.get('GSM')
        self.power = tichy.Service.get('Power')
        self.prefs = tichy.Service.get('Prefs')
        self.gprs = tichy.Service.get('Gprs')
        self.gprs.connect('gprs-status', self.gprs_status)
        self.gsm.connect('network-strength', self.network_strength)
        self.power.connect('battery_capacity', self.battery_capacity)
        self.power.connect('battery_status', self.battery_status)
        self.prefs.connect('profile_changed', self.profile_change)
        yield self._do_sth()
    
    def _do_sth(self):
        pass
    
    def create(self, parent, onclick, standalone=False):
        
        tb = gui.elm_tb(parent, onclick, self.edje_file, standalone)
        
        if hasattr(tb,"tb"):
          self.tb_list.append(tb.tb.elm_obj)
          tb.tb.elm_obj.on_del_add(self.tb_deleted)
          if hasattr(self,"power"):
              try:
                  self.battery_capacity(0,self.power.get_battery_capacity())
              except:
                  pass
          if hasattr(self,"gsm"):
              try:
                  self.network_strength(0,self.gsm.network_strength)
              except:
                  pass
          if hasattr(self,"prefs"):
              try:
                  self.profile_change(0,self.prefs.get_profile())
              except:
                  pass
          #logger.info("topbar created for %s", str(parent))
        return tb

    def tb_deleted(self, *args, **kargs):
        try:
            self.tb_list.remove(args[0])
        except Exception,e:
            dir(e)

    def network_strength(self, *args, **kargs):
        logger.info("network strength %s", str(args[1]))
        for i in self.tb_list:
            i.edje_get().signal_emit(str(args[1]), "gsm_change")
        
    def gprs_status(self, *args, **kargs):
        logger.info("gprs status change in launcher to %s", str(args[1]))
        for i in self.tb_list:
            i.edje_get().signal_emit(str(args[1]), "gprs_status")
        
    def battery_capacity(self, *args, **kargs):
        for i in self.tb_list:
            logger.info("capacity change in launcher to %s", str(args[1]))
            i.edje_get().signal_emit(str(args[1]), "battery_change")

    def profile_change(self, *args, **kargs):
        for i in self.tb_list:
            logger.info("profile display changed to %s", self.prefs.get_profile())
            i.edje_get().signal_emit(self.prefs.get_profile(), "profile-change")

    def volume_change(self, *args, **kargs):
        for i in self.tb_list:
            logger.info("volume display changed to %s", str(args[0]))
            i.edje_get().signal_emit(str(args[0]), "profile-change")

    def battery_status(self, *args, **kargs):
        for i in self.tb_list:
            logger.info("battery status change in launcher")
            if args[1] == "charging":
                i.edje_get().signal_emit(args[1], "battery_status_charging")
            elif args[1] == "discharging":
                bat_value = self.power.get_battery_capacity() 
                i.edje_get().signal_emit(str(bat_value), "battery_change")
            elif args[1] == "full":
                #TODO: We may do something here.
                pass
