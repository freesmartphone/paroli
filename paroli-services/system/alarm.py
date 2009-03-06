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
logger = logging.getLogger('AlarmService')
import dbus
import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange
import time


class Slot(dbus.service.Object):
    """ Alarm notifications will be submitted as dbus method calls, hence 
        alarm receivers need to implement the interface 
        org.freesmartphone.Notification on the root object. Alarm 
        receivers need to be running dbus system services or dbus 
        system-activatable.
    """

    def __init__(self, *args, **kargs):
        super(Slot, self).__init__(*args, **kargs)

    @dbus.service.method("org.freesmartphone.Notification")
    def Alarm(self):
        print "!!!!!!!!!!!!!! Alarm !!!!!!!!!!!!!!!!!!"


class FreeSmartPhoneAlarmService(tichy.Service):
    service = 'Alarm'
  
    def __init__(self):
        super(FreeSmartPhoneAlarmService, self).__init__()
        self.alarm = None

    def init(self):
        """Connect to the freesmartphone DBus object"""
        logger.info('alarm service init')
        self._setup_notification_cb()
        yield self._connect_dbus()

    def _setup_notification_cb(self):
        bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        bus_name = dbus.service.BusName('org.tichy.notification', bus)
        slot = Slot(bus_name, '/')

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.otimed', time_out=None)
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            alarm_obj = bus.get_object('org.freesmartphone.otimed', 
                          '/org/freesmartphone/Time/Alarm')
            self.alarm = dbus.Interface(alarm_obj, 'org.freesmartphone.Time.Alarm')
            logger.info('Alarm service OK!')
        except Exception, e:
            logger.warning("can't use freesmartphone Alarm service : %s", e)

    @tichy.tasklet.tasklet
    def clear_alarm(self):
        try:
            yield WaitDBus( self.alarm.ClearAlarm, 'org.tichy.notification')
        except Exception, ex:
            logger.error("Exception : %s", ex)
            raise

    @tichy.tasklet.tasklet
    def set_alarm(self, ttime):
        try:
            yield WaitDBus(self.alarm.SetAlarm, 'org.tichy.notification', int(ttime.value) )
        except Exception, ex:
            logger.error("Exception : %s", ex)
            raise

