#
#    Paroli
#
#    copyright 2008 openmoko
#
#    This file is part of Paroli
#
#    Tichy is free software: you can redistribute it and/or modify it
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

import logging
LOGGER = logging.getLogger('keep_alive')

from subprocess import call, PIPE
import os

import tichy

class KeepAliveService(tichy.Service):
    """This service can be used to make sure that a given daemon is
    alive and restart it if it is dead.

    The implementation is pretty bad, using subprocess to directly
    call the pgrep unix command.

    (Is there a better way to do that ?)
    """
    service = 'KeepAlive'

    def _restart(self, daemon):
        init_script = "/etc/init.d/%s" % daemon
        LOGGER.error("restarting %s", daemon)
        call([init_script, 'start'], stdout=PIPE)

    @tichy.tasklet.tasklet
    def keep_alive(self, daemon, period=5):
        """Tasklet that will ensure that the daemon stay alive"""
        # We make sure that the init.d script is present
        init_script = "/etc/init.d/%s" % daemon
        if not os.path.exists(init_script):
            LOGGER.error('cannot find init script "%s"', init_script)
            raise Exception('file "%s" not present' % init_script)
        while True:
            is_alive = call(['pgrep', '-f', daemon], stdout=PIPE) == 0
            if not is_alive:
                LOGGER.error("daemon %s is dead", daemon)
                self._restart(daemon)
            yield tichy.tasklet.Sleep(period)

    @tichy.tasklet.tasklet
    def keep_dbus_service_alive(self, name, daemon):
        """Same thing but monitoring a daemon that expose a dbus service

        It works by monitoring the NameOwnerChanged signal from
        org.freedesktop.Dbus.
        """
        import dbus
        dbus.set_default_main_loop
        bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        bus_obj = bus.get_object('org.freedesktop.DBus',
                                 '/org/freedesktop/DBus')
        bus_obj_iface = dbus.proxies.Interface(bus_obj,
                                               'org.freedesktop.DBus')
        all_bus_names = bus_obj_iface.ListNames()
        # XXX: maybe the service is not even started yet
        while True:
            var = yield tichy.tasklet.WaitDBusSignal(bus_obj_iface, 'NameOwnerChanged')
            if var[0] == name:
                LOGGER.error("get NameOwnerChanged for dbus name %s", name)
                self._restart(daemon)
