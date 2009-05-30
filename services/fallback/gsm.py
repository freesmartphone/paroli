#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Paroli (formerly: Tichy)
#
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#    copyright 2009 Mirko Lindner (mirko@openmoko.org)

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

import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange
from paroli.tel_number import TelNumber, ListSettingObject
from paroli.message import SMS
from paroli.sim import GSMService, Call, SIMContact, PINError

import logging
logger = logging.getLogger('service.fallback.gsm')


class FallbackGSMService(GSMService):
    """Fake service that can be used to test without GSM drivers
    """

    service = 'GSM'
    name = 'Fallback'

    def __init__(self):
        super(FallbackGSMService, self).__init__()
        #self.logs.append(Call('0478657392'))

    def init(self):
        """register on the network"""
        logger.info("Turn on antenna power")
        logger.info("Register on the network")
        self.emit('provider-modified', "Charlie Telecom")
        self.network_strength = 100
        yield tichy.Service.get('Config').wait_initialized()
        self.config_service = tichy.Service.get("Config")
        logger.info("got config service")
        self.values = self.config_service.get_items("call_forwarding")
        if self.values != None: self.values = dict(self.values)
        logger.info("realized values is none")
        self.SettingReason = tichy.settings.ListSetting('Call Forwarding', 'Reason', tichy.Text, value='unconditional', setter=self.ForwardingSetReason, options=["unconditional","mobile busy","no reply","not reachable","all","all conditional"], model=tichy.List([ListSettingObject("unconditional", self.action),ListSettingObject("mobile busy", self.action),ListSettingObject("no reply", self.action),ListSettingObject("not reachable", self.action),ListSettingObject("all", self.action),ListSettingObject("all conditional", self.action)]), ListLabel = [('title','name')])
        self.SettingChannels = tichy.settings.Setting('Call Forwarding', 'channels', tichy.Text, value=self.ForwardingGet('class'), setter=self.ForwardingSetClass, options=["voice","data","voice+data","fax","voice+data+fax"])
        self.SettingTargetNumber = tichy.settings.NumberSetting('Call Forwarding', 'Target Number', tichy.Text, value=self.ForwardingGet('number'), setter=self.ForwardingSetNumber)
        self.SettingTargetNumber = tichy.settings.NumberSetting('Call Forwarding', 'Timeout', tichy.Text, value=self.ForwardingGet('timeout'), setter=self.ForwardingSetTimeout)
        
        if len(self.logs) == 0:    
            for i in range(3):
                call = Call('0049110', direction='out')
                self.logs.insert(0, call)
        yield None
    
    #@tichy.tasklet.tasklet
    #def ToggleForwarding(self):
    
    #def GetForwardingStatus(self, reason):
        
    
    def ForwardingGetReason(self):
        return self.SettingReason.value
    
    @tichy.tasklet.tasklet
    def ForwardingSetClass(self, *args, **kargs):
        logger.debug("here are the args %s", args)
        value = "%s,%s,%s" % (str(args[0]), self.ForwardingGet('number'), self.ForwardingGet('timeout'))
        self.set_param(value)
        yield value
    
    @tichy.tasklet.tasklet
    def ForwardingSetNumber(self, *args, **kargs):
        logger.debug("here are the args %s", args)
        value = "%s,%s,%s" % (self.ForwardingGet('class'), str(args[0]), self.ForwardingGet('timeout'))
        self.set_param(value)
        yield value
    
    @tichy.tasklet.tasklet
    def ForwardingSetTimeout(self, *args, **kargs):
        logger.debug("here are the args %s", args)
        value = "%s,%s,%s" % (self.ForwardingGet('class'), self.ForwardingGet('number'), str(args[0]))
        self.set_param(value)
        yield value
    
    def set_param(self, value):
        reason = self.ForwardingGetReason().encode('ascii')
        try:
            self.config_service.set_item('call_forwarding', reason.replace(' ','_'), value)
            self.values = self.config_service.get_items("call_forwarding")
            if self.values != None: self.values = dict(self.values)
        except Exception, e:
            logger.exception('set_param')
    
    def ForwardingGet(self, cat, reason=False):
        if reason:
            reason = reason
        else:
            reason = self.ForwardingGetReason().encode('ascii')
        attribute = {'class':0,'number':1,'timeout':2}
        if self.values != None:
            if self.values.has_key(reason.replace(' ','_')):
                logger.info("trying to get value")
                vals_list = self.values[reason.replace(' ','_')].split(',')
                if len(vals_list) >= attribute[cat]+1:
                    ret = vals_list[attribute[cat]]
                else:
                    ret = None
            else:
                ret = None
        else:
            ret = None
        return ret
    
    @tichy.tasklet.tasklet
    def ForwardingSetReason(self, *args, **kargs):
        #print "forwardingSetReason"
        #print self.ForwardingGet('class')
        #print args
        #print kargs
        yield 'moo'

    def action(self, *args, **kargs):
        item = args[0]
        self.SettingReason.set(item[0].name).start()
        args[2].emit('back')
        self.SettingChannels.set(self.ForwardingGet('class',reason=item[0].name)).start()
        self.SettingTargetNumber.set(self.ForwardingGet('number',reason=item[0].name)).start()

    def create_call(self, number, direction='out'):
        call = Call(number, direction=direction)
        self.logs.insert(0, call)
        return call

    @tichy.tasklet.tasklet
    def _initiate(self, call):
        def on_timeout():
            call._active()
            if call.number == '666':
                self._start_incoming().start()
        tichy.mainloop.timeout_add(1000, on_timeout)
        yield None

    @tichy.tasklet.tasklet
    def _start_incoming(self):
        logger.info("simulate incoming call in 5 second")
        yield Sleep(5)
        call = self.create_call('01234567', direction='in')
        self.emit('incoming-call', call)

    @tichy.tasklet.tasklet
    def _activate(self, call):
        logger.info("activate call")
        yield Sleep(1)
        call._active()

    @tichy.tasklet.tasklet
    def _send_dtmf(self, call, code):
        logger.info("send dtmf %s to call %s", code, call.number)
        assert call.status == 'active'
        yield Sleep(1)

    @tichy.tasklet.tasklet
    def _release(self, call):
        call._released()
        yield None

    @tichy.tasklet.tasklet
    def _ask_pin(self):
        #window = tichy.Service.get("WindowsManager").get_app_parent()
        window = None
        editor = tichy.Service.get('TelePIN2')
        sim = tichy.Service.get('SIM')
        for i in range(4):
            pin = yield editor.edit(window, name="Enter PIN",
                                    input_method='number')
            try:
                yield sim.send_pin(pin)
                break
            except sim.PINError, e:
                if i == 4: # after 3 times we give up
                    raise
                logger.exception("pin wrong : %s", e)

    def get_provider(self):
        return 'Charlie Telecom'

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

class FallbackSIMService(tichy.Service):

    service = 'SIM'
    name = 'Fallback'

    PINError = PINError

    @tichy.tasklet.tasklet
    def get_contacts(self):
        yield [SIMContact(name='atest', tel='099872394', sim_index=0),SIMContact(name='btest2', tel='099872394', sim_index=0),SIMContact(name='ctest3', tel='099872394', sim_index=0),SIMContact(name='dtest4', tel='099872394', sim_index=0),SIMContact(name='etest5', tel='099872394', sim_index=0),SIMContact(name='ftest6', tel='099872394', sim_index=0),SIMContact(name='ttest7', tel='099872394', sim_index=0),SIMContact(name='htest8', tel='099872394', sim_index=0),SIMContact(name='utest9', tel='099872394', sim_index=0),SIMContact(name='otest10', tel='099872394', sim_index=0),SIMContact(name='ptest11', tel='099872394', sim_index=0),SIMContact(name='ptest12', tel='099872394', sim_index=0),SIMContact(name='rtest13', tel='099872394', sim_index=0),SIMContact(name='qtest14', tel='099872394', sim_index=0),SIMContact(name='ltest15', tel='099872394', sim_index=0),SIMContact(name='ztest16', tel='099872394', sim_index=0),SIMContact(name='ytest17', tel='099872394', sim_index=0)]

    @tichy.tasklet.tasklet
    def get_messages(self):
        yield []

    @tichy.tasklet.tasklet
    def add_contact(self, name, number):
        #logger.info("add %s : %s into the sim" % (name, number))
        index = 0
        contact = SIMContact(name=name, tel=number, sim_index=index)
        yield contact

    @tichy.tasklet.tasklet
    def remove_contact(self, contact):
        #logger.info("remove contact %s from sim", contact.name)
        yield None

    @tichy.tasklet.tasklet
    def init(self):
        self.sim_info = {'imsi':'0123456789012345'}
        yield None

    @tichy.tasklet.tasklet
    def send_pin(self, pin):
        logger.info("sending pin")
        yield None

class FallbackSMSService(tichy.Service):

    service = 'SMS'
    name = 'Fallback'

    @tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('Config').wait_initialized()
        self.config_service = tichy.Service.get("Config")
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
