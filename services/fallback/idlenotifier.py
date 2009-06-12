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


from tichy.service import Service

import logging
logger = logging.getLogger('services.fallback.idlenotifier')


class FallbackIdleNotifier(Service):

    service = 'IdleNotifier'
    name = 'Fallback'

    def __init__(self):
        super(FallbackIdleNotifier, self).__init__()

    def init(self):
        """Connect to object"""
        logger.info('IdleNotifier test service init')
        yield None

