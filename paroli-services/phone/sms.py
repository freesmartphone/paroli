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
        sim = tichy.Service.get('SIM')
        yield sim.remove_message(self)

    def save(self):
        logger.warning("save SIM message not implemented yet")
        yield None

    @classmethod
    @tichy.tasklet.tasklet
    def load_all(cls):
        sim = tichy.Service.get('SIM')
        yield sim.wait_initialized()
        ret = yield sim.get_messages()
        yield ret


class FreeSmartPhoneSMS(tichy.Service):

    service = 'SMS'

    def __init__(self):
        super(FreeSmartPhoneSMS, self).__init__()

    @tichy.tasklet.tasklet
    def init(self):
        logger.info("connecting to freesmartphone.GSM SMS dbus interface")
        yield tichy.Service.get('GSM').wait_initialized()
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            gsm = bus.get_object('org.freesmartphone.ogsmd',
                                 '/org/freesmartphone/GSM/Device')
            self.sim_iface = dbus.Interface(gsm,
                                            'org.freesmartphone.GSM.SIM')
            self.sms_iface = dbus.Interface(gsm,
                                            'org.freesmartphone.GSM.SMS')

            logger.info("Listening for incoming SMS")
            # XXX: we should use the IncomigMessage method, but there
            #      is a bug in the framework.
            self.sms_iface.connect_to_signal("IncomingMessage",
                                             self.on_incoming_unstored_message)
            self.sim_iface.connect_to_signal("IncomingStoredMessage",
                                             self.on_incoming_message)
            self.sim_iface.connect_to_signal("MemoryFull",
                                             self.on_memory_full)
            
            self.sms_iface.connect_to_signal("IncomingMessageReceipt",
                                             self.on_incoming_unstored_message)
            
            
            ##stuff for settings
            
            self.config_service = tichy.Service.get("ConfigService")
            self.values = self.config_service.get_items("Messages")
            if self.values != None: self.values = dict(self.values)
            
            self.ReportSetting = tichy.settings.Setting('Messages', 'Delivery Report', tichy.Text, value=self.GetDeliveryReport(), setter=self.SetParam, options=["on","off"])
            
        except Exception, e:
            logger.error("can't use freesmartphone SMS : %s", e)
            self.sim_iface = None
        yield None

    def update(self):
        logger.info("update sms inbox")
        status = yield WaitDBus(self.sim_iface.GetSimReady)
        status = yield WaitDBus(self.sim_iface.GetAuthStatus)
        messages = yield WaitDBus(self.sim_iface.RetrieveMessagebook, "all")
        logger.info("found %s messages into sim", len(messages))

        messages_service = tichy.Service.get('Messages')
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
        logger.info("Sending message to %s", sms.peer)
        if self.GetDeliveryReport() == 'on':
            properties = {'type':'sms-submit','alphabet': 'gsm_default','status-report-request':True}
        else:
            logger.info("no delivery report value is %s", self.GetDeliveryReport())
            properties = dict(type='sms-submit', alphabet='gsm_default')
        try:
            index, timestamp = yield WaitDBus(self.sms_iface.SendMessage,
                                          str(sms.peer), unicode(sms.text),
                                          properties)
        except Exception, e:
            logger.info ("%s %s", str(Exception), str(e))
        logger.info("Store message into messages")
        yield tichy.Service.get('Messages').add(sms)

    def on_incoming_unstored_message(self, *args, **kargs):
        logger.info("incoming unstored message")
        logger.debug('on_incoming_unstored_message %s', args)
        self._on_incoming_unstored_message(args).start()

    @tichy.tasklet.tasklet
    def _on_incoming_unstored_message(self, message):
        # XXX: It would be better to use a PhoneMessage here, and
        #      never store messages on the SIM.
        #logger.info("Incoming message %d", index)
        #message = yield WaitDBus(self.sim_iface.RetrieveMessage, index)
        #status = str(message[0])
        peer = str(message[0])
        if message[2]['type'] == 'sms-status-report':
            text = unicode(message[2]['status-message']) + unicode(', message was received: ') + unicode(message[2]['timestamp'])
        else:
            text = unicode(message[1])
        messages_service = tichy.Service.get('Messages')
        store_message = messages_service.create(peer, text, 'in')
        yield messages_service.add(store_message)
        tichy.Service.get('Sounds').Message()
        # We delete the message from the SIM
        if message[2]['type'] != 'sms-status-report':
            self.sms_iface.AckMessage(store_message)
        #yield WaitDBus(self.sim_iface.DeleteMessage, index)

    def on_incoming_message(self, index):
        self._on_incoming_message(index).start()

    @tichy.tasklet.tasklet
    def _on_incoming_message(self, index):
        # XXX: It would be better to use a PhoneMessage here, and
        #      never store messages on the SIM.
        logger.info("Incoming message %d", index)
        message = yield WaitDBus(self.sim_iface.RetrieveMessage, index)
        status = str(message[0])
        peer = str(message[1])
        text = unicode(message[2])
        messages_service = tichy.Service.get('Messages')
        message = messages_service.create(peer, text, 'in')
        yield messages_service.add(message)
        tichy.Service.get('Sounds').Message()
        # We delete the message from the SIM
        logger.info("deleting %d", index)
        yield WaitDBus(self.sim_iface.DeleteMessage, index)
        logger.info("deleted %d", index)

    def on_memory_full(self, *args, **kargs):
        logger.info("SIM full")
        ##not yielding as this is not meant to block anything
        tichy.Service.get('Dialog').dialog("window", 'SIM', "your SIM card is full, please delete messages").start()
        

    #settings functions begin
    def GetDeliveryReport(self):
        if self.values != None:
            ret = self.values['deliveryreport']
        else: 
            self.SetDeliveryReport('off')
            ret = 'off'
        
        return ret
        
    @tichy.tasklet.tasklet    
    def SetParam(self, value):
        self.SetDeliveryReport(value)
        yield value
    
    def SetDeliveryReport(self, value):
        try:
            self.config_service.set_item('Messages', 'DeliveryReport', value)
        except Exception, e:
            logger.exception('SetDeliveryReport')
          
class TestSms(tichy.Service):

    service = 'SMS'
    name = 'Test'

    @tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('ConfigService').wait_initialized()
        self.config_service = tichy.Service.get("ConfigService")
        self.values = self.config_service.get_items("Messages")
        
        if self.values != None: self.values = dict(self.values)
        logger.info("init done")
        self.ReportSetting = tichy.settings.Setting('Messages', 'Delivery Report', tichy.Text, value=self.GetDeliveryReport(), setter=self.SetParam, options=["on","off"])
        yield None

    def create(self, number='', text='', direction='out'):
        number = TelNumber(number)
        text = tichy.Text(text)
        return SMS(number, text, direction)

    def update(self):
        yield None

    @tichy.tasklet.tasklet
    def send(self, sms):
        #logger.info("Sending message to %s", sms.peer)
        yield tichy.tasklet.Sleep(2)
        logger.info("Store message into messages")
        yield tichy.Service.get('Messages').add(sms)

        yield None

    def fake_incoming_message(self, msg):
        logger.info("Incoming message %d", 0)
        sms = self.create('0123456789', msg, 'in')
        tichy.Service.get('Messages').add(sms).start()

    #settings functions begin
    def GetDeliveryReport(self):
        if self.values != None:
            ret = self.values['deliveryreport']
        else: 
            self.SetDeliveryReport('off')
            ret = 'off'
        
        return ret
        
    @tichy.tasklet.tasklet    
    def SetParam(self, value):
        self.SetDeliveryReport(value)
        yield value
    
    def SetDeliveryReport(self, value):
        try:
            self.config_service.set_item('Messages', 'DeliveryReport', value)
        except Exception, e:
            logger.exception('SetDeliveryReport')
