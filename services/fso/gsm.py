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

import dbus
from threading import Timer

from tichy.object import Object
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange, tasklet
from tichy.service import Service
from tichy.list import List
from tichy.text import Text
from tichy.settings import ListSetting, ToggleSetting, Setting, NumberSetting
from tichy import mainloop
from paroli.tel_number import TelNumber, ListSettingObject
from paroli.message import SMS
from paroli.sim import GSMService, Call, SIMContact, PINError

import logging
logger = logging.getLogger('service.fso.gsm')


class WaitFSOResource(Tasklet):
    """Wait for a FSO resource to be available"""
    def run(self, name, time_out=None):
        yield WaitDBusName('org.freesmartphone.ousaged', time_out=time_out)
        bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
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

    @tasklet
    def _connect_dbus(self):
        logger.info("connecting to DBus")
        yield WaitDBusName('org.freesmartphone.ousaged', time_out=120)
        logger.info("connecting to freesmartphone.GSM dbus interface")
        # We create the dbus interfaces to org.freesmarphone
        self.bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
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

    @tasklet
    def _keep_alive(self):
        """Reinit the dbus connection if the framework crashes"""
        yield WaitDBusNameChange('org.freesmartphone.ogsmd')
        logger.error("org.freesmartphone.ogsmd crashed")
        logger.info("Attempt to re-init the service")
        yield self.init()


    def _register_jumper(self):
        #logger.info("register jumper")
        self._register().start()

    @tasklet
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

        logger.info("ret is %s", ret)

        #self.reg_counter += 1

        if not ret:
            t = Timer(30, self._register_jumper)
            t.start()
            #logger.info("timer obj: %s", t)

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
                #provider = yield Wait(self, 'provider-modified')

            self._keep_alive().start()

            ##network selection end

        except Exception, ex:
            logger.exception("Error : %s", ex)
            raise

        try:

            yield Service.get('Config').wait_initialized()
            self.config_service = Service.get("Config")
            logger.info("got config service")

        except Exception, ex:
            logger.exception("Error in try retrieving config service : %s", ex)

        try:

            ##call forwaring setting start
            self.values = self.config_service.get_items("call_forwarding")
            if self.values != None: self.values = dict(self.values)
            logger.info("realized values is none")

        except Exception, ex:
            logger.exception("Error in try call forwarding setting : %s", ex)


        try:

            self.SettingReason = ListSetting('call Forwarding','Reason',Text,value='unconditional', setter=self.ForwardingSetReason,options=["unconditional","mobile busy","no reply","not reachable","all","allconditional"],model=List([ ListSettingObject("unconditional", self.action),ListSettingObject("mobile busy",self.action),ListSettingObject("no reply", self.action),ListSettingObject("not reachable", self.action),ListSettingObject("all", self.action),ListSettingObject("all conditional", self.action)]), ListLabel =[('title','name')])

            self.SettingForwarding = ToggleSetting('call Forwarding', 'active', Text, value=self.GetForwardingStatus('unconditional'),setter=self.ToggleForwarding, options=['active','inactive'])


        except Exception, ex:
            logger.exception("Error in try call forwarding setting list : %s", ex)


        try:

            self.SettingChannels = Setting('call Forwarding', 'channels', Text, value=self.ForwardingGet('class'), setter=self.ForwardingSetClass, options=["voice","data","voice+data","fax","voice+data+fax"])

            self.SettingTargetNumber = NumberSetting('call Forwarding', 'Target Number', Text, value=self.ForwardingGet('number'), setter=self.ForwardingSetNumber)

            self.SettingTargetNumber = NumberSetting('call Forwarding', 'Timeout', Text, value=self.ForwardingGet('timeout'), setter=self.ForwardingSetTimeout)

            ##call forwaring setting stop


        except Exception, ex:
            logger.exception("Error in try Error in try call forwarding setting : %s", ex)

        try:

            ##call identifaction setting start
            self.CallIdentification = Setting('network', 'Call Identification', Text, value=self.GetCallIdentification(), setter=self.SetCallIdentifaction, options=["on","off","network"])
            ##call identifaction setting stop

        except Exception, ex:
            logger.exception("Error in network identification setting: %s", ex)

        try:
            ##network selection etc begin
            self.NetworkRegistration = Setting('network', 'Registration', Text, value=self.GetRegStatus(), setter=self.SetRegStatus, options=["registered","not registered"])


        except Exception, ex:
            logger.exception("Error in network registration setting : %s", ex)


        try:

            self.scanning = False
            self.NetworkList = List()
            self.ListLabel = [('title','name'),('subtitle','status')]

            self.scan_setting = ListSetting('network', 'List', Text, value="scan", setter=self.run_scan, options=['scan'], model=self.NetworkList, ListLabel=self.ListLabel)

        except Exception, ex:
            logger.exception("Error in network list setting : %s", ex)
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
        except dbus.exceptions.DBusException, e:
            if e.get_dbus_name() != 'org.freesmartphone.GSM.SIM.AuthFailed':
                raise
            logger.exception("_turn_on %s", e)
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

    @tasklet
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

    @tasklet
    def _activate(self, call):
        #logger.info("activate call %s", (call.number))
        yield WaitDBus(self.gsm_call.Activate, call.__id)

    @tasklet
    def _send_dtmf(self, call, code):
        #logger.info("send dtmf %s to call %s", code, (call.number))
        assert call.status == 'active'
        yield WaitDBus(self.gsm_call.SendDtmf, code)

    @tasklet
    def _release(self, call):
        #logger.info("release call %s", (call.number))
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

    @tasklet
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

    @tasklet
    def RegisterWithProvider(self, *args, **kargs):
        Provider = args[0][0]
        edje_obj = args[2]
        if Provider.status != 'current':
            yield WaitDBus(self.gsm_network.RegisterWithProvider, Provider.Pid)
        edje_obj.emit("back")

    @tasklet
    def run_scan(self, val):
      if not self.scanning:
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

    @tasklet
    def SetCallIdentifaction(self, value):
        yield WaitDBus(self.gsm_network.SetCallingIdentification, value)
        yield value

    ##call forwarding

    @tasklet
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
                  logger.exception('ToggleForwarding')
                  yield Service.get('Dialog').dialog("window", 'Error', str(e))

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

    @tasklet
    def ForwardingSetClass(self, *args, **kargs):
        value = "%s,%s,%s" % (str(args[0]), self.ForwardingGet('number'), self.ForwardingGet('timeout'))
        self.set_param(value)
        yield value

    @tasklet
    def ForwardingSetNumber(self, *args, **kargs):
        logger.debug("here are the args %s", args)
        value = "%s,%s,%s" % (self.ForwardingGet('class'), str(args[0]), self.ForwardingGet('timeout'))
        self.set_param(value)
        yield value

    @tasklet
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

    @tasklet
    def ForwardingSetReason(self, *args, **kargs):
        yield 'moo'

    def action(self, *args, **kargs):
        item = args[0]
        self.SettingReason.set(item[0].name).start()
        args[2].emit('back')
        self.SettingChannels.set(self.ForwardingGet('class',reason=item[0].name)).start()
        self.SettingTargetNumber.set(self.ForwardingGet('number',reason=item[0].name)).start()

class Provider(Object):
    def __init__(self, obj, action):
        self.Pid = obj[0]
        self.status = obj[1]
        logger.debug('__init__ %s', self.status)
        self.name = obj[2]
        self.abbr = obj[3]
        self.NetworkType = obj[4]
        self.action = action

class FSOUssdService(Service):
    """The 'Button' service

    This service can be used to listen to the input signals form hw buttons
    """

    service = 'Ussd'
    name = 'FSO'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(FSOUssdService, self).__init__()
        self.last = None

    @tasklet
    def init(self):
        logger.info('init')
        yield self._connect_dbus()

    @tasklet
    def _connect_dbus(self):
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            logger.info('ussd service active')
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            input_dev = bus.get_object('org.freesmartphone.ogsmd',
                                       '/org/freesmartphone/GSM/Device',
                                       follow_name_owner_changes=True)
            self.input_intf = dbus.Interface(input_dev, 'org.freesmartphone.GSM.Network')
            self.input_intf.connect_to_signal('IncomingUssd', self._on_incoming_ussd)
        except Exception, e:
            logger.exception("can't use freesmartphone ussd service : %s", e)
            self.input_intf = None

    def _on_incoming_ussd(self, *args, **kargs):
        logger.info('incoming ussd')
        self.emit('incoming', args)

    def send_ussd(self, s):
        if self.input_intf != None:
            try:
                self.input_intf.SendUssdRequest(s)
            except Exception, e:
                logger.exception("error in ussd: %s", e)
        else:
            logger.info("unable to send ussd request")

class FSOSIMService(Service):

    service = 'SIM'
    name = 'FSO'

    PINError = PINError         # Expose the PINError exception

    def __init__(self):
        super(FSOSIMService, self).__init__()
        logger.info("connecting to freesmartphone.GSM dbus interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            self.gsm = bus.get_object('org.freesmartphone.ogsmd',
                                      '/org/freesmartphone/GSM/Device',
                                      follow_name_owner_changes=True)
            self.gsm_sim = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.SIM')

        except Exception, e:
            logger.exception("can't use freesmartphone SIM : %s", e)
            self.gsm = None

        self.indexes = {}       # map sim_index -> contact

    #@tasklet
    def init(self):
        yield Service.get('GSM').wait_initialized()
        #set sim info variable to be used by various apps
        #logger.info("Get sim info")
        try:
            msg_center = NumberSetting('Messages', 'Service Center', Text, value=self.gsm_sim.GetServiceCenterNumber(), setter=self.SetServiceCenterNumber)
        except Exception, e:
            logger.exception('init')

        try:
            ##pin setting start
            self.PinSetting = ToggleSetting('SIM', 'PIN', Text, value=self.GetAuthRequired(),setter=self.SetAuthRequired,options=["on","off"])

            self.ChangePinSetting = ToggleSetting('SIM', 'Change PIN', Text, value="",setter=self.ChangeAuthCode)
            ##pin setting stop
        except Exception, ex:
            logger.exception("Error : %s", ex)
            raise

        #logger.info("message center is %s", (msg_center))
        self.sim_info = yield WaitDBus(self.gsm_sim.GetSimInfo)
        yield None

    @tasklet
    def SetServiceCenterNumber(self, value):
        self.gsm_sim.SetServiceCenterNumber(value)
        yield None

    @staticmethod
    @tasklet
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

        bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
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
                logger.exception("sim busy, retry in 5 seconds")
                yield WaitFirst(Sleep(5),
                                WaitDBusSignal(gsm_sim, 'ReadyStatus'))
                continue
        else:
            logger.error("SIM always busy")
            raise Exception("SIM too busy")

    def get_contacts(self):
        """Return the list of all the contacts in the SIM

        The framework may fail, so we try at least 5 times before we
        give up. We need to remove this if the framework correct this
        problem.
        """
        logger.info("Retrieve Phonebook")
        ready = yield WaitDBus(self.gsm_sim.GetSimReady)
        if not ready:
           logger.info("ready false")
           while 1:
              status = yield WaitDBusSignal(self.gsm_sim, 'ReadyStatus')
              if status:
                  logger.debug("ready now true breaking")
                  break
              else:
                  logger.debug("ready still false not breaking")
                  continue

        entries = yield FSOSIMService.retry_on_sim_busy(self.gsm_sim.RetrievePhonebook,
                                          'contacts')
        logger.info("Got %d contacts" % len(entries))
        #logger.debug('get contacts : %s', entries)

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
        entries = yield FSOSIMService.retry_on_sim_busy(self.gsm_sim.RetrieveMessagebook, 'all')

        ret = []
        for entry in entries:
            #logger.debug("Got message %s", entry)
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
        #logger.info("add %s : %s into the sim" % (name, number))
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

    @tasklet
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
            logger.exception("send_pin : %s", ex)
            raise PINError(pin)

    def GetAuthStatus(self):
        val = self.gsm_sim.GetAuthStatus()
        
        return val

    def Unlock(self, puk, new_pin):
        try:
            yield WaitDBus(self.gsm_sim.Unlock, puk, new_pin)
        except:
            raise PINError(pin)

    def GetAuthRequired(self):
        val = self.gsm_sim.GetAuthCodeRequired()

        if val:
            ret = 'on'
        else:
            ret = 'off'

        return ret

    @tasklet
    def SetAuthRequired(self, val):

        editor = Service.get('TelePIN2')

        pin = yield editor.edit(None, name="Enter PIN",  input_method='number')

        current = self.gsm_sim.GetAuthCodeRequired()

        try:
            self.gsm_sim.SetAuthCodeRequired(not(current),  pin)

        except Exception,  e:
            logger.exception('SetAuthCodeRequired')
            dialog = Service.get("Dialog")
            yield dialog.dialog(None,  "Error",  str(e))

        ret = self.GetAuthRequired()

        yield ret

    @tasklet
    def ChangeAuthCode(self, val):

        editor = Service.get('TelePIN2')

        old_pin = yield editor.edit(None, text="Enter old PIN", input_method='number')

        #current = self.gsm_sim.GetAuthCodeRequired()

        new_pin_one = yield editor.edit(None, text="Enter new PIN", input_method='number')

        new_pin_two = yield editor.edit(None, text="Enter new PIN again", input_method='number')
        
        if new_pin_one == new_pin_two:
            try:
                self.gsm_sim.ChangeAuthCode(old_pin, new_pin_one)
            
            except Exception, e:
                logger.info("PIN change error")
                dialog = Service.get("Dialog")
                yield dialog.dialog(None, "Error", "Old pin entered is wrong.")
        
        else:
            dialog = tichy.Service.get("Dialog")
            yield dialog.dialog(None, "Error", "The two new PINs entered don't match.")

        ret = ""
        yield ret

class FSOSMSService(Service):

    service = 'SMS'
    name = 'FSO'

    def __init__(self):
        super(FSOSMSService, self).__init__()

    @tasklet
    def init(self):
        logger.info("connecting to freesmartphone.GSM SMS dbus interface")
        yield Service.get('GSM').wait_initialized()
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
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

            self.config_service = Service.get("Config")
            self.values = self.config_service.get_items("Messages")
            if self.values != None: self.values = dict(self.values)

            self.ReportSetting = Setting('SMS', 'Delivery Report', Text, value=self.GetDeliveryReport(), setter=self.SetParam, options=["on","off"])

        except Exception, e:
            logger.exception("can't use freesmartphone SMS : %s", e)
            self.sim_iface = None
        yield None

    def update(self):
        logger.info("update sms inbox")
        status = yield WaitDBus(self.sim_iface.GetSimReady)
        status = yield WaitDBus(self.sim_iface.GetAuthStatus)
        messages = yield WaitDBus(self.sim_iface.RetrieveMessagebook, "all")
        logger.info("found %s messages into sim", len(messages))

        messages_service = Service.get('Messages')
        for msg in messages:
            id, status, number, text = msg
            sms = self.create(str(number), unicode(text), 'in')
            messages_service.add_to_messages(sms)

    def create(self, number='', text='', direction='out'):
        """create a new sms instance"""
        number = TelNumber.as_type(number)
        text = Text.as_type(text)
        return SMS(number, text, direction)

    @tasklet
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
            logger.exception ("send %s", e)
        logger.info("Store message into messages")
        yield get('Messages').add(sms)

    def on_incoming_unstored_message(self, *args, **kargs):
        logger.info("incoming unstored message")
        logger.debug('on_incoming_unstored_message %s', args)
        self._on_incoming_unstored_message(args).start()

    @tasklet
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
        messages_service = Service.get('Messages')
        store_message = messages_service.create(peer, text, 'in')
        yield messages_service.add(store_message)
        Service.get('Sounds').Message()
        # We delete the message from the SIM
        if message[2]['type'] != 'sms-status-report':
            self.sms_iface.AckMessage(store_message)
        #yield WaitDBus(self.sim_iface.DeleteMessage, index)

    def on_incoming_message(self, index):
        self._on_incoming_message(index).start()

    @tasklet
    def _on_incoming_message(self, index):
        # XXX: It would be better to use a PhoneMessage here, and
        #      never store messages on the SIM.
        logger.info("Incoming message %d", index)
        message = yield WaitDBus(self.sim_iface.RetrieveMessage, index)
        status = str(message[0])
        peer = str(message[1])
        text = unicode(message[2])
        messages_service = Service.get('Messages')
        message = messages_service.create(peer, text, 'in')
        yield messages_service.add(message)
        Service.get('Sounds').Message()
        # We delete the message from the SIM
        logger.info("deleting %d", index)
        yield WaitDBus(self.sim_iface.DeleteMessage, index)
        logger.info("deleted %d", index)

    def on_memory_full(self, *args, **kargs):
        logger.info("SIM full")
        ##not yielding as this is not meant to block anything
        Service.get('Dialog').dialog("window", 'SIM', "your SIM card is full, please delete messages").start()


    #settings functions begin
    def GetDeliveryReport(self):
        if self.values != None:
            ret = self.values['deliveryreport']
        else:
            self.SetDeliveryReport('off')
            ret = 'off'

        return ret

    @tasklet
    def SetParam(self, value):
        self.SetDeliveryReport(value)
        yield value

    def SetDeliveryReport(self, value):
        try:
            self.config_service.set_item('Messages', 'DeliveryReport', value)
        except Exception, e:
            logger.exception('SetDeliveryReport')

