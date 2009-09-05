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

import logging
logger = logging.getLogger('services.fso.wifi')

import dbus
from tichy.object import Object
from tichy.text import Text
from tichy.list import List
from tichy.tasklet import Tasklet, WaitDBus, WaitDBusName, WaitDBusSignal, Sleep, WaitDBusNameChange, WaitFirst, tasklet
from tichy.service import Service
from tichy import mainloop
import tichy.settings

class FSOWifiService(Service):
    """The 'Wifi' service
    """

    service = 'Wifi'
    name = 'FSO'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(FSOWifiService, self).__init__()

    def init(self):
        logger.info('wifi service init')
        try:
            self.config_service = Service.get("Config")
            yield self.config_service.wait_initialized()
            self.usage_service = Service.get('Usage')
            yield self.usage_service.wait_initialized()
            yield self.usage_service.request_resource('Wifi')
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)

            ## power related
            power_obj = bus.get_object('org.freesmartphone.odeviced', 
                                       '/org/freesmartphone/Device/PowerControl/WiFi')
            self.power_iface = dbus.Interface(power_obj, 
                                              'org.freesmartphone.Device.PowerControl')
            try_num = 0
            obj = None
            ## devicing
            for i in range(5):
                    try:
                        obj = bus.get_object("org.moblin.connman", "/")
                        logger.info("moblin success")
                    except:
                        logger.info("moblin failed")
                        yield WaitFirst(Sleep(1))
                        continue
                    else:
                        break
                        #raise Exception("moblin not starting")
            if obj:
                self.devicing_iface = dbus.Interface(
                                           obj, 
                                           "org.moblin.connman.Manager")
                self.status_setting = tichy.settings.ToggleSetting(
                                            'wifi', 'power', 
                                            Text, value=self.get_power(), 
                                            setter=self.power, 
                                            options=['active','inactive'])
                self.NetworkList = List()
                self.ListLabel = [('title','name'),('subtitle','info')]
                self.scan_setting = tichy.settings.ListSetting('wifi', 
                                                               'scan', 
                                                               Text, 
                                                               value="Networks", 
                                                               setter=self.run_scan, 
                                                               options=['Networks'], 
                                                               model=self.NetworkList, 
                                                               ListLabel=self.ListLabel)
                if self.get_power():
                    self.get_device()
                self.devicing_iface.connect_to_signal('PropertyChanged', 
                                                      self.property_changed)
                self.connect("closing", self.closing)
            else: 
                logger.error("Moblin failed. Is Connman/moblin installed?")
        except Exception, e:
            logger.exception("can't use wifi service : %s", e)
            raise

    def closing(self, *args, **kargs):
        if self.power_iface.GetPower():
            self.power('moo').start()

    @tasklet
    def power(self, status):
        logger.info("setting power of wifi device")
        if self.power_iface.GetPower():
            yield WaitDBus(self.power_iface.SetPower,False)
            ret = "inactive"
        else:
            yield WaitDBus(self.power_iface.SetPower,True)
            ret = "active"

        logger.info("new status %s", ret)
        yield ret

    def get_power(self):
        val = self.power_iface.GetPower()
        if val:
            ret = "active"
        else:
            ret = "inactive"
        return ret


    def property_changed(self, *args, **kargs):
        if args[0] == 'Devices':
            self.get_device()


    def get_device(self):
        ## device
        if len(self.devicing_iface.GetProperties()['Devices']) > 0:
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            addr = self.devicing_iface.GetProperties()['Devices'][0]
            dev_obj = bus.get_object("org.moblin.connman", dbus.ObjectPath(addr))
            self.device = dbus.Interface(dev_obj, 'org.moblin.connman.Device')
            self.device.SetProperty("Scanning", False)
            self.device.connect_to_signal("PropertyChanged", self.DevPropChange)

    def DevPropChange(self, *args, **kargs):
        cat = args[0]
        val = args[1]

        if cat == "Networks":
            if self.get_power() == 'active':
                if hasattr(self, 'device'):
                    networks = self.device.GetProperties()['Networks']
                    self.NetworkList.clear()
                    for n in networks:
                        bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
                        dev_obj = bus.get_object("org.moblin.connman", dbus.ObjectPath(n))
                        nw = dbus.Interface(dev_obj, 'org.moblin.connman.Network')
                        nw_obj = WifiNetwork(self.NetworkList, nw, self.WiFiConnectPre)
                        self.NetworkList.append(nw_obj)
        elif cat == 'Powered':
            if self.get_power() == 'inactive':
                self.NetworkList.clear()
        elif cat == "Scanning":
            if not val:
                self.device.SetProperty("Scanning", True)
        else:
            logger.info(cat)

    def WiFiConnectPre(self, *args, **kargs):
        self.WiFiConnect(*args, **kargs).start()

    @tasklet
    def WiFiConnect(self, *args, **kargs):

        network = args[0][0]
        parent = args[1]
        edje_obj = args[2]
        if network.DBusObject.GetProperties()['Connected']:
            network.DBusObject.Disconnect(reply_handler=self.connection_info,
                                          error_handler=self.connection_info)
        else:  
            if network.WiFiSecurity   != 'none' and \
               network.WiFiPassphrase == '':
                fe = Service.get("FreeEdit")
                passphrase = yield fe.StringEdit(None, parent, edje_obj)
                logger.info("passphrase entered is: %s", passphrase)
                network.DBusObject.SetProperty("WiFi.Passphrase", passphrase)
            network.DBusObject.Connect(reply_handler=self.connection_info,
                                       error_handler=self.connection_info)
        yield None

    def connection_info(self, *args, **kargs):
        #if network.DBusObject.GetProperties()['Connected']:
            #logger.info("connected to wifi")
        #else:
            #logger.info("disconnected from wifi")
        pass

    @tasklet
    def run_scan(self, *args, **kargs):
        if self.get_power() == 'active':
            logger.info("power active")
            if hasattr(self, 'device'):
                try:
                    yield WaitDBus(self.device.ProposeScan)
                    logger.debug(" wifi Scan proposed")
                except:
                    logger.debug("proposing wifi scan failed")
                yield WaitDBus(self.device.SetProperty,"Scanning", True)
            yield "scan"
        else:
            self.status_setting.rotate()
            yield "scan"

class WifiNetwork(Object):
    def __init__(self, NetworkList, DBusObject, action):
        self.DBusObject = DBusObject
        self.NetworkList  = NetworkList
        self.action = action
        self.get_vals(DBusObject, action)
        self.DBusObject.connect_to_signal("PropertyChanged", self.UpdateProp)

    def UpdateProp(self, *args):
        cat = str(args[0])
        val = args[1]
        if hasattr(self, str(cat)):
            if cat == 'Connected':
                if val:
                    self.info = 'connected'
                else:
                    self.info = self.WiFiSecurity
            else:
                logger.info("cat is %s", cat)
            setattr(self, cat, val)
        self.NetworkList.emit("appended")

    def get_vals(self, DBusObject, action):
        ConnmanProps = DBusObject.GetProperties()
        self.name = ConnmanProps['Name']
        if ConnmanProps.has_key("Strength"):
            self.strength = ConnmanProps['Strength']
        if ConnmanProps.has_key("WiFi.Security"):
            self.WiFiSecurity = ConnmanProps['WiFi.Security']
        else:
            self.WiFiSecurity = ''
        if ConnmanProps.has_key("WiFi.Passphrase"):
            self.WiFiPassphrase = ConnmanProps['WiFi.Passphrase']
        else:
            self.WiFiPassphrase = ''
        self.Connected = ConnmanProps['Connected']
        self.obj_addr = ConnmanProps['Device']
        self.mode = ConnmanProps['WiFi.Mode']
        self.mac = ConnmanProps['Address']
        if ConnmanProps['Connected'] or str(ConnmanProps['Connected']) == '1':
            self.info = 'connected'
        else:
            self.info = self.WiFiSecurity
        self.action = action
