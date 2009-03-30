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

import dbus

import tichy
from tichy.tasklet import WaitDBus, WaitDBusSignal, WaitFirst, Sleep

import logging
logger = logging.getLogger('SIM')

from contact import Contact
from message import Message
from sms import SMS
from tel_number import TelNumber

class PINError(Exception):
    def __init__(self, pin):
        super(PINError, self).__init__("wrong PIN : %s" % pin)

@tichy.tasklet.tasklet
def retry_on_sim_busy(method, *args):
    """Attempt a dbus call the the framework and retry if we get a sim
    busy error

    Every time we get a SIM busy error, we wait for the ReadyStatus
    signal, or 5 seconds, and we try again.

    If it fails 5 times, we give up and raise an Exception.
    """

    def is_busy_error(ex):
        """Check if an exception is due to a SIM busy error"""
        # There is a little hack to handle cases when the framework
        # fails to send the SIM.NotReady error.
        name = ex.get_dbus_name()
        msg = ex.get_dbus_message()
        return name == 'org.freesmartphone.GSM.SIM.NotReady' or \
            msg.endswith('SIM busy')

    bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
    gsm = bus.get_object('org.freesmartphone.ogsmd',
                         '/org/freesmartphone/GSM/Device',
                         follow_name_owner_changes=True)
    gsm_sim = dbus.Interface(gsm, 'org.freesmartphone.GSM.SIM')

    for i in range(5):
        try:
            ret = yield WaitDBus(method, *args)
            yield ret
        except dbus.exceptions.DBusException, ex:
            if not is_busy_error(ex): # This is an other error
                raise
            logger.info("sim busy, retry in 5 seconds")
            yield WaitFirst(Sleep(5),
                            WaitDBusSignal(gsm_sim, 'ReadyStatus'))
            continue
    else:
        logger.error("SIM always busy")
        raise Exception("SIM too busy")


class SIMContact(Contact):
    storage = 'SIM'

    name = Contact.Field('name', tichy.Text, True)
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
        sim = tichy.Service.get('SIM')
        ret = yield sim.add_contact(contact.name, contact.tel)
        yield ret

    def delete(self):
        sim = tichy.Service.get('SIM')
        yield sim.remove_contact(self)

    @classmethod
    @tichy.tasklet.tasklet
    def load(cls):
        sim = tichy.Service.get('SIM')
        yield sim.wait_initialized()
        ret = yield sim.get_contacts()
        yield ret

class FreeSmartPhoneSim(tichy.Service):

    service = 'SIM'

    PINError = PINError         # Expose the PINError exception

    def __init__(self):
        super(FreeSmartPhoneSim, self).__init__()
        logger.info("connecting to freesmartphone.GSM dbus interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.gsm = bus.get_object('org.freesmartphone.ogsmd',
                                      '/org/freesmartphone/GSM/Device',
                                      follow_name_owner_changes=True)
            self.gsm_sim = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.SIM')

            #for d in self.sim_imsi:
            #print self.sim_info['imsi']
        except Exception, e:
            logger.warning("can't use freesmartphone GSM : %s", e)
            self.gsm = None

        self.indexes = {}       # map sim_index -> contact

    @tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('GSM').wait_initialized()
        #set sim info variable to be used by various apps
        logger.debug("Get sim info")
        self.sim_info = yield WaitDBus(self.gsm_sim.GetSimInfo)

    def get_contacts(self):
        """Return the list of all the contacts in the SIM

        The framework may fail, so we try at least 5 times before we
        give up. We need to remove this if the framework correct this
        problem.
        """
        logger.info("Retrieve Phonebook")
        entries = yield retry_on_sim_busy(self.gsm_sim.RetrievePhonebook,
                                          'contacts')
        logger.info("Got %d contacts" % len(entries))
        logger.debug('get contacts : %s', entries)

        ret = []
        for entry in entries:
            index = int(entry[0])
            name = unicode(entry[1])
            tel = str(entry[2])
            contact = SIMContact(name=name, tel=tel, sim_index=index)
            self.indexes[index] = contact
            ret.append(contact)
        yield ret

    def get_messages(self):
        """Return the list of all the messages in the SIM
        """
        logger.info("Get all the messages from the SIM")
        entries = yield retry_on_sim_busy(self.gsm_sim.RetrieveMessagebook, 'all')

        ret = []
        for entry in entries:
            logger.debug("Got message %s", entry)
            index = entry[0]
            status = str(entry[1]) # "read"|"sent"|"unread"|"unsent"
            peer = str(entry[2])
            text = unicode(entry[3])
            properties = entry[4]
            timestamp = properties.get('timestamp', None)
            # TODO: make the direction arg a boolean
            direction = 'out' if status in ['sent', 'unsent'] else 'in'

            message = SMS(peer, text, direction, status=status,
                          timestamp=timestamp, sim_index=index)
            self.indexes[index] = message
            ret.append(message)

        logger.info("got %d messages", len(ret))
        yield ret

    def add_contact(self, name, number):
        logger.info("add %s : %s into the sim" % (name, number))
        index = self._get_free_index()
        contact = SIMContact(name=name, tel=number, sim_index=index)
        self.indexes[index] = contact
        yield WaitDBus(self.gsm_sim.StoreEntry, 'contacts', index,
                       unicode(name), str(number))
        yield contact

    def _get_free_index(self):
        """return the first found empty index in the sim"""
        # XXX: Need to return an error if we don't have enough place
        # on the sim
        all = self.indexes.keys()
        ret = 1
        while True:
            if not ret in all:
                return ret
            ret += 1

    def remove_contact(self, contact):
        logger.info("remove contact %s from sim", contact.name)
        yield WaitDBus(self.gsm_sim.DeleteEntry, 'contacts',
                       contact.sim_index)

    def remove_message(self, message):
        logger.info("remove message %s from sim", message.sim_index)
        yield WaitDBus(self.gsm_sim.DeleteMessage, int(message.sim_index))


    def send_pin(self, pin):
        logger.info("sending pin")
        try:
            yield WaitDBus(self.gsm_sim.SendAuthCode, pin)
        except dbus.exceptions.DBusException, ex:
            if ex.get_dbus_name() not in ['org.freesmartphone.GSM.SIM.AuthFailed', 'org.freesmartphone.GSM.SIM.InvalidIndex']:
                raise
            raise PINError(pin)


class TestSim(tichy.Service):

    service = 'SIM'
    name = 'Test'

    PINError = PINError

    @tichy.tasklet.tasklet
    def get_contacts(self):
        yield [SIMContact(name='test', tel='099872394', sim_index=0),SIMContact(name='test2', tel='099872394', sim_index=0),SIMContact(name='test3', tel='099872394', sim_index=0),SIMContact(name='test4', tel='099872394', sim_index=0),SIMContact(name='test5', tel='099872394', sim_index=0),SIMContact(name='test6', tel='099872394', sim_index=0),SIMContact(name='test7', tel='099872394', sim_index=0),SIMContact(name='test8', tel='099872394', sim_index=0),SIMContact(name='test9', tel='099872394', sim_index=0),SIMContact(name='test10', tel='099872394', sim_index=0),SIMContact(name='test11', tel='099872394', sim_index=0),SIMContact(name='test12', tel='099872394', sim_index=0),SIMContact(name='test13', tel='099872394', sim_index=0),SIMContact(name='test14', tel='099872394', sim_index=0),SIMContact(name='test15', tel='099872394', sim_index=0),SIMContact(name='test16', tel='099872394', sim_index=0),SIMContact(name='test17', tel='099872394', sim_index=0)]

    @tichy.tasklet.tasklet
    def get_messages(self):
        yield []

    @tichy.tasklet.tasklet
    def add_contact(self, name, number):
        logger.info("add %s : %s into the sim" % (name, number))
        index = 0
        contact = SIMContact(name=name, tel=number, sim_index=index)
        yield contact

    @tichy.tasklet.tasklet
    def remove_contact(self, contact):
        logger.info("remove contact %s from sim", contact.name)
        yield None

    @tichy.tasklet.tasklet
    def init(self):
        self.sim_info = {'imsi':'0123456789012345'}
        yield None

    @tichy.tasklet.tasklet
    def send_pin(self, pin):
        logger.info("sending pin")
        yield None

