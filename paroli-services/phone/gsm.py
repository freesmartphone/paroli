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

import logging
logger = logging.getLogger('GSM')

import dbus

import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange

from call import Call
from threading import Timer

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
        self.missed_call_count = tichy.Int(0)
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
        tichy.Persistance('calls/logs').save(data)

    def _load_logs(self):
        """Load all the logs"""
        logger.info("Loading call logs")
        data = tichy.Persistance('calls/logs').load()
        if not data:
            return
        # TODO: add some checks for data consistency
        logs = []
        for kargs in data:
            logger.debug('_load_logs %s', kargs)
            call = Call(**kargs)
            logs.append(call)
        self.logs[:] = logs

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
            except sim.PINError:
                if i == 4: # after 3 times we give up
                    raise
                logger.info("pin wrong : %s", pin)

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


class FSOGSMService(GSMService):
    """GSMService that uses freesmartphone DBUS API"""

    service = 'GSM'
    name = 'FSO'

    def __init__(self):
        super(FSOGSMService, self).__init__()
        self.lines = {}
        self.provider = None
        self.network_strength = None
        self.gsm_call = None
        self.reg_counter = 0

    def get_provider(self):
        """Return the current provider of GSM network

        :Returns: str
        """
        return self.provider

    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        logger.info("connecting to DBus")
        yield WaitDBusName('org.freesmartphone.ousaged', time_out=120)
        logger.info("connecting to freesmartphone.GSM dbus interface")
        # We create the dbus interfaces to org.freesmarphone
        self.bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
        self.ousage = self.bus.get_object('org.freesmartphone.ousaged',
                                          '/org/freesmartphone/Usage',
                                          follow_name_owner_changes=True)
        self.ousage = dbus.Interface(self.ousage, 'org.freesmartphone.Usage')
        self.gsm = self.bus.get_object('org.freesmartphone.ogsmd',
                                       '/org/freesmartphone/GSM/Device',
                                       follow_name_owner_changes=True)
        self.gsm_device = dbus.Interface(self.gsm,
                                         'org.freesmartphone.GSM.Device')
        self.gsm_network = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.Network')
        self.gsm_call = dbus.Interface(self.gsm,
                                       'org.freesmartphone.GSM.Call')
        self.gsm_network.connect_to_signal("Status", self._on_status)
        self.gsm_call.connect_to_signal("CallStatus",
                                        self._on_call_status)

    @tichy.tasklet.tasklet
    def _keep_alive(self):
        """Reinit the dbus connection if the framework crashes"""
        yield WaitDBusNameChange('org.freesmartphone.ogsmd')
        logger.error("org.freesmartphone.ogsmd crashed")
        logger.info("Attempt to re-init the service")
        yield self.init()
    
    
    def _register_jumper(self):
        #logger.info("register jumper")
        self._register().start()

    @tichy.tasklet.tasklet
    def _register(self):
        try:
            #if self.reg_counter != 0:
                #logger.info("about to wait")
            yield WaitDBus(self.gsm_network.Register)
            ret = True
            #else:
                #logger.info("elsed")
                #raise TypeError
        except:
            ret = False
        
        logger.info("ret is %s", str(ret))
        
        #self.reg_counter += 1
        
        if not ret:
            t = Timer(30, self._register_jumper)
            t.start()
            #logger.info("timer obj: %s", str(t))

        yield ret
        
    def init(self):
        """Tasklet that registers on the network
        """
        try:
            yield self._connect_dbus()
            logger.info("Request the GSM resource")
            yield WaitFSOResource('GSM', time_out=30)
            yield WaitDBus(self.ousage.RequestResource, 'GSM')
            yield self._turn_on()
            logger.info("register on the network")
            register = yield self._register()
            #if register:
                #provider = yield tichy.Wait(self, 'provider-modified')
                
            self._keep_alive().start()
            
            ##network selection end
            
        except Exception, ex:
            logger.error("Error : %s", ex)
            raise
        
        try:
            
            yield tichy.Service.get('Config').wait_initialized()
            self.config_service = tichy.Service.get("Config")
            logger.info("got config service")
        
        except Exception, ex:
            logger.error("Error in try retrieving config service : %s", ex)
        
        try:
            
            ##call forwaring setting start
            self.values = self.config_service.get_items("call_forwarding")
            if self.values != None: self.values = dict(self.values)
            logger.info("realized values is none")

        except Exception, ex:
            logger.error("Error in try call forwarding setting : %s", ex)
            
            
        try:

            self.SettingReason = tichy.settings.ListSetting('Call Forwarding','Reason',tichy.Text,value='unconditional', setter=self.ForwardingSetReason,options=["unconditional","mobile busy","no reply","not reachable","all","allconditional"],model=tichy.List([ ListSettingObject("unconditional", self.action),ListSettingObject("mobile busy",self.action),ListSettingObject("no reply", self.action),ListSettingObject("not reachable", self.action),ListSettingObject("all", self.action),ListSettingObject("all conditional", self.action)]), ListLabel =[('title','name')])
            
            self.SettingForwarding = tichy.settings.ToggleSetting('Call Forwarding', 'active', tichy.Text, value=self.GetForwardingStatus('unconditional'),setter=self.ToggleForwarding, options=['active','inactive'])
            
        
        except Exception, ex:
            logger.error("Error in try call forwarding setting list : %s", ex)
            
            
        try:

            self.SettingChannels = tichy.settings.Setting('Call Forwarding', 'channels', tichy.Text, value=self.ForwardingGet('class'), setter=self.ForwardingSetClass, options=["voice","data","voice+data","fax","voice+data+fax"])
            
            self.SettingTargetNumber = tichy.settings.NumberSetting('Call Forwarding', 'Target Number', tichy.Text, value=self.ForwardingGet('number'), setter=self.ForwardingSetNumber)
            
            self.SettingTargetNumber = tichy.settings.NumberSetting('Call Forwarding', 'Timeout', tichy.Text, value=self.ForwardingGet('timeout'), setter=self.ForwardingSetTimeout)
            
            ##call forwaring setting stop
            
        
        except Exception, ex:
            logger.error("Error in try Error in try call forwarding setting : %s", ex)
            
        try:

            ##call identifaction setting start
            self.CallIdentification = tichy.settings.Setting('Network', 'Call Identification', tichy.Text, value=self.GetCallIdentification(), setter=self.SetCallIdentifaction, options=["on","off","network"])
            ##call identifaction setting stop
        
        except Exception, ex:
            logger.error("Error in network identification setting: %s", ex)
            
        try:    
            ##network selection etc begin
            self.NetworkRegistration = tichy.settings.Setting('Network', 'Registration', tichy.Text, value=self.GetRegStatus(), setter=self.SetRegStatus, options=["registered","not registered"])
            
        
        except Exception, ex:
            logger.error("Error in network registration setting : %s", ex)
            
            
        try:
            
            self.scanning = False
            self.NetworkList = tichy.List()
            self.ListLabel = [('title','name'),('subtitle','status')]
            
            self.scan_setting = tichy.settings.ListSetting('Network', 'List', tichy.Text, value="scan", setter=self.run_scan, options=['scan'], model=self.NetworkList, ListLabel=self.ListLabel)
        
        except Exception, ex:
            logger.error("Error in network list setting : %s", ex)
            #raise
        
    def _turn_on(self):
        """turn on the antenna

        We need to check if the SIM PIN is required and if so start
        the PIN input application.
        """
        logger.info("Check antenna power")
        power = yield WaitDBus(self.gsm_device.GetAntennaPower)
        logger.info("antenna power is %d", power)
        if power:
            yield None
        logger.info("turn on antenna power")
        try:
            yield WaitDBus(self.gsm_device.SetAntennaPower, True)
        except dbus.exceptions.DBusException, ex:
            if ex.get_dbus_name() != 'org.freesmartphone.GSM.SIM.AuthFailed':
                raise
            yield self._ask_pin()

    def _on_call_status(self, call_id, status, properties):
        #logger.info("call status %s %s %s", call_id, status, properties)
        call_id = int(call_id)
        status = str(status)

        if status == 'incoming':
            logger.info("incoming call")
            # XXX: should use an assert, but it doesn't work on neo :O
            if call_id in self.lines:
                logger.warning("WARNING : line already present %s %s",
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
            call._incoming()

        elif status == 'outgoing':
            self.lines[call_id]._outgoing()
        elif status == 'active':
            self.lines[call_id]._active()
        elif status == 'release':
            self.lines[call_id]._released()
            del self.lines[call_id]
            self.update_missed_call_count()
        else:
            logger.warning("Unknown status : %s", status)

    def _on_status(self, status):
        logger.debug("status %s", status)
        if 'provider' in status:
            provider = str(status['provider'])
            if provider != self.provider:
                self.provider = provider
                self.emit('provider-modified', self.provider)
                logger.info("provider is '%s'", self.provider)
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
        logger.info("create call %s" % number)
        call = Call(number, direction=direction)
        self.logs.insert(0, call)
        return call

    @tichy.tasklet.tasklet
    def _initiate(self, call):
        """Initiate a given call
        """
        if not self.gsm_call:
            raise Exception("No connectivity")
        number = str(call.number)
        logger.info("initiate call to %s", number)
        call_id = yield WaitDBus(self.gsm_call.Initiate, number, "voice")
        call_id = int(call_id)
        logger.info("call id : %d", call_id)
        self.lines[call_id] = call
        # TODO: mabe not good idea to store this in the call itself,
        #       beside, it makes pylint upset.
        call.__id = call_id

    @tichy.tasklet.tasklet
    def _activate(self, call):
        #logger.info("activate call %s", str(call.number))
        yield WaitDBus(self.gsm_call.Activate, call.__id)

    @tichy.tasklet.tasklet
    def _send_dtmf(self, call, code):
        #logger.info("send dtmf %s to call %s", code, str(call.number))
        assert call.status == 'active'
        yield WaitDBus(self.gsm_call.SendDtmf, code)

    @tichy.tasklet.tasklet
    def _release(self, call):
        #logger.info("release call %s", str(call.number))
        yield WaitDBus(self.gsm_call.Release, call.__id)


    ##for settings

    ##network selection
    def GetRegStatus(self):
        d = self.gsm_network.GetStatus()
        if d['registration'] != 'unregistered':
            ret = ("%s with %s") % (d['registration'], d['provider'])
        else:
            ret = 'not registered'
            
        return ret
    
    @tichy.tasklet.tasklet
    def SetRegStatus(self, val):
        if self.GetRegStatus() != 'not registered':
            yield WaitDBus(self.gsm_network.Unregister)
            ret = "not registered"
        else:
            yield WaitDBus(self.gsm_network.Register)
            ret = "registered"
        yield ret

    def RegisterWithProvider_pre(self, *args, **kargs):
        self.RegisterWithProvider(*args, **kargs).start()
        
    @tichy.tasklet.tasklet
    def RegisterWithProvider(self, *args, **kargs):
        Provider = args[0][0]
        edje_obj = args[2]
        if Provider.status != 'current':
            yield WaitDBus(self.gsm_network.RegisterWithProvider, Provider.Pid)
        edje_obj.emit("back")

    @tichy.tasklet.tasklet
    def run_scan(self, val):
      if self.scanning == False:
          self.scanning = True
          self.NetworkList.clear()
          providers = yield WaitDBus(self.gsm_network.ListProviders)
          
          for i in providers:
              if i[1] != 'forbidden':
                  obj = Provider(i, self.RegisterWithProvider_pre)
                  self.NetworkList.append(obj)
          self.scanning = False
          
      yield "scan"

    ##call identification
    
    def GetCallIdentification(self):
        ret = self.gsm_network.GetCallingIdentification()
        return ret
    
    @tichy.tasklet.tasklet
    def SetCallIdentifaction(self, value):
        yield WaitDBus(self.gsm_network.SetCallingIdentification, value)
        yield value
        
    ##call forwarding

    @tichy.tasklet.tasklet
    def ToggleForwarding(self, *args):
        reason = self.ForwardingGetReason()
        if self.GetForwardingStatus(reason) == 'inactive':
              
              channel = self.ForwardingGet('status')
              number = self.ForwardingGet('number')
              timeout = self.ForwardingGet('timeout')
              try:
                  if reason == "no reply":
                      yield WaitDBus(self.gsm_network.EnableCallForwarding( reason, channel, number, int(timeout)))
                  else:
                      yield WaitDBus(self.gsm_network.EnableCallForwarding( reason, channel, number, int(timeout) ))
              except Exception, e:
                  yield tichy.Service.get('Dialog').dialog("window", 'Error', str(e))
                  logger.exception('ToggleForwarding')
                  
        else:
            self.gsm_network.DisableCallForwarding( reason )

    def GetForwardingStatus(self, reason='unconditional'):
        status = self.gsm_network.GetCallForwarding(reason)
        if len(status) == 0:
            ret = "inactive"
        else:
            ret = "active"
        return ret        
    
    def ForwardingGetReason(self):
        return self.SettingReason.value
    
    @tichy.tasklet.tasklet
    def ForwardingSetClass(self, *args, **kargs):
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
        yield 'moo'

    def action(self, *args, **kargs):
        item = args[0]
        self.SettingReason.set(item[0].name).start()
        args[2].emit('back')
        self.SettingChannels.set(self.ForwardingGet('class',reason=item[0].name)).start()
        self.SettingTargetNumber.set(self.ForwardingGet('number',reason=item[0].name)).start()

class Provider(tichy.Object):
    def __init__(self, obj, action):
        self.Pid = obj[0]
        self.status = obj[1]
        logger.debug('__init__ %s', self.status)
        self.name = obj[2]
        self.abbr = obj[3]
        self.NetworkType = obj[4]
        self.action = action

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
        logger.info("send dtmf %s to call %s", code, str(call.number))
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
            except sim.PINError:
                if i == 4: # after 3 times we give up
                    raise
                logger.info("pin wrong : %s", pin)

    def get_provider(self):
        return 'Charlie Telecom'

class ListSettingObject():
      
      def __init__(self, name, action):
          self.name = name
          self.action = action
