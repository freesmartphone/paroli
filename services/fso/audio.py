# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2008 Mirko Lindner (mirko@openmoko.org)
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
#    along with paroli.  If not, see <http://www.gnu.org/licenses/>.
import logging
logger = logging.getLogger('services.fso.audio')

import dbus
from tichy.int import Int
from tichy.tasklet import WaitDBusName, tasklet
from tichy.settings import Setting
from tichy.service import Service
from tichy import mainloop


class FSOSetting(Setting):
    """Special setting class that hooks into a FSO preference

    It relies on the 'Prefs' service.
    """
    @property
    def value(self):
        """accessor to the actual value"""
        prefs = Service.get('Prefs')
        return prefs[self.group][self.name]

    @tasklet
    def set(self, value):
        """Try to set the Setting value and block until it is done"""
        prefs = Service.get('Prefs')
        # XXX: make this asynchronous
        prefs[self.group][self.name] = value
        self.options.emit('updated')
        yield None

class FSOAudioService(Service):

    service = 'Audio'
    name = 'FSO'

    def __init__(self):
        super(FSOAudioService, self).__init__()
        self.device = None
        self.audio = None
        self.muted = 0
        self.pushed = 0

    @tasklet
    def init(self):
        logger.info("audio.py->init()")
        yield Service.get('GSM').wait_initialized()
        yield self._connect_dbus()
        if self.device != None:
            self.mic_state = self.get_mic_status()
            ##XXX: currently not working method in Framework so we assume 40
            #self.speaker_volume = self.get_speaker_volume()
            self.speaker_volume = Int(50)
        Setting('phone', 'ring-volume', Int,  options=[0,25,50,75,100])
        Setting('phone', 'message-volume', Int, options=[0,25,50,75,100])
        Setting('phone', 'ring-vibration', bool,  options=[False,True])
        Setting('phone', 'message-vibration', bool,  options=[False,True])
        yield None

    @tasklet
    def _connect_dbus(self):
        logger.info("connecting to freesmartphone.GSM dbus audio interface")
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=mainloop.dbus_loop)
            device = bus.get_object('org.freesmartphone.ogsmd', '/org/freesmartphone/GSM/Device')
            self.device = dbus.Interface(device, 'org.freesmartphone.GSM.Device')

            audio = bus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/Audio')
            self.audio = dbus.Interface(audio, 'org.freesmartphone.Device.Audio')

        except Exception, e:
            logger.exception("can't use freesmartphone audio : %s", e)
            raise ServiceUnusable # what the hell is this? FIXME has this ever worked?

    def _do_sth(self):
        pass

    def get_mic_status(self):
        logger.info("retriving mic status")
        return self.device.GetMicrophoneMuted()

    def set_mic_status(self, val):
        if self.muted != 1:
            self.device.SetMicrophoneMuted(val)

    def get_speaker_volume(self):
        logger.info("retriving speaker status")
        return self.device.GetSpeakerVolume()

    def set_speaker_volume(self, val):
        logger.info("set speaker vol called")
        if self.muted != 1:
            self.device.SetSpeakerVolume(int(val))
            logger.info("set volume to %d", self.get_speaker_volume())

    def push_scenario(self, state):
        """It push on top of the stack the new scenario(gsmhandset, speakerout)
        """
        logger.info("we push the gsmhandset scenario for enabling sound in call")
        try:
            self.audio.PushScenario('gsmhandset')
            self.pushed += 1
        except dbus.DBusException, e:
            logger.exception("pushscenarrio: %s", e)
        
        logger.info("current scenario file is: %s", self.audio.GetScenario())
        
        
        return
    
    def pull_scenario(self):
        """It pulls scenario from the top of the stack, reenabling the last 
        used scenario.
        """
        logger.info("pull_scenario")
        
        if self.pushed > 0:
            used_scenario = self.audio.PullScenario()
            self.pushed -= 1
            logger.info("this is the scenario what we used: %s", used_scenario)
        else:
            logger.error("we want to pull scenario without pushing it first!!!")
        logger.info("and this is the current scenario: %s", self.audio.GetScenario())
        return
        
    def audio_toggle(self):
        if self.device != None:
            if self.muted == 0:
                self.muted = 1
                self.device.SetMicrophoneMuted(True)
                # Notice: this does in no way affect the ringtone volume of an incoming call
                self.device.SetSpeakerVolume(0)
                logger.info("mic muted: %i speaker volume %i", self.get_mic_status(),self.get_speaker_volume())
            elif self.muted == 1:
                self.device.SetMicrophoneMuted(self.mic_state)
                self.device.SetSpeakerVolume(self.speaker_volume)
                self.muted = 0
                logger.info("mic muted: %i speaker volume %i", self.get_mic_status(),self.get_speaker_volume())
            return 0
        else:
            return 1

    def stop_all_sounds(self):
        logger.info("Stop all sounds")
        self.audio.StopAllSounds()
        #restore the previous scenario file
        self.pull_scenario()

    def ringtone(self, ringtype):
        if ringtype == "call":
            logger.info("playing ringtone")
            self.play("/usr/share/sounds/ringtone_ringnroll.wav", 1)
        if ringtype == "message":
            logger.info("playing smstone")
            self.play("/usr/share/sounds/notify_message.wav")

    def play(self, filepath, loop=0, length=0):
        if filepath == "/usr/share/sounds/phone_ringing.ogg":
            # TODO: how the hell coming this phone_ringing.ogg parameter?
            # needs to be fixed ASAP
            logger.error("/usr/share/sounds/phone_ringing.ogg passed as argument!")
            filepath = "/usr/share/sounds/ringtone_ringnroll.wav"
        try:
            # rules.yaml RingTone() function
            self.audio.PlaySound( filepath, loop, length )
        except dbus.DBusException, e:
            logger.exception("play: %s, filepath: %s", e, filepath)
            
            assert e.get_dbus_name() == "org.freesmartphone.Device.Audio.PlayerError", \
                                            "wrong error returned"
        else:
            assert False, "PlayerError expected"
