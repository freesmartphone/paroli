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
logger = logging.getLogger('vibrator')


class FallbackVibratorService(tichy.Service):
    """The 'Vibrator' service

    """

    service = 'Vibrator'
    name = 'Fallback'

    def __init__(self):
        super(FallbackVibratorService, self).__init__()

    def init(self):
        logger.info('vibrator service init')
        yield None

class FSOVibratorService(tichy.Service):
    """The 'Vibrator' service

    This service can be used to start or stop the device vibrator if
    it has one.
    """

    service = 'Vibrator'
    name = 'FSO'

    def __init__(self):
        super(FSOVibratorService, self).__init__()
        self.vibrator = None

    def init(self):
        """Connect to the freesmartphone DBus object"""
        try:
            yield WaitDBusName('org.freesmartphone.odeviced')
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            vibrator = bus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/LED/neo1973_vibrator')
            self.vibrator = dbus.Interface(vibrator, 'org.freesmartphone.Device.LED')

        except Exception, e:
            logger.exception("can't use freesmartphone vibrator : %s", e)

    def IncomingSMS(self):
        logger.info("starting vibrator for incoming SMS")
        if not self.vibrator:
            return
        self.vibrator.BlinkSeconds(1, 200, 200)

    def IncomingCall(self):
        logger.info("starting vibrator for incoming call")
        if not self.vibrator:
            return
        self.vibrator.SetBlinking(600, 500)

    def start(self):
        """Start the vibrator"""
        logger.info("start vibrator")
        if not self.vibrator:
            return
        self.vibrator.SetBlinking(300, 700)

    def stop(self):
        """Stop the vibrator"""
        logger.info("stop vibrator")
        if not self.vibrator:
            return
        self.vibrator.SetBrightness(0)
