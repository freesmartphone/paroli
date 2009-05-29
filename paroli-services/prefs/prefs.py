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

import tichy
import tichy.item as item
from tichy.service import Service
from tichy.tasklet import WaitDBusName

import logging
logger = logging.getLogger('prefs')

import dbus

# TODO: make the blocking methods asynchronous

class PrefsService(Service):

    def __getitem__(self, name):
        raise NotImplementedError

    def get_profile(self):
        raise NotImplementedError

    def set_profile(self, name):
        raise NotImplementedError

    def get_profiles(self):
        raise NotImplementedError


class FreeSmartPhonePrefs(tichy.Service):

    service = 'Prefs'

    def __init__(self):
        super(FreeSmartPhonePrefs, self).__init__()

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
            print self.iface.GetValue(key)

    @tichy.tasklet.tasklet
    def init(self):
        logger.info(
            "connecting to freesmartphone.Preferences dbus interface")
        try:
            yield tichy.Service.get('GSM').wait_initialized()
            yield tichy.Service.get('ConfigService').wait_initialized()
            yield WaitDBusName('org.freesmartphone.opreferencesd', time_out=120)
            # We create the dbus interfaces to org.freesmarphone
            self.bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.prefs = self.bus.get_object(
                'org.freesmartphone.opreferencesd',
                '/org/freesmartphone/Preferences')
            self.prefs = dbus.Interface(
                self.prefs,
                'org.freesmartphone.Preferences')
                
            self.config_service = tichy.Service.get("ConfigService")
            self.values = self.config_service.get_items("RingProfile")
            if self.values != None: self.values = dict(self.values)
            
            profile = tichy.settings.Setting('phone', 'profile', tichy.Text, value=self.get_profile(), setter=self.set_profile, options=self.get_profiles(), listenObject=self.prefs, signal="Notify" )
            
            if self.values != None:
                yield self.set_profile(self.values['profile'])
            
        except Exception, e:
            logger.warning("can't use freesmartphone Preferences : %s", e)
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
        try:
            self.config_service.set_item('RingProfile', "profile", name)
        except e:
            logger.info(e)
        yield self.emit('profile_changed')

    def __getitem__(self, name):
        return FreeSmartPhonePrefs.Service(self, name)

class TestPrefs(PrefsService):

    service = 'Prefs'

    class Service(item.Item):

        def __init__(self, prefs, name):
            super(TestPrefs.Service, self).__init__()
            self.prefs = prefs
            self.name = name
            self.attrs = {}

        def __getitem__(self, name):
            for profile in self.prefs.activated_profiles:
                try:
                    value = self.attrs[name][profile]
                    logger.info("Get %s.%s using profile %s",
                                self.name, name, profile)
                    return value
                except KeyError:
                    pass
            raise KeyError(name)

        def __setitem__(self, name, value):
            self.attrs[name] = value

    def __init__(self):
        phone = TestPrefs.Service(self, 'phone')
        phone['ring-tone'] = {'default': 'music1'}
        phone['ring-volume'] = {'default': 10, 'silent': 0}
        self.services = {'phone': phone}
        self.profiles = ['default', 'silent', 'outdoor']
        self.activated_profiles = ['default']

    def __getitem__(self, name):
        return self.services[name]

    def get_profile(self):
        return self.activated_profiles[0]

    def get_profiles(self):
        return self.profiles

    def set_profile(self, name):
        logger.info("Set profile to \"%s\"", name)
        self.activated_profiles = [name, 'default']
