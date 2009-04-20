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
logger = logging.getLogger('usage')


class UsageService(tichy.Service):
    """The 'Usage' service

    This service can be used to listen to the power signals and control the device power.
    """

    service = 'Usage'

    def __init__(self):
        super(UsageService, self).__init__()

    def init(self):
        """ initialize service and connect to dbus object
        """
        logger.info('usage service init')
        yield self._connect_dbus()

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.obj = bus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
            self.iface = dbus.Interface(self.obj, 'org.freesmartphone.Usage')
        except Exception, e:
            logger.warning("can't use fso usage interface service : %s", e)
    
    def occupy_cpu(self):
        logger.info("requesting resource")
        self.iface.RequestResource('CPU')
    
    def release_cpu(self):
        logger.info("releasing resource")
        self.iface.ReleaseResource('CPU')
