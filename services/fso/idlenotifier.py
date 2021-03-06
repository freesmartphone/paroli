# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2009 Mirko Lindner (mirko@openmoko.org)
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
logger = logging.getLogger('services.fso.idlenotifier')

import dbus
from tichy.int import Int
from tichy.tasklet import WaitDBusName, tasklet
from tichy.settings import Setting
from tichy.service import Service
from tichy import mainloop


class FSOIdleNotifierService(Service):

    service = 'IdleNotifier'
    name = 'FSO'

    def __init__(self):
        super(FSOIdleNotifierService, self).__init__()

    def init(self):
        """Connect to the freesmartphone DBus object"""
        logger.info('IdleNotifier service init')
        yield self._connect_dbus()

    @tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.odeviced', time_out=120)
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            obj = bus.get_object('org.freesmartphone.odeviced',
                          '/org/freesmartphone/Device/IdleNotifier/0')
            self.iface = dbus.Interface(obj, 'org.freesmartphone.Device.IdleNotifier')
            suspend_setting = Setting('phone', 'suspend-time', Int, value=self.get_timeout('suspend'), setter=self.set_suspend, options=[-1, 20, 30, 60])

            #self.iface.connect_to_signal("State", self.dim)

        except Exception, e:
            logger.exception("can't use freesmartphone IdleNotifier service : %s", e)

    def dim(self, *args, **kargs):
        logger.debug('dim %s', args)

    def get_timeout(self, state):
        timeouts = self.iface.GetTimeouts()
        suspend = timeouts[state]
        return suspend

    @tasklet
    def set_suspend(self, time):
        yield self.iface.SetTimeout('suspend', int(time))

    @tasklet
    def set_idle_dim(self, time):
        yield self.iface.SetTimeout('idle_dim', int(time))
