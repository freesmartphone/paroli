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
            if self.action is not None:
                self.action(self.args)
            self.action = None
            self.args = None
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
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            alarm_obj = bus.get_object('org.freesmartphone.otimed', 
                          '/org/freesmartphone/Time/Alarm')
            self.alarm = dbus.Interface(alarm_obj, 'org.freesmartphone.Time.Alarm')
            logger.info('Alarm service OK! %s', self.alarm)
        except Exception, e:
            logger.exception("can't use freesmartphone Alarm service : %s", e)

    @tichy.tasklet.tasklet
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
