# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2008 Jeremy Chang (jeremy@openmoko.org)
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
logger = logging.getLogger('SysTimeService')
import dbus
import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange
import time
import os

class FreeSmartPhoneTimeService(tichy.Service):
    service = 'SysTime'
  
    def __init__(self):
        super(FreeSmartPhoneTimeService, self).__init__()
        self.rtc = None

    def init(self):
        """Connect to the freesmartphone DBus object"""
        logger.info('systime service init')
        yield self._connect_dbus()

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.odeviced', time_out=120)
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            rtc_obj = bus.get_object('org.freesmartphone.odeviced', 
                          '/org/freesmartphone/Device/RealTimeClock/rtc0')
            self.rtc = dbus.Interface(rtc_obj, 'org.freesmartphone.Device.RealTimeClock')
            
            self.ListLabel = [('title','name'),('value','value')]
            
            self.hour = TimeSetting("hour",3,tichy.List(range(24)), "int")
            
            self.minute =  TimeSetting("minute",4,tichy.List(range(60)), "int")
            
            self.ValueList = tichy.List()
            self.ValueList.append(self.hour)
            self.ValueList.append(self.minute)
            
            self.time_setting = tichy.settings.ListSetting('Time', 'set time', tichy.Text, value="set", setter=self.set_time, options=['set'], model=self.ValueList, ListLabel=self.ListLabel, edje_group="ValueSetting", save_button=True)
            
            self.ValueList.connect('save', self.UpdateSystemTime)
            
        except Exception, e:
            logger.warning("can't use freesmartphone RealTimeClock service : %s", e)

    def test(self, *args, **kargs):
        logger.info("test called")

    @tichy.tasklet.tasklet
    def set_time(self, val):
        yield val

    def UpdateSystemTime(self, *args, **kargs):
        logger.info("time updating called")
        year = time.localtime(self.rtc.GetCurrentTime())[0]
        month = time.localtime(self.rtc.GetCurrentTime())[1]
        day = time.localtime(self.rtc.GetCurrentTime())[2]
        hour = self.hour.value
        minute = self.minute.value
        sec = time.localtime(self.rtc.GetCurrentTime())[5]
        wday = time.localtime(self.rtc.GetCurrentTime())[6]
        yday = time.localtime(self.rtc.GetCurrentTime())[7]
        isdst = time.localtime(self.rtc.GetCurrentTime())[8]
        new_time = time.mktime((year, month, day, hour, minute, sec, wday, yday, isdst))
        ltime = time.asctime((year, month, day, hour, minute, sec, wday, yday, isdst))
        timeSetCmd = 'date -s ' + ltime.split()[3]
        #XXX: here seems a dirty quick way (os.system).
        os.system(timeSetCmd)
        self.rtc.SetCurrentTime(int(new_time))

    def get_current_time(self):
        seconds = self.rtc.GetCurrentTime()
        return tichy.Time.as_type(float(seconds))

    @tichy.tasklet.tasklet
    def set_current_time(self, ttime):
        """  Set time, but not date here. ttime argument is GMT time """
        if not isinstance(ttime, tichy.ttime.Time):
            raise TypeError
        try:
            localtime = ttime.local_repr().split()
            timeSetCmd = 'date -s ' + localtime[3] 
            #XXX: here seems a dirty quick way (os.system).
            os.system(timeSetCmd)
            yield WaitDBus(self.rtc.SetCurrentTime, int(ttime.value) )
        except Exception, ex:
            logger.error("Exception : %s", ex)
            raise

class TimeSetting(tichy.Object):
    def __init__(self, name, rep_part, val_range, type_arg):
        self.service = tichy.Service.get('SysTime')
        self.name = name
        self.value = time.localtime(self.service.rtc.GetCurrentTime())[rep_part]
        self.rep_part = rep_part
        self.val_range = val_range
        self.val_type = type_arg

    def action(self, *args, **kargs):
        pass
        
    def __repr__(self):
        time = time.localtime(self.service.rtc.GetCurrentTime())[self.rep_part]
        return time