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
logger = logging.getLogger('ussd')


class FSOUssdService(tichy.Service):
    """The 'Button' service

    This service can be used to listen to the input signals form hw buttons
    """

    service = 'Ussd'
    name = 'FSO'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(FSOUssdService, self).__init__()
        self.last = None

    @tichy.tasklet.tasklet
    def init(self):
        logger.info('init')
        yield self._connect_dbus()

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            logger.info('ussd service active')
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            input_dev = bus.get_object('org.freesmartphone.ogsmd',
                                       '/org/freesmartphone/GSM/Device',
                                       follow_name_owner_changes=True)
            self.input_intf = dbus.Interface(input_dev, 'org.freesmartphone.GSM.Network')
            self.input_intf.connect_to_signal('IncomingUssd', self._on_incoming_ussd)
        except Exception, e:
            logger.exception("can't use freesmartphone ussd service : %s", e)
            self.input_intf = None
            
    def _on_incoming_ussd(self, *args, **kargs):
        logger.info('incoming ussd')
        self.emit('incoming', args)

    def send_ussd(self, s):
        if self.input_intf != None:
            try:
                self.input_intf.SendUssdRequest(s)
            except Exception, e:
                logger.exception("error in ussd: %s", e)
        else:
            logger.info("unable to send ussd request")

class FallbackUssdService(tichy.Service):
    """The 'Button' service

    This service can be used to listen to the input signals form hw buttons
    """

    service = 'Ussd'
    name = 'Fallback'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(FallbackUssdService, self).__init__()
        self.last = None

    @tichy.tasklet.tasklet
    def init(self):
        logger.info('init')
        yield None
