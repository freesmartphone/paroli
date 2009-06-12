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
logger = logging.getLogger('services.fso.alarm')

import dbus
import time
from tichy.tasklet import WaitDBus, WaitDBusName, tasklet
from tichy.object import Object
from tichy.list import List
from tichy.text import Text
from tichy.service import Service
from tichy import mainloop
from tichy.settings import ListSetting

class FSOSlot(dbus.service.Object):
    """ Alarm notifications will be submitted as dbus method calls, hence
        alarm receivers need to implement the interface
        org.freesmartphone.Notification on the root object. Alarm
        receivers need to be running dbus system services or dbus
        system-activatable.
    """

    def __init__(self, *args, **kargs):
        super(FSOSlot, self).__init__(*args, **kargs)
        self.action = None
        self.args = None

    def set_action(self, func, args):
        logger.info("action set to %s with %s", func, args)
        self.action = func
        self.args = args

    @dbus.service.method("org.freesmartphone.Notification")
    def Alarm(self):
        logger.info( "!!!!!!!!!!!!!! Alarm !!!!!!!!!!!!!!!!!!" )
        try:
            #if self.action is not None:
                #self.action(self.args)
            #self.action = None
            #self.args = None
            self.AlarmService = Service.get("Alarm")
            self.AlarmService.ring()

        except Exception, ex:
            logger.exception( "Alarm except %s", ex )


class FSOAlarmService(Service):

    service = 'Alarm'
    name = 'FSO'

    def __init__(self):
        super(FSOAlarmService, self).__init__()
        self.alarm = None

    def init(self):
        """Connect to the freesmartphone DBus object"""
        logger.info('alarm service init')
        self._setup_notification_cb()
        yield self._connect_dbus()

    def _setup_notification_cb(self):
        bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
        bus_name = dbus.service.BusName('org.tichy.notification', bus)
        self.slot = FSOSlot(bus_name, '/')

    @tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.otimed', time_out=120)
            yield Service.get('SysTime').wait_initialized()

            self.rtc = Service.get("SysTime").rtc

            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            alarm_obj = bus.get_object('org.freesmartphone.otimed',
                          '/org/freesmartphone/Time/Alarm')
            self.alarm = dbus.Interface(alarm_obj, 'org.freesmartphone.Time.Alarm')

            self.ListLabel = [('title','name'),('value','value')]

            self.hour = TimeSetting("hour",3,List(range(24)), "int")

            self.minute =  TimeSetting("minute",4,List(range(60)), "int")

            self.AlarmList = List()
            self.AlarmList.append(self.hour)
            self.AlarmList.append(self.minute)

            self.alarm_setting = ListSetting('Time', 'set alarm', Text, value="set", setter=self.SetAlarm, options=['set'], model=self.AlarmList, ListLabel=self.ListLabel, edje_group="ValueSetting", save_button=True)

            self.AlarmList.connect('save', self.UpdateAlarmTime)

        except Exception, e:
            logger.exception("can't use freesmartphone Alarm service : %s", e)

    @tasklet
    def SetAlarm(self, val):
        yield val

    def UpdateAlarmTime(self, *args, **kargs):
        logger.info("alarm updating called")
        now = self.rtc.GetCurrentTime()
        year = time.localtime(self.rtc.GetCurrentTime())[0]
        month = time.localtime(self.rtc.GetCurrentTime())[1]
        day = time.localtime(self.rtc.GetCurrentTime())[2]
        hour = self.hour.value
        minute = self.minute.value
        sec = 0
        wday = time.localtime(self.rtc.GetCurrentTime())[6]
        yday = time.localtime(self.rtc.GetCurrentTime())[7]
        isdst = time.localtime(self.rtc.GetCurrentTime())[8]

        new_time = time.mktime((year, month, day, hour, minute, sec, wday, yday, isdst))

        if int(now) - int(new_time) > 0:
            alarm = time.mktime((year, month, day+1, hour, minute, sec, wday+1, yday+1, isdst))
        else:
            alarm = new_time

        yield WaitDBus(self.alarm.SetAlarm, 'org.tichy.notification', int(alarm) )


    @tasklet
    def clear_alarm(self):
        try:
            yield WaitDBus( self.alarm.ClearAlarm, 'org.tichy.notification')
        except Exception, ex:
            logger.exception("Exception : %s", ex)
            raise

    @tasklet
    def set_alarm(self, ttime, func, *args):
        try:
            self.slot.set_action(func, *args)
            logger.debug('set_action %s %s', func, args, )
            yield WaitDBus(self.alarm.SetAlarm, 'org.tichy.notification', int(ttime.value) )
        except Exception, ex:
            logger.exception("Exception : %s", ex)
            raise

    def ring(self, *args):
        logger.info("ring ring")

class TimeSetting(Object):
    def __init__(self, name, rep_part, val_range, type_arg):
        self.service = Service.get('SysTime')
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

