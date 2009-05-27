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
logger = logging.getLogger('buttons')


class ButtonTestService(tichy.Service):
    """The 'Button' service

    This service can be used to listen to the input signals form hw buttons
    """

    service = 'Buttons'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(ButtonTestService, self).__init__()
        logger.info('button service init')
        self._connect_dbus().start() 
        self.last = None

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.odeviced', time_out=120)
            logger.info('button service active')
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            input_dev = bus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/Input')
            self.input_intf = dbus.Interface(input_dev, 'org.freesmartphone.Device.Input')
            self.input_intf.connect_to_signal('Event', self._on_button_press)
        except Exception, e:
            logger.warning("can't use freesmartphone button service : %s", e)
            self.input_intf = None
            
    def _on_button_press(self, name, action, seconds):
        logger.debug("button pressed name: %s action: %s seconds %i", name, action, seconds)
        text = tichy.Text()
        if action.lower() == 'pressed':
            self.last = 'pressed'
        elif action.lower() == 'released':
            if self.last == 'pressed':
                text = "%s_button_%s" % (name.lower(), self.last)
            self.last = None
        if action.lower() == 'held':
            self.last = 'held'
            text = "%s_button_%s" % (name.lower(), self.last)
            
        self.emit(text, seconds)

class ButtonService(tichy.Service):
    """The 'Button' service

    This service can be used to listen to the input signals form hw buttons
    """

    service = 'Buttons'
    name = 'Test'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(ButtonService, self).__init__()

    def init(self):
        """Connect to the freesmartphone DBus object"""
        logger.info('IdleNotifier test service init')
        yield None
