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

import dbus
import tichy

import logging
logger = logging.getLogger('gprs')



class GprsService(tichy.Service):
    """The 'Gprs' service
    """

    service = 'Gprs'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(GprsService, self).__init__()

    def init(self):
        yield tichy.Service.get('ConfigService').wait_initialized()
        logger.info('gprs service init')
        try:
            yield tichy.tasklet.WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            yield tichy.Service.get('GSM').wait_initialized()
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            battery = bus.get_object('org.freesmartphone.ogsmd', '/org/freesmartphone/GSM/Device')
            self.iface = dbus.Interface(battery, 'org.freesmartphone.GSM.PDP')
            self.config_service = tichy.Service.get("ConfigService")
            self.values = self.config_service.get_items("PDP")
            if self.values != None: self.values = dict(self.values)
            logger.info("values: %s", str(self.values))
            password = tichy.settings.StringSetting('gprs', 'password', tichy.Text, value=self.get_password(), setter=self.set_password)
            user = tichy.settings.StringSetting('gprs', 'user', tichy.Text, value=self.get_user(), setter=self.set_user)
            apn = tichy.settings.StringSetting('gprs', 'apn', tichy.Text, value=self.get_apn(), setter=self.set_apn)
            status = tichy.settings.ToggleSetting('gprs', 'status', tichy.Text, value=self.get_status(), setter=self.set_status, options=['registered','unregistered'], listenObject=self.iface, signal="NetworkStatus")
            self.iface.connect_to_signal("NetworkStatus", self.status_change)
            self.iface.connect_to_signal("ContextStatus", self.context_status_change)
        except Exception, e:
            logger.warning("can't use freesmartphone gprs service : %s", e)
            raise
            
            self.pdp_id = None
            
    def activate(self):
        if self.iface.NetworkStatus()["registration"] == 'unregistered':
            values = self.config_service.get_items("PDP")
            if values != None:
                try:
                    self.iface.ActivateContext(values["apn"], values["user"], values["pwd"])
                except Exception, e:
                    print e
                    print Exception
            
    def deactivate(self):
        if self.iface.NetworkStatus()["registration"] != 'unregistered':
            try:
                self.iface.DeactivateContext()
            except Exception, e:
                print e
                print Exception
    
    def context_status_change(self, index, status, properties=False):
        try:
            self.pdp_id = index
            self.status_change(status)
        except:
            pass
    
    
    def status_change(self, status):
         if status['registration'] in ["home","roaming"]:
            self.emit("gprs-status", "on")
         else:
            self.emit("gprs-status", "off")
    
    @tichy.tasklet.tasklet
    def set_password(self, val):
        self.set_param("pwd", val)
        yield None
    
    @tichy.tasklet.tasklet
    def set_user(self, val):
        self.set_param("user", val)
        yield None
    
    @tichy.tasklet.tasklet
    def set_apn(self, val):
        self.set_param("apn", val)
        yield None

    def get_status(self):
        if self.iface:
            status = self.iface.GetNetworkStatus()['registration']
            return status

    @tichy.tasklet.tasklet
    def set_status(self, val):
        status = self.get_status()
        if status == "unregistered":
            self.pdp_id = yield tichy.tasklet.WaitDBus(self.iface.ActivateContext, self.get_apn(), self.get_user(), self.get_password())
            ret = "active"
        elif status in ["home","roaming","busy"]:
            if self.pdp_id != None:
                yield tichy.tasklet.WaitDBus(self.iface.DeactivateContext)
                self.pdp_id = None
                ret = "unregistered"
        else:
            ret = "unregistering"
        yield tichy.tasklet.Wait(self,"gprs-status")
        yield ret

    def get_apn(self):
        if self.values != None and "apn" in self.values.keys():
            #logger.info("values: %s", str(self.values))
            return str(self.values["apn"])
        else:
            return ""
    
    def get_password(self):
        if self.values != None and "pwd" in self.values.keys():
            #logger.info("values: %s", str(self.values))
            return str(self.values["pwd"])
        else:
            return ""
    
    def get_user(self):
        if self.values != None and "user" in self.values.keys():
            #logger.info("values: %s", str(self.values))
            return str(self.values["user"])
        else:
            return ""
    
    def set_param(self, param, value):
        try:
            self.config_service.set_item('PDP', param, value)
        except Exception, e:
            print e
            print Exception
