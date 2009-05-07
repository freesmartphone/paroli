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

__docformat__ = 'reStructuredText'

import dbus

import tichy
from tichy.tasklet import WaitDBus, WaitDBusName

import logging
logger = logging.getLogger('power')


class DisplayService(tichy.Service):
    """The 'Power' service

    This service can be used to listen to the power signals and control the device power.
    """

    service = 'Display'

    def __init__(self):
        super(DisplayService, self).__init__()

    def init(self):
        """ initialize service and connect to dbus object
        """
        logger.info('display service init')
        self.theme = False
        yield self._connect_dbus()

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        logger.info("connecting to e dbus iface")
        try:
            yield WaitDBusName('org.enlightenment.wm.service', time_out=120, session=True)
            bus = dbus.SessionBus(mainloop=tichy.mainloop.dbus_loop)
            self.obj = bus.get_object('org.enlightenment.wm.service', '/org/enlightenment/wm/RemoteObject')
            self.iface = dbus.Interface(self.obj, 'org.enlightenment.wm.Profile')

            yield WaitDBusName('org.freesmartphone.odeviced', time_out=120, session=False)

            bus2 = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.bobj = bus2.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/Display/gta02_bl')
            self.biface = dbus.Interface(self.bobj, 'org.freesmartphone.Device.Display')

            self.Brightness = tichy.settings.Setting('display', 'Brightness', tichy.Int, value=self.getBrightness(), setter=self.setBrightness, options=[20,40,60,80,100])

        except Exception, e:
            logger.warning("can't use e dbus interface service : %s", e)
        else:
            if not self.theme:
                self.theme = tichy.settings.Setting('display', 'profile', tichy.Text, value=self.get_profile(), setter=self.set_profile, options=self.get_profile_list())

    def getBrightness(self, *args, **kargs):
        return self.biface.GetBrightness()

    @tichy.tasklet.tasklet
    def setBrightness(self, value):
        yield WaitDBus(self.biface.SetBrightness, value)
        yield value
    
    def get_profile(self):
        return self.iface.Get()
    
    def get_profile_list(self):
        profiles = self.iface.List()
        if profiles.count('default') != 0:
            profiles.pop(profiles.index('default'))
        return profiles
    
    @tichy.tasklet.tasklet
    def set_profile(self, profile):
        yield self._connect_dbus()
        yield WaitDBus(self.iface.Set, profile)
