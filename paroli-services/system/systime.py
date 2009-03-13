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
        except Exception, e:
            logger.warning("can't use freesmartphone RealTimeClock service : %s", e)

    def get_current_time(self):
        seconds = self.rtc.GetCurrentTime()
        return tichy.Time.as_type(float(seconds))

    @tichy.tasklet.tasklet
    def set_current_time(self, ttime):
        """  Set time, but not date here. ttime argument is GMT time """
        if not isinstance(ttime, tichy.Time): 
            raise TypeError
        try:
            localtime = ttime.local_repr().split()
            timeSetCmd = 'date -s ' + localtime[3] 
            #XXX: here seems a dirty quick way (os.system).
            os.system(timeSetCmd)
            yield WaitDBus(self.rtc.SetCurrentTime, str(ttime.value) )
        except Exception, ex:
            logger.error("Exception : %s", ex)
            raise

