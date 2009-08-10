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
import logging
logger = logging.getLogger('services.fso.gprs')

__docformat__ = 'reStructuredText'

import dbus
from tichy.tasklet import WaitDBusName, WaitDBus, Wait, tasklet
from tichy.service import Service
from tichy.settings import StringSetting
from tichy.text import Text
from tichy import mainloop

class FSOGprsService(Service):
    """The 'Gprs' service
    """

    service = 'Gprs'
    name = 'FSO'

    def __init__(self):
        """Connect to the freesmartphone DBus object"""
        super(FSOGprsService, self).__init__()

    def init(self):
        yield Service.get('Config').wait_initialized()
        logger.info('gprs service init')
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            yield Service.get('GSM').wait_initialized()
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            battery = bus.get_object('org.freesmartphone.ogsmd', '/org/freesmartphone/GSM/Device')
            self.iface = dbus.Interface(battery, 'org.freesmartphone.GSM.PDP')
            self.config_service = Service.get("Config")
            self.values = self.config_service.get_items("PDP")
            if self.values != None: self.values = dict(self.values)
            #logger.info("values: %s", str(self.values))
            password = StringSetting('GPRS', 'password', Text, value=self.get_password(), setter=self.set_password)
            user = StringSetting('GPRS', 'user', Text, value=self.get_user(), setter=self.set_user)
            apn = StringSetting('GPRS', 'apn', Text, value=self.get_apn(), setter=self.set_apn)
            status = ToggleSetting('GPRS', 'status', Text, value=self.get_status(), setter=self.set_status, options=['registered','unregistered'], listenObject=self.iface, signal="NetworkStatus", arrayElement="registration")
            self.iface.connect_to_signal("NetworkStatus", self.status_change)
            self.iface.connect_to_signal("ContextStatus", self.context_status_change)
        except Exception, e:
            logger.exception("can't use freesmartphone gprs service : %s", e)
            raise

            self.pdp_id = None

    def activate(self):
        if self.iface.NetworkStatus()["registration"] == 'unregistered':
            values = self.config_service.get_items("PDP")
            if values != None:
                try:
                    self.iface.ActivateContext(values["apn"], values["user"], values["pwd"])
                except Exception, e:
                    logger.exception('activate')

    def deactivate(self):
        if self.iface.NetworkStatus()["registration"] != 'unregistered':
            try:
                self.iface.DeactivateContext()
            except Exception, e:
                logger.exception('deactivate')

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

    @tasklet
    def set_password(self, val):
        self.set_param("pwd", val)
        yield None

    @tasklet
    def set_user(self, val):
        self.set_param("user", val)
        yield None

    @tasklet
    def set_apn(self, val):
        self.set_param("apn", val)
        yield None

    def get_status(self):
        if self.iface:
            status = self.iface.GetNetworkStatus()['registration']
            return status

    @tasklet
    def set_status(self, val):
        status = self.get_status()
        ret = status
        logger.info("status is: %s", status)
        if status == "unregistered":
            self.pdp_id = yield WaitDBus(self.iface.ActivateContext, self.get_apn(), self.get_user(), self.get_password())
            ret = "active"
        elif status in ["home","roaming","busy"]:
            if self.pdp_id != None:
                logger.info("trying to disconnect PDP")
                yield WaitDBus(self.iface.DeactivateContext)
                logger.info("disconnected PDP")
                self.pdp_id = None
                ret = "unregistered"
            else:
                yield tichy.tasklet.WaitDBus(self.iface.DeactivateContext)
                logger.info("no pdp_id found not disconnecting")
        else:
            ret = "unregistering"
        yield Wait(self,"gprs-status")
        yield ret

    def get_apn(self):
        if self.values != None and "apn" in self.values.keys():
            #logger.info("values: %s", (self.values))
            return str(self.values["apn"])
        else:
            return ""

    def get_password(self):
        if self.values != None and "pwd" in self.values.keys():
            #logger.info("values: %s", (self.values))
            return str(self.values["pwd"])
        else:
            return ""

    def get_user(self):
        if self.values != None and "user" in self.values.keys():
            #logger.info("values: %s", (self.values))
            return str(self.values["user"])
        else:
            return ""

    def set_param(self, param, value):
        try:
            self.config_service.set_item('PDP', param, value)
        except Exception, e:
            logger.exception('set_param')
