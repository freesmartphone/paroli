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
from tichy.tasklet import WaitDBus

import logging
logger = logging.getLogger('SIM')

from contact import Contact
from message import Message
from tel_number import TelNumber

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
        sim = tichy.Service('SIM')
        ret = yield sim.add_contact(contact.name, contact.tel)
        yield ret

    def delete(self):
        sim = tichy.Service('SIM')
        yield sim.remove_contact(self)

    @classmethod
    @tichy.tasklet.tasklet
    def load(cls):
        sim = tichy.Service('SIM')
        ret = yield sim.get_contacts()
        yield ret

class SIMMessage(Message):

    storage = 'SIM'

    #peer = TelNumber.as_type(peer)
    #text = tichy.Text.as_type(text)
    #timestamp = tichy.Time.as_time(timestamp)
    #direction = tichy.Text.as_type(text)
    #status = tichy.Text.as_type(text)
    #fields = [name, text, timestamp, direction, status]

    def __init__(self, sim_index=None, **kargs):
        super(SIMMessage, self).__init__(sim_index=sim_index, **kargs)
        self.sim_index = sim_index
        #self.icon = 'pics/sim.png'

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        assert not isinstance(message, PhoneMessage)
        ret = PhoneMessage(peer=message.peer,text=message.text,timestamp=message.timestamp,direction=message.direction,status=message.status)
        yield ret

    #def delete(self):
        #sim = tichy.Service('SIM')
        #yield sim.remove_contact(self)

    @classmethod
    @tichy.tasklet.tasklet
    def load(cls):
        sim = tichy.Service('SIM')
        ret = yield sim.get_messages()
        yield ret

class FreeSmartPhoneSim(tichy.Service):

    service = 'SIM'

    def __init__(self):
        logger.info("connecting to freesmartphone.GSM dbus interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.gsm = bus.get_object('org.freesmartphone.ogsmd',
                                      '/org/freesmartphone/GSM/Device')
            self.gsm_sim = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.SIM')

            #for d in self.sim_imsi:
            #print self.sim_info['imsi']
        except Exception, e:
            logger.warning("can't use freesmartphone GSM : %s", e)
            self.gsm = None
            raise tichy.ServiceUnusable

        self.indexes = {}       # map sim_index -> contact

    @tichy.tasklet.tasklet
    def init(self):
        #set sim info variable to be used by various apps
        logger.info("Get sim info")
        self.sim_info = yield WaitDBus(self.gsm_sim.GetSimInfo)

    def get_contacts(self):
        """Return the list of all the contacts in the SIM

        The framework may fail, so we try at least 5 times before we
        give up. We need to remove this if the framework correct this
        problem.
        """
        for i in range(5):
            try:
                logger.info("Retrieve Phonebook")
                entries = yield WaitDBus(self.gsm_sim.RetrievePhonebook,
                                         'contacts')
                logger.info("Got %d contacts" % len(entries))
                logger.debug('get contacts : %s', entries)
                break
            except Exception, e:
                logger.error("can't retrieve phone book : %s" % e)
                logger.info("retrying in 10 seconds")
                yield tichy.tasklet.Sleep(10)
                continue
        else:
            logger.error("can't retrieve phone book")
            raise Exception("can't retrieve phone book")

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

        The framework may fail, so we try at least 5 times before we
        give up. We need to remove this if the framework correct this
        problem.
        """
        for i in range(5):
            try:
                logger.info("Retrieve Messages")
                entries = yield WaitDBus(self.gsm_sim.RetrieveMessagebook,
                                         'all')
                logger.info("Got %d messages" % len(entries))
                logger.debug('get messages : %s', entries)
                break
            except Exception, e:
                logger.error("can't retrieve message book : %s" % e)
                logger.info("retrying in 10 seconds")
                yield tichy.tasklet.Sleep(10)
                continue
        else:
            logger.error("can't retrieve message book")
            raise Exception("can't retrieve message book")

        ret = []
        for entry in entries:
            #print entry
            index = int(entry[0])
            #name = unicode(entry[1])
            #tel = str(entry[2])
            status = unicode(entry[1])
            text = unicode(entry[3]).encode('utf8')
            if status in  ['read','unread']:
              timestamp = entry[4]['timestamp']
              #print timestamp
            else :
              timestamp = 'Tue Oct 14 12:01:07 2008'
            direction = unicode(entry[4]['direction'])
            peer = unicode(entry[2])

            message = SIMMessage(peer=peer,text=text,timestamp=timestamp,direction=direction,status=status, sim_index=index)
            self.indexes[index] = message
            ret.append(message)
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
        self.gsm_sim.DeleteMessage(int(message.sim_index))


    def send_pin(self, pin):
        logger.info("sending pin")
        yield WaitDBus(self.gsm_sim.SendAuthCode, pin)


class TestSim(tichy.Service):

    service = 'SIM'
    name = 'Test'

    @tichy.tasklet.tasklet
    def get_contacts(self):
        yield [SIMContact(name='test', tel='099872394', sim_index=0)]

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
        logger.info("Get sim info")
        yield None
