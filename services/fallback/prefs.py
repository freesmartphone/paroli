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

import logging
logger = logging.getLogger('prefs')


class FallbackPrefsSerices(tichy.Service):

    service = 'Prefs'
    name = 'Fallback'

    class Service(item.Item):

        def __init__(self, prefs, name):
            super(FallbackPrefsSerices.Service, self).__init__()
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
                    logger.exception("__getitem__: %s", e)
                    pass
            raise KeyError(name)

        def __setitem__(self, name, value):
            self.attrs[name] = value

    def __init__(self):
        phone = FallbackPrefsSerices.Service(self, 'phone')
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
