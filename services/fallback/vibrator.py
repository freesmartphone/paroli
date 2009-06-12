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
logger = logging.getLogger('services.fallback.vibrator')

__docformat__ = 'reStructuredText'

from tichy.service import Service


class FallbackVibratorService(Service):
    """The 'Vibrator' service

    """

    service = 'Vibrator'
    name = 'Fallback'

    def __init__(self):
        super(FallbackVibratorService, self).__init__()

    def init(self):
        logger.info('vibrator service init')
        yield None

    def stop(self):
        pass

