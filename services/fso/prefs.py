# -*- coding: utf-8 -*-
#    Tichy
#
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#
#    This file is part of Tichy.
#
#    Tichy is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tichy is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Tichy.  If not, see <http://www.gnu.org/licenses/>.

import dbus

import tichy
from tichy.tasklet import WaitDBusName

import logging
logger = logging.getLogger('prefs')


# TODO: make the blocking methods asynchronous
class FSOPrefsServices(tichy.Service):

    service = 'Prefs'
    name = 'FSO'

    def __init__(self):
        super(FSOPrefsServices, self).__init__()

    class Service(object):

        def __init__(self, prefs, name):
            self.prefs = prefs
            self.name = name
            # We retrieve the dbus object associated with this service
            path = prefs.prefs.GetService(name)
            self.service = prefs.bus.get_object(
                'org.freesmartphone.opreferencesd', path)
      
            self.iface = dbus.Interface(self.service, 'org.freesmartphone.Preferences.Service')

        def __getitem__(self, key):
            return self.iface.GetValue(key)

        def __setitem__(self, key, value):
            self.iface.SetValue(key, value)
            logger.debug('__setitem__ %s', self.iface.GetValue(key))

    @tichy.tasklet.tasklet
    def init(self):
        logger.info(
            "connecting to freesmartphone.Preferences dbus interface")
        try:
            yield WaitDBusName('org.freesmartphone.opreferencesd', time_out=120)
            # We create the dbus interfaces to org.freesmarphone
            self.bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.prefs = self.bus.get_object(
                'org.freesmartphone.opreferencesd',
                '/org/freesmartphone/Preferences')
            self.prefs = dbus.Interface(
                self.prefs,
                'org.freesmartphone.Preferences')
                
            profile = tichy.settings.Setting('phone', 'profile', tichy.Text, value=self.get_profile(), setter=self.set_profile, options=self.get_profiles(), listenObject=self.prefs, signal="Notify" )
        except Exception, e:
            logger.exception("can't use freesmartphone Preferences : %s", e)
            self.prefs = None

    def get_profile(self):
        ret = self.prefs.GetProfile()
        return str(ret)

    def get_profiles(self):
        ret = self.prefs.GetProfiles()
        return [str(x) for x in ret]
    
    @tichy.tasklet.tasklet
    def set_profile(self, name):
        self.prefs.SetProfile(name)
        yield self.emit('profile_changed')

    def __getitem__(self, name):
        return FSOPrefsServices.Service(self, name)

