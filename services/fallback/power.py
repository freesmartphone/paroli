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

from tichy.service import Service

import logging
logger = logging.getLogger('services.fallback.power')


class FallbackPowerService(Service):
    """The 'Power' service

    This service can be used to listen to the power signals and control the device power.
    """

    service = 'Power'
    name = 'Fallback'

    def __init__(self):
        """Connect to object"""
        super(FallbackPowerService, self).__init__()
        self.battery_capacity = 50
        self.battery_status = "fallback"
        self.battery = None

    def init(self):
        logger.info('power service init')
        yield None

