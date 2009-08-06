# -*- coding: utf-8 -*-
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
import logging
logger = logging.getLogger('services.fso.usage')

__docformat__ = 'reStructuredText'

import dbus
from tichy import mainloop
from tichy.tasklet import WaitDBus, WaitDBusName, tasklet
from tichy.service import Service


class FSOUsageService(Service):
    """The 'Usage' service

    This service can be used to listen to the power signals and control the device power.
    """

    service = 'Usage'
    name = 'FSO'

    def __init__(self):
        super(FSOUsageService, self).__init__()

    def init(self):
        """ initialize service and connect to dbus object
        """
        logger.info('usage service init')
        self.flags = {}
        yield self._connect_dbus()

    @tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.ousaged', time_out=120)
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            self.obj = bus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
            self.iface = dbus.Interface(self.obj, 'org.freesmartphone.Usage')
        except Exception, e:
            logger.exception("can't use fso usage interface service : %s", e)

    #@tasklet
    def occupy_cpu(self):
        return self.request_resource('CPU')

    #@tasklet
    def release_cpu(self):
        return self.release_resource('CPU')

    @tasklet
    def request_resource(self, resource):
        if hasattr(self, "iface"):
            if resource in self.iface.ListResources():
                logger.debug("requesting resource %s state", resource)
                state = yield WaitDBus(self.iface.GetResourceState,resource)
                if state == False and self.flags[resource] == False:
                    try:
                        logger.debug("requesting resource %s", resource)
                        yield WaitDBus(self.iface.RequestResource,resource)
                        logger.debug("requested resource %s", resource)
                        self.flags[resource] = True
                    except Exception, e:
                        logger.exception ("request_resource %s", e)
                else:
                    logger.debug("not requesting resource %s as it has been already requested", resource)
        yield None

    @tasklet
    def release_resource(self, resource):
        if hasattr(self, "iface"):
            if resource in self.iface.ListResources():
                logger.debug("requesting resource %s state", resource)
                state = yield WaitDBus(self.iface.GetResourceState,resource)
                if state == True and self.flags[resource] == True:
                    try:
                        logger.debug("releasing resource %s", resource)
                        yield WaitDBus(self.iface.ReleaseResource,resource)
                        logger.debug("released resource %s", resource)
                        self.flags[resource] = False
                    except Exception, e:
                        logger.exception ("release_resource %s", e)
                else:
                    logger.debug("not releasing resource %s as it has been already released", resource)
        yield None
