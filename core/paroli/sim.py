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
import logging
logger = logging.getLogger('core.paroli.sim')

from tichy.persistance import Persistance
from tichy.int import Int
from tichy.item import Item
from tichy.list import List
from tichy.tasklet import tasklet
from tichy.service import Service
from tichy.ttime import Time
from tichy.text import Text
from paroli.tel_number import TelNumber
from contact import Contact


class PINError(Exception):
    def __init__(self, pin):
        super(PINError, self).__init__("wrong PIN : %s" % pin)


class Call(Item):
    """Class that represents a voice call"""

    def __init__(self, number, direction='out', timestamp=None,
                 status='inactive'):
        """Create a new call object

        :Parameters:

            number : `tichy.TelNumber` | str
                The number of the peer

            direction : str
               'out' for outgoing call, 'in' for incoming call

            timestamp
                the time at which we created the call. If set to None
                we use the current time

            status : str | None
                Can be any of :
                    - 'inactive'
                    - 'incoming'
                    - 'outoing'
                    - 'activating'
                    - 'active'
                    - 'releasing'
                    - 'released'
                (default to 'inactive')

            checked : boolean
                Actaully it's used only for "missed" calls

        Signals

            initiating
                The call is being initiated

            outgoing
                The call is outgoing

            activated
                The call has been activated

            releasing
                The call is being released

            released
                The call has been released
        """
        self.number = TelNumber.as_type(number)
        self.direction = direction
        self.timestamp = Time.as_type(timestamp)
        self.status = status
        self.missed = False
        self.checked = True

    def get_text(self):
        return self.number.get_text()

    @property
    def description(self):
        if (self.missed):
            return "Missed" + " at " + unicode(self.timestamp.simple_repr())
        else:
            if (self.direction == "out"):
                return "Outgoing" + " at " + unicode(self.timestamp.simple_repr())
            elif (self.direction == "in"):
                return "Incoming" + " at " + unicode(self.timestamp.simple_repr())

    @tasklet
    def initiate(self):
        """Initiate the call

        This will try to get the 'GSM' service and call its 'initiate'
        method.
        """
        logger.info("initiate call")
        gsm_service = Service.get('GSM')
        yield gsm_service._initiate(self)
        self.status = 'initiating'
        self.emit(self.status)

    @tasklet
    def release(self):
        logger.info("release call")
        if self.status in ['releasing', 'released']:
            return
        gsm_service = Service.get('GSM')
        try:
            yield gsm_service._release(self)
        except Exception, e:
            logger.exception('released')
            #XXX should the call get a
            #logger.debug('call error')
            self.emit("error", e)
            self.status = 'released'
        else:
            self.status = 'releasing'
        self.emit(self.status)

    @tasklet
    def activate(self):
        """Activate the call"""
        logger.info("activate call")
        gsm_service = Service.get('GSM')
        yield gsm_service._activate(self)
        self.status = 'activating'
        self.emit(self.status)

    # XXX: those methods should be tasklets

    def mute_ringtone(self):
        """mute the call ringtone if it is ringing"""
        logger.info("mute ring tone")
        Service.get('Audio').stop_all_sounds()
        Service.get('Vibrator').stop()

    def mute(self):
        """Mute an active call"""
        logger.info("mute call")
        Service.get('Audio').set_mic_status(False)

    def unmute(self):
        """Un Mute an active call"""
        logger.info("mute call")
        Service.get('Audio').set_mic_status(True)

    def mute_toggle(self):
        logger.info("mute call toggle")
        if Service.get('Audio').get_mic_status() == 1:
            Service.get('Audio').set_mic_status(0)
        else:
            Service.get('Audio').set_mic_status(1)

    @tasklet
    def send_dtmf(self, code):
        """Send one or more Dual Tone Multiple Frequency (DTMF)
        signals during an active call"""
        gsm_service = Service.get('GSM')
        if self.status != 'active':
            raise Exception("Can't send DMTF to a call that is not active")
        yield gsm_service._send_dtmf(self, code)

    # Those methods are only supposed to be called by the gsm service

    def _outgoing(self):
        self.status = 'outgoing'
        self.emit('outgoing')

    def _active(self):
        self.status = 'active'
        self.emit('activated')

    def _released(self):
        if self.status == 'incoming':
            self.missed = True
            self.checked = False
        self.status = 'released'
        self.emit('released')

    def _incoming(self):
        self.status = 'incoming'
        self.emit('incoming')

    def check(self):
        self.checked = True

    # TODO: In the long run we should really use a system similar to
    #       PEAK, where we can define all the Items attributes and
    #       every atomic value has a save and load method.  So that we
    #       don't have to create all those `to_dict` and `from_dict`
    #       methods. We could use a Struct Item for this kind of
    #       things.

    def to_dict(self):
        """return all the attributes in a python dict"""
        return {'number': str(self.number),
                'status': str(self.status),
                'direction': self.direction,
                'timestamp': str(self.timestamp)}

    @classmethod
    def from_dict(self, kargs):
        """return a new Call object from a dictionary

        This should be compatible with the `to_dict` method
        """
        number = kargs['number']
        status = kargs['status']
        direction = kargs['direction']
        timestamp = kargs['timestamp']
        return Call(number, direction=direction, timestamp=timestamp,
                    status=status)

class SIMContact(Contact):
    storage = 'SIM'

    name = Contact.Field('name', Text, True)
    tel = Contact.Field('tel', TelNumber)
    fields = [name, tel]

    def __init__(self, sim_index=None, **kargs):
        super(SIMContact, self).__init__(sim_index=sim_index, **kargs)
        self.sim_index = sim_index
        self.icon = 'pics/sim.png'

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        assert not isinstance(contact, SIMContact)
        sim = Service.get('SIM')
        ret = yield sim.add_contact(contact.name, contact.tel)
        yield ret

    def delete(self):
        sim = Service.get('SIM')
        yield sim.remove_contact(self)

    @classmethod
    @tasklet
    def load(cls):
        sim = Service.get('SIM')
        yield sim.wait_initialized()
        ret = yield sim.get_contacts()
        yield ret

class GSMService(Service):

    """GSM Service base class

    signals

        provider-modified(string name)
            emitted when the provider name has been  modified

        incoming-call(call)
            indicate an incoming call. Pass the `Call` object
    """

    def __init__(self):
        super(GSMService, self).__init__()
        self.logs = List()
        self.missed_call_count = Int(0)
        self.logs.connect('modified', self._on_logs_modified)
        self._load_logs()

    def init(self):
        """This must return a Tasklet"""
        raise NotImplementedError

    def create_call(self, number, direction):
        """create a new call to a given number"""
        raise NotImplementedError

    def _on_logs_modified(self, logs):
        self._save_logs()
        self.update_missed_call_count()

    def _save_logs(self):
        """Save the logs into a file"""
        logger.info("Saving call logs")
        data = [c.to_dict() for c in self.logs[:29]]
        Persistance('calls/logs').save(data)

    def _load_logs(self):
        """Load all the logs"""
        logger.info("Loading call logs")
        data = Persistance('calls/logs').load()
        if not data:
            return
        # TODO: add some checks for data consistency
        logs = []
        for kargs in data:
            logger.debug('_load_logs %s', kargs)
            call = Call(**kargs)
            logs.append(call)
        self.logs[:] = logs

    @tasklet
    def _ask_pin(self):
        #window = tichy.Service.get("WindowsManager").get_app_parent()
        window = None
        editor = Service.get('TelePIN2')
        sim = Service.get('SIM')

        status = sim.GetAuthStatus()
        logger.info("asking for: %s", status)
        
        if status in ["SIM PIN", "SIM PIN2"]:
            pin_status = True
            ranger = 3
        else:
            pin_status = False
            ranger = 9

        for i in range(ranger):
            pin = yield editor.edit(window, name="Enter " + str(status),
                                    input_method='number')
            try:
                if pin_status:
                    yield sim.send_pin(pin)
                    break
                else:
                    new_pin_one = yield editor.edit(window, name="Enter new PIN",
                                    input_method='number')
                    new_pin_two = yield editor.edit(window, name="Enter new PIN again",
                                    input_method='number')                
                    if new_pin_one == new_pin_two:
                        sim.Unlock(pin, new_pin_one)
                        break
                    else:
                        text = "The two PINs entered don't match.<br/>Setting PIN to 0000. Please change it later."
                        dialog = Service.get("Dialog")
                        yield dialog.dialog(None,  "Error",  text)
                        sim.Unlock(pin, "0000")
                        break
            except sim.PINError:
                dialog = Service.get("Dialog")
                if status != "SIM PIN" and status != "SIM PIN2":
                    number = 9 - i
                else:
                    number = 2 - i
                text = "Incorrect " + str(status) + " " + str(number)  + " trials left"
                yield dialog.dialog(None,  "Error",  text)
                if i == ranger: # after ranger times we give up - depends on PIN/PUK
                    raise
                logger.exception("pin wrong : %s", pin)

    def update_missed_call_count(self):
        count = 0
        for call in self.logs:
            if call.missed and ( not call.checked ):
                count = count + 1
        self.missed_call_count.value = count

    def check_all_missed_call_logs(self):
        for call in self.logs:
            if call.missed and ( not call.checked ):
                call.check()
        self.missed_call_count.value = 0
