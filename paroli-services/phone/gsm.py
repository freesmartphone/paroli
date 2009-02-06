#!/usr/bin/env python
#
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

__docformat__ = 'reStructuredText'

import logging
LOGGER = logging.getLogger('GSM')

import dbus

import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep

from call import Call

# TODO: move this tasklet into paroli-service/phone

class WaitFSOResource(Tasklet):
    """Wait for a FSO resource to be available"""
    def run(self, name, time_out=None):
        yield WaitDBusName('org.freesmartphone.ousaged', time_out=time_out)
        bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        ousage = bus.get_object('org.freesmartphone.ousaged',
                                '/org/freesmartphone/Usage')
        ousage = dbus.Interface(ousage, 'org.freesmartphone.Usage')

        resources = ousage.ListResources()
        if name in resources:
            yield None

        while True:
            r_name, r_status = yield WaitDBusSignal(ousage,
                                                    'ResourceAvailable',
                                                    time_out=time_out)
            if r_name == name:
                yield None



class GSMService(tichy.Service):

    """GSM Service base class

    signals

        provider-modified(string name)
            emitted when the provider name has been  modified

        incoming-call(call)
            indicate an incoming call. Pass the `Call` object
    """

    def __init__(self):
        super(GSMService, self).__init__()
        self.logs = tichy.List()
        self._load_logs()
        self.logs.connect('modified', self._on_logs_modified)

    def init(self, on_step=None):
        """This must return a Tasklet"""
        raise NotImplementedError

    def create_call(self, number, direction):
        """create a new call to a given number"""
        raise NotImplementedError

    def _on_logs_modified(self, logs):
        self._save_logs()

    def _save_logs(self):
        """Save the logs into a file"""
        LOGGER.info("Saving call logs")
        data = [c.to_dict() for c in self.logs]
        tichy.Persistance('calls/logs').save(data)

    def _load_logs(self):
        """Load all the logs"""
        LOGGER.info("Loading call logs")
        data = tichy.Persistance('calls/logs').load()
        if not data:
            return
        # TODO: add some checks for data consistency
        logs = []
        for kargs in data:
            #print kargs
            call = Call(**kargs)
            logs.append(call)
        self.logs[:] = logs


class FreeSmartPhoneGSM(GSMService):
    """GSMService that uses freesmartphone DBUS API"""

    service = 'GSM'

    def __init__(self):
        super(FreeSmartPhoneGSM, self).__init__()
        self.lines = {}
        self.provider = None
        self.network_strength = None

    def get_provider(self):
        """Return the current provider of GSM network

        :Returns: str
        """
        return self.provider

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        LOGGER.info("connecting to DBus")
        yield WaitDBusName('org.freesmartphone.ousaged', time_out=30)
        LOGGER.info("connecting to freesmartphone.GSM dbus interface")
        # We create the dbus interfaces to org.freesmarphone
        self.bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        self.ousage = self.bus.get_object('org.freesmartphone.ousaged',
                                          '/org/freesmartphone/Usage')
        self.ousage = dbus.Interface(self.ousage, 'org.freesmartphone.Usage')
        self.gsm = self.bus.get_object('org.freesmartphone.ogsmd',
                                       '/org/freesmartphone/GSM/Device')
        self.gsm_device = dbus.Interface(self.gsm,
                                         'org.freesmartphone.GSM.Device')
        self.gsm_network = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.Network')
        self.gsm_call = dbus.Interface(self.gsm,
                                       'org.freesmartphone.GSM.Call')
        self.gsm_network.connect_to_signal("Status", self._on_status)
        self.gsm_call.connect_to_signal("CallStatus",
                                        self._on_call_status)


    def init(self, on_step=None):
        """Tasklet that registers on the network

        :Parameters:

            on_step : callback function | None
                a callback function that take a string argument that
                will be called at every step of the registration
                procedure
        """

        def default_on_step(msg):
            pass
        on_step = on_step or default_on_step

        try:
            yield self._connect_dbus()
            LOGGER.info("Request the GSM resource")
            on_step("Request the GSM resource")
            yield WaitFSOResource('GSM', time_out=30)
            yield WaitDBus(self.ousage.RequestResource, 'GSM')
            yield self._turn_on(on_step)
            on_step("Register on the network")
            LOGGER.info("register on the network")
            yield WaitDBus(self.gsm_network.Register)
            yield tichy.Wait(self, 'provider-modified')
        except Exception, ex:
            LOGGER.error("Error : %s", ex)
            raise

    def _turn_on(self, on_step):
        LOGGER.info("Check antenna power")
        power = yield WaitDBus(self.gsm_device.GetAntennaPower)
        LOGGER.info("antenna power is %d", power)
        if power:
            yield None
        LOGGER.info("turn on antenna power")
        on_step("Turn on antenna power")
        for i in range(3):
            try:
                yield WaitDBus(self.gsm_device.SetAntennaPower, True)
            except dbus.exceptions.DBusException, ex:
                if ex.get_dbus_name() != \
                        'org.freesmartphone.GSM.SIM.AuthFailed':
                    raise
                # We ask for the PIN
                yield self._ask_pin()

    def _ask_pin(self):
        #window = tichy.Service("WindowsManager").get_app_parent()
        window = None
        editor = tichy.Service('TelePIN')
        pin = yield editor.edit(window, name="Enter PIN",
                                input_method='number')
        yield tichy.Service('SIM').send_pin(pin)

    def _on_call_status(self, call_id, status, properties):
        LOGGER.info("call status %s %s %s", id, status, properties)
        call_id = int(call_id)
        status = str(status)

        if status == 'incoming':
            LOGGER.info("incoming call")
            # XXX: should use an assert, but it doesn't work on neo :O
            if call_id in self.lines:
                LOGGER.warning("WARNING : line already present %s %s",
                               call_id, self.lines)
                # XXX : I just ignore the message, because the
                # framework send it twice !! Bug in the framework ?
                return
                # raise Exception("call already present")
            peer_number = str(properties.get('peer', "Unknown"))

            call = self.create_call(peer_number, direction='in')
            call.__id = call_id
            self.lines[call_id] = call

            assert call_id in self.lines
            self.emit('incoming-call', call)

        elif status == 'outgoing':
            self.lines[call_id].outgoing()
        elif status == 'active':
            self.lines[call_id].active()
        elif status == 'release':
            self.lines[call_id].released()
            del self.lines[call_id]
        else:
            LOGGER.warning("Unknown status : %s", status)

    def _on_status(self, status):
        LOGGER.debug("status %s", status)
        if 'provider' in status:
            provider = str(status['provider'])
            if provider != self.provider:
                self.provider = provider
                self.emit('provider-modified', self.provider)
        if 'strength' in status:
            strength = int(status['strength'])
            if strength != self.network_strength:
                self.network_strength = strength
                self.emit('network-strength', self.network_strength)

    def create_call(self, number, direction='out'):
        """create a new Call

        :Parameters:

            number : `TelNumber` | str
                The peer number of the call

            direction : str
                Indicate the direction of the call. Can be 'in' or
                'out'
        """
        LOGGER.info("create call %s" % number)
        call = Call(number, direction=direction)
        self.logs.insert(0, call)
        return call

    @tichy.tasklet.tasklet
    def _initiate(self, call):
        """Initiate a given call
        """
        number = str(call.number)
        LOGGER.info("initiate call to %s", number)
        call_id = yield WaitDBus(self.gsm_call.Initiate, number, "voice")
        call_id = int(call_id)
        LOGGER.info("call id : %d", call_id)
        self.lines[call_id] = call
        # TODO: mabe not good idea to store this in the call itself,
        #       beside, it makes pylint upset.
        call.__id = call_id

    @tichy.tasklet.tasklet
    def _activate(self, call):
        LOGGER.info("activate call %s", str(call.number))
        yield WaitDBus(self.gsm_call.Activate, call.__id)

    @tichy.tasklet.tasklet
    def _release(self, call):
        LOGGER.info("release call %s", str(call.number))
        yield WaitDBus(self.gsm_call.Release, call.__id)


class TestGsm(GSMService):
    """Fake service that can be used to test without GSM drivers
    """

    service = 'GSM'
    name = 'Test'

    def __init__(self):
        super(TestGsm, self).__init__()
        self.logs.append(Call('0478657392'))

    def init(self, on_step=None):
        """register on the network"""

        def default_on_step(msg):
            pass
        on_step = on_step or default_on_step

        LOGGER.info("Turn on antenna power")
        on_step("Turn on antenna power")
        LOGGER.info("Register on the network")
        on_step("Register on the network")
        self.emit('provider-modified', "Charlie Telecom")
        yield None

    def create_call(self, number, direction='out'):
        call = Call(number, direction=direction)
        self.logs.insert(0, call)
        return call

    @tichy.tasklet.tasklet
    def _initiate(self, call):
        yield Sleep(2)
        call.active()

    @tichy.tasklet.tasklet
    def _release(self, call):
        call.released()
        yield None

    def get_provider(self):
        return 'Charlie Telecom'
