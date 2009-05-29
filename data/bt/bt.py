# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2009 Mirko Lindner (mirko@openmoko.org)
#
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

import re
import dbus
import dbus.service
import tichy
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange

import logging
logger = logging.getLogger('bt')



class GpsService(tichy.Service):
    """The 'Gps' service
    """

    service = 'BT'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(GpsService, self).__init__()

    @tichy.tasklet.tasklet
    def init(self):
        yield None

    @tichy.tasklet.tasklet
    def init2(self):
        yield tichy.Service.get('ConfigService').wait_initialized()
        try:
            yield tichy.tasklet.WaitDBusName('org.bluez',time_out=120)
            self.usage_service = tichy.Service.get('Usage')
            yield self.usage_service.request_resource('Bluetooth')
            self.bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            manager_obj = self.bus.get_object('org.bluez', "/")
            self.Manager = dbus.Interface(manager_obj, 'org.bluez.Manager')
            raise
            try:
                default_adapter = yield WaitDBus(self.Manager.DefaultAdapter)
                adapter = yield WaitDBus(self.Manager.FindAdapter, default_adapter)
                adapter_obj = self.bus.get_object('org.bluez', adapter)
            except:
                adapter_list = yield WaitDBus(self.Manager.ListAdapters)
                if len(adapter_list) == 0:
                    logger.info("adapter list empty.. waiting")
                    yield WaitDBusSignal(self.Manager, "AdapterAdded")
                    adapter_list = yield WaitDBus(self.Manager.ListAdapters)

                adapter_obj = self.bus.get_object('org.bluez', adapter_list[0])              
            
            self.Adapter = dbus.Interface(adapter_obj, 'org.bluez.Adapter')
                
            #self.config_service = tichy.Service.get("ConfigService")
            
            #setting up agent
            agent_path = "/test/agent"
            self.Agent = Agent(self.bus, agent_path)
            logger.debug("bluez Agent registered")
            self.Adapter.RegisterAgent(self.Agent, "DisplayYesNo")
            #listen for signals
            #on bt obj
            self.Adapter.connect_to_signal('DeviceFound',self.DeviceAppeared)
            self.Adapter.connect_to_signal('DeviceDisappeared',self.DeviceDisappeared)
            self.Adapter.connect_to_signal('DeviceRemoved',self.DeviceRemoved)
            print self.Adapter.GetProperties()
            #on service instance
            self.connect("close", self.close)
            
            self.scanning = False
            self.DeviceList = tichy.List()
            self.ListLabel = [('title','name'),('subtitle','addr')]
            
            self.scan_setting = tichy.settings.ListSetting('Bluetooth', 'List', tichy.Text, value="scan", setter=self.StartScanning, options=['scan'], model=self.DeviceList, ListLabel=self.ListLabel)
            
            #status = tichy.settings.ToggleSetting('', 'status', tichy.Text, value=self.get_status(), setter=self.set_status, options=['active','inactive'])
            
            #password = tichy.settings.StringSetting('gprs', 'password', tichy.Text, value=self.get_password(), setter=self.set_password)
            #user = tichy.settings.StringSetting('gprs', 'user', tichy.Text, value=self.get_user(), setter=self.set_user)
            #apn = tichy.settings.StringSetting('gprs', 'apn', tichy.Text, value=self.get_apn(), setter=self.set_apn)
            
            #self.iface.connect_to_signal("NetworkStatus", self.status_change)
            #self.iface.connect_to_signal("ContextStatus", self.context_status_change)
        except Exception, e:
            logger.warning("can't use bt service : %s", e)
            raise
        else:
            logger.info('bt activated')

    def close(self, *args, **kargs):
        self.DeviceList.clear()
        yield self.usage_service.release_resource('Bluetooth')

    @tichy.tasklet.tasklet
    def StartScanning(self, val):
        yield WaitDBus(self.Adapter.StartDiscovery)
        yield val

    def DeviceAppeared(self, addr, obj):
        device = BtDevice(obj, self.Adapter, self.bus)
        if self.DeviceList.count(device) == 0:
            self.DeviceList.append(device)
            logger.info("bt device discovered and added to list")
  
    def DeviceDisappeared(self, obj):
        if self.DeviceList.count(obj) == 1:
            self.DeviceList.remove(obj)
            self.DeviceList.emit("appended")
            logger.info("bt device disappeared and was removed from the list")
    
    def DeviceRemoved(self, obj):
        m = re.search('\/org\/bluez\/.*/hci0/dev_(.*)',str(obj))
        obj = dbus.String(str(m.group(1)).replace("_",":"))            
        for i in self.DeviceList:
            if str(i.addr) == str(obj):
                self.DeviceList.remove(i)
                self.DeviceList.emit("appended")
                logger.info("bt device was removed from the list")
    
class BtDevice(tichy.Object):
    def __init__(self, obj, adapter, bus):
        self.addr = obj['Address']
        self.Adapter = adapter
        self.bus = bus
        self.attributes = obj
        self.name = obj['Name']
        self.action = self.bt_connect
        
    def bt_connect(self, *args, **kargs):
        self.DeviceConnect(*args, **kargs).start()
    
    @tichy.tasklet.tasklet
    def DeviceConnect(self, *args, **kargs):
        agent_path = unicode("/test/").encode("utf-8") + unicode(self.addr).replace(":","_").encode('utf-8')
        try:
            yield WaitDBus(self.Adapter.CreatePairedDevice, args[0][0].addr, Agent(self.bus, agent_path), "DisplayYesNo")
        except Exception, e:
            logger.debug("can't pair %s %s", str(Exception), str(e))
        yield None
    
    def __repr__(self):
        return self.addr
    
class Rejected(dbus.DBusException):
  _dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
      self.exit_on_release = exit_on_release

    @dbus.service.method("org.bluez.Agent", in_signature="", out_signature="")
    def Release(self):
      print "Release"
      #if self.exit_on_release:
        #mainloop.quit()

    @dbus.service.method("org.bluez.Agent", in_signature="os", out_signature="")
    def Authorize(self, device, uuid):
      print "Authorize (%s, %s)" % (device, uuid)

    @dbus.service.method("org.bluez.Agent", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
      logger.debug("RequestPinCode (%s)",str(device))
      pin_remote = tichy.Text("")
      self.pairing_dialog(device, variable=pin_remote)
      while True:
      
          if pin_remote.value == "":
              
              logger.info("pin_remote empty")
              continue
              
          else:
              logger.info("pin remote %s", str(pin_remote.value))
              break
      
      pin = unicode(pin_remote.value)
      return int(pin)
      
    @tichy.tasklet.tasklet
    def pairing_dialog(self, device):
      editor = tichy.Service.get('TelePIN2')
      pin = yield editor.edit(None, name="Enter PIN",input_method='number')
      yield pin
      #raw_input("Enter PIN Code: ")  


    @dbus.service.method("org.bluez.Agent", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
      print "RequestPasskey (%s)" % (device)
      passkey = raw_input("Enter passkey: ")
      return dbus.UInt32(passkey)

    @dbus.service.method("org.bluez.Agent", in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, passkey):
      print "DisplayPasskey (%s, %d)" % (device, passkey)

    @dbus.service.method("org.bluez.Agent",in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
      print "RequestConfirmation (%s, %d)" % (device, passkey)
      confirm = raw_input("Confirm passkey (yes/no): ")
      if (confirm == "yes"):
        return
      raise Rejected("Passkey doesn't match")

    @dbus.service.method("org.bluez.Agent",in_signature="s", out_signature="")
    def ConfirmModeChange(self, mode):
      print "ConfirmModeChange (%s)" % (mode)

    @dbus.service.method("org.bluez.Agent",in_signature="", out_signature="")
    def Cancel(self):
      print "Cancel"

    def create_device_reply(device):
      print "New device (%s)" % (device)
      #mainloop.quit()

    def create_device_error(error):
      print "Creating device failed: %s" % (error)
      #mainloop.quit()