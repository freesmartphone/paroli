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
from tichy.tasklet import WaitDBus, WaitDBusSignal, WaitFirst, Sleep

import logging
logger = logging.getLogger('SIM')

from sms import SMS
from paroli.sim import SIMContact, PINError


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

class FSOSIMService(tichy.Service):

    service = 'SIM'
    name = 'FSO'

    PINError = PINError         # Expose the PINError exception

    def __init__(self):
        super(FSOSIMService, self).__init__()
        logger.info("connecting to freesmartphone.GSM dbus interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.gsm = bus.get_object('org.freesmartphone.ogsmd',
                                      '/org/freesmartphone/GSM/Device',
                                      follow_name_owner_changes=True)
            self.gsm_sim = dbus.Interface(self.gsm,
                                          'org.freesmartphone.GSM.SIM')
            
        except Exception, e:
            logger.exception("can't use freesmartphone SIM : %s", e)
            self.gsm = None

        self.indexes = {}       # map sim_index -> contact

    #@tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('GSM').wait_initialized()
        #set sim info variable to be used by various apps
        #logger.info("Get sim info")
        try:
            msg_center = tichy.settings.NumberSetting('Messages', 'Service Center', tichy.Text, value=self.gsm_sim.GetServiceCenterNumber(), setter=self.SetServiceCenterNumber)
        except Exception, e:
            logger.exception('init')
        
        try:
            ##pin setting start
            self.PinSetting = tichy.settings.ToggleSetting('SIM', 'PIN', tichy.Text, value=self.GetAuthRequired(),setter=self.SetAuthRequired,options=["on","off"])

            self.ChangePinSetting = tichy.settings.ToggleSetting('SIM', 'Change PIN', tichy.Text, value="",setter=self.ChangeAuthCode)
            ##pin setting stop  
        except Exception, ex:
            logger.exception("Error : %s", ex)
            raise
            
        #logger.info("message center is %s", (msg_center))
        self.sim_info = yield WaitDBus(self.gsm_sim.GetSimInfo)
        yield None

    @tichy.tasklet.tasklet
    def SetServiceCenterNumber(self, value):
        self.gsm_sim.SetServiceCenterNumber(value)
        yield None

    @staticmethod
    @tichy.tasklet.tasklet
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

        bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
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

    @tichy.tasklet.tasklet
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

    def GetAuthRequired(self):
        val = self.gsm_sim.GetAuthCodeRequired()
        
        if val:
            ret = 'on'
        else:
            ret = 'off'
         
        return ret

    @tichy.tasklet.tasklet
    def SetAuthRequired(self, val):
        
        editor = tichy.Service.get('TelePIN2')
        
        pin = yield editor.edit(None, name="Enter PIN",  input_method='number')
        
        current = self.gsm_sim.GetAuthCodeRequired()
        
        try:
            self.gsm_sim.SetAuthCodeRequired(not(current),  pin)
        
        except Exception,  e:
            logger.exception('SetAuthCodeRequired')
            dialog = tichy.Service.get("Dialog")
            yield dialog.dialog(None,  "Error",  str(e),  Exception)
        
        ret = self.GetAuthRequired()
        
        yield ret

    @tichy.tasklet.tasklet
    def ChangeAuthCode(self, val):
        
        editor = tichy.Service.get('TelePIN2')
        
        old_pin = yield editor.edit(None, text="Enter old PIN",  input_method='number')
        
        current = self.gsm_sim.GetAuthCodeRequired()
        
        new_pin = yield editor.edit(None, text="Enter new PIN",  input_method='number')
        
        try:
            self.gsm_sim.ChangeAuthCode(old_pin,  new_pin)
        
        except Exception,  e:
            logger.exception('ChangeAuthCode')
            dialog = tichy.Service.get("Dialog")
            yield dialog.dialog(None,  "Error",  str(e),  Exception)
        
        ret = ""
        
        yield ret
