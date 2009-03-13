#    Paroli
#
#    copyright 2008 Mirko Lindner (mirko@openmoko.org)
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

__docformat__ = 'reStructuredText'

import dbus

import tichy
from tichy.tasklet import WaitDBus, WaitDBusName

import logging
logger = logging.getLogger('power')


class PowerService(tichy.Service):
    """The 'Power' service

    This service can be used to listen to the power signals and control the device power.
    """

    service = 'Power'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(PowerService, self).__init__()
        self.battery_capacity = 50
        self.battery_status = ""
        self.battery = None

    def init(self):
        logger.info('power service init')
        yield self._connect_dbus()

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.odeviced', time_out=120)
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            battery = bus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/PowerSupply/battery')
            self.battery = dbus.Interface(battery, 'org.freesmartphone.Device.PowerSupply')
            self.battery.connect_to_signal('Capacity', self._on_capacity_change)
            self.battery.connect_to_signal('PowerStatus', self._on_status_change)
            self._on_capacity_change(self.battery.GetCapacity()) 
        except Exception, e:
            logger.warning("can't use freesmartphone power service : %s", e)
        else:
            self._on_capacity_change(self.battery.GetCapacity())
            self.battery_capacity = 0
            
    def _on_capacity_change(self, percent):
        logger.info("capacity changed to %i", percent)
        self.battery_capacity = percent
        self.emit('battery_capacity', self.battery_capacity)

    def _on_status_change(self, status):
        self.battery_status = status
        self.emit('battery_status', self.battery_status)

    def get_battery_capacity(self):
        bat_value = self.battery.GetCapacity()
        return bat_value

    #def start(self):
        #"""Start the vibrator"""
        #logger.info("start vibrator")
        #if not self.vibrator:
            #return
        #self.vibrator.SetBlinking(300, 700)

    #def stop(self):
        #"""Stop the vibrator"""
        #logger.info("stop vibrator")
        #if not self.vibrator:
            #return
        #self.vibrator.SetBrightness(0)
