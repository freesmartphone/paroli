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

import dbus

import tichy
from tichy.tasklet import WaitDBus, WaitDBusName

import logging
logger = logging.getLogger('audio')

class FallbackAudioService(tichy.Service):

    service = 'Audio'
    name = 'Fallback'

    def __init__(self):
        super(FallbackAudioService, self).__init__()
        self.device = None
        self.muted = 0
        self.volume = tichy.Int.as_type(55)

    @tichy.tasklet.tasklet
    def init(self):
        yield self._do_sth()
        
    def _do_sth(self):
        pass
        
    def get_mic_status(self):
        return 0
        
    def set_mic_status(self, val):
        if self.muted != 1:
            pass
    
    def get_speaker_volume(self):
        return self.volume.value
        
    def set_speaker_volume(self, val):
        if self.muted != 1:
            self.volume.value = val
            logger.info("volume set to %d", self.get_speaker_volume())
        
    def audio_toggle(self):
        return 0

    def stop_all_sounds(self):
        logger.info("Stop all sounds")

class FSOAudioService(tichy.Service):

    service = 'Audio'
    name = 'FSO'

    def __init__(self):
        super(FSOAudioService, self).__init__()
        self.device = None
        self.audio = None
        self.muted = 0
        
    @tichy.tasklet.tasklet
    def init(self):
        yield tichy.Service.get('GSM').wait_initialized()
        yield self._connect_dbus()
        if self.device != None:
            self.mic_state = self.get_mic_status()
            ##XXX: currently not working method in Framework so we assume 40
            #self.speaker_volume = self.get_speaker_volume()
            self.speaker_volume = tichy.Int(50)
        tichy.settings.FSOSetting('phone', 'ring-volume', tichy.Int,  options=[0,25,50,75,100])
        tichy.settings.FSOSetting('phone', 'message-volume', tichy.Int, options=[0,25,50,75,100])
        tichy.settings.FSOSetting('phone', 'ring-vibration', bool,  options=[False,True])
        tichy.settings.FSOSetting('phone', 'message-vibration', bool,  options=[False,True])
        yield None
        
    @tichy.tasklet.tasklet
    def _connect_dbus(self):
        logger.info("connecting to freesmartphone.GSM dbus audio interface")
        try:
            yield WaitDBusName('org.freesmartphone.ogsmd', time_out=120)
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            device = bus.get_object('org.freesmartphone.ogsmd', '/org/freesmartphone/GSM/Device')
            self.device = dbus.Interface(device, 'org.freesmartphone.GSM.Device')

            audio = bus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/Audio')
            self.audio = dbus.Interface(audio, 'org.freesmartphone.Device.Audio')

        except Exception, e:
            logger.exception("can't use freesmartphone audio : %s", e)
            raise tichy.ServiceUnusable
    
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

    def ringtone(self, ringtype):
        if ringtype == "call":
            logger.info("playing ringtone")
            self.play("/usr/share/sounds/phone_ringing.ogg", 1)
        if ringtype == "message":
            logger.info("playing smstone")
            self.play("/usr/share/sounds/notify_message.mp3")

    def play(self, filepath, loop=0, length=0):
        try:
            self.audio.PlaySound( filepath, loop, length )
        except dbus.DBusException, e:
            logger.exception("play: %s", e)
            assert e.get_dbus_name() == "org.freesmartphone.Device.Audio.PlayerError", \
                                            "wrong error returned"
        else:
            assert False, "PlayerError expected"

