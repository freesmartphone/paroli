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

from tel_number import TelNumber

import logging
logger = logging.getLogger('SMS')

from message import Message


class SMS(Message):

    storage = 'SIM'

    def __init__(self, peer, text, direction, status=None, timestamp=None,
                 sim_index=None, **kargs):
        super(SMS, self).__init__(peer, text, direction,
                                         status=status, timestamp=timestamp,
                                         sim_index=sim_index, **kargs)
        self.sim_index = sim_index

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        assert not isinstance(message, PhoneMessage)
        ret = PhoneMessage(peer=message.peer,text=message.text,timestamp=message.timestamp,direction=message.direction,status=message.status)
        yield ret

    def delete(self):
        sim = tichy.Service('SIM')
        yield sim.remove_message(self)

    def save(self):
        logger.warning("save SIM message not implemented yet")
        yield None

    @classmethod
    @tichy.tasklet.tasklet
    def load_all(cls):
        sim = tichy.Service('SIM')
        ret = yield sim.get_messages()
        yield ret


class FreeSmartPhoneSMS(tichy.Service):

    service = 'SMS'

    @tichy.tasklet.tasklet
    def init(self):
        logger.info("connecting to freesmartphone.GSM dbus interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            gsm = bus.get_object('org.freesmartphone.ogsmd',
                                 '/org/freesmartphone/GSM/Device')
            self.sim_iface = dbus.Interface(gsm,
                                            'org.freesmartphone.GSM.SIM')
            logger.info("Listening to incoming SMS")
            self.sim_iface.connect_to_signal("IncomingStoredMessage",
                                             self.on_incoming_message)
        except Exception, e:
            logger.warning("can't use freesmartphone SMS : %s", e)
            self.sim_iface = None
            raise tichy.ServiceUnusable
        yield None

    def update(self):
        logger.info("update sms inbox")
        status = yield WaitDBus(self.sim_iface.GetSimReady)
        status = yield WaitDBus(self.sim_iface.GetAuthStatus)
        messages = yield WaitDBus(self.sim_iface.RetrieveMessagebook, "all")
        logger.info("found %s messages into sim", len(messages))

        messages_service = tichy.Service('Messages')
        for msg in messages:
            id, status, number, text = msg
            sms = self.create(str(number), unicode(text), 'in')
            messages_service.add_to_messages(sms)

    def create(self, number='', text='', direction='out'):
        """create a new sms instance"""
        number = TelNumber.as_type(number)
        text = tichy.Text.as_type(text)
        return SMS(number, text, direction)

    @tichy.tasklet.tasklet
    def send(self, sms):
        logger.info("Storing message to %s", sms.peer)
        message_id = yield WaitDBus(self.sim_iface.StoreMessage,
                                    str(sms.peer), unicode(sms.text), {})
        logger.info("Done, id : %s", message_id)
        logger.info("Sending message")
        yield WaitDBus(self.sim_iface.SendStoredMessage, message_id)
        logger.info("Done")
        # We store a copy cause we don't want to modify the stored sms.
        logger.info("Store message into messages")
        #sms = SMS(sms.peer, sms.text, 'out')
        yield tichy.Service('Messages').add(sms)

    def on_incoming_message(self, index):
        logger.info("Incoming message %d", index)
        message = self.sim_iface.RetrieveMessage(index)
        status = str(message[0])
        peer = str(message[1])
        text = unicode(message[2])
        # XXX: It would be better to use a PhoneMessage here, and
        #      never store messages on the SIM.
        sms = SMS(peer, text, 'in')
        tichy.Service('Messages').add(sms).start()


class TestSms(tichy.Service):

    service = 'SMS'
    name = 'Test'

    def __init__(self):
        pass

    def create(self, number='', text='', direction='out'):
        number = TelNumber(number)
        text = tichy.Text(text)
        return SMS(number, text, direction)

    def update(self):
        yield None

    @tichy.tasklet.tasklet
    def send(self, sms):
        logger.info("Sending message to %s", sms.peer)
        yield tichy.tasklet.Sleep(2)
        logger.info("Store message into messages")
        yield tichy.Service('Messages').add(sms)

        yield None

    def fake_incoming_message(self, msg):
        logger.info("Incoming message %d", 0)
        sms = self.create('0123456789', msg, 'in')
        tichy.Service('Messages').add(sms).start()
