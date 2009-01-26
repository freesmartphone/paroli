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
#    along with Tichy.  If not, see <http://www.gnu.org/licenses/>.

import dbus

import tichy
from tichy.tasklet import WaitDBus

import logging
logger = logging.getLogger('audio')

class FSOAudio(tichy.Service):

    service = 'Audio'

    def __init__(self):
        super(FSOAudio, self).__init__()
        logger.info("connecting to freesmartphone.GSM dbus audio interface")
        try:
            # We create the dbus interfaces to org.freesmarphone
            bus = dbus.SystemBus(mainloop=tichy.mainloop.dbus_loop)
            self.bus_object = bus.get_object('org.freesmartphone.ogsmd',
                                      '/org/freesmartphone/GSM/Device')
            self.audio = dbus.Interface(self.bus_object,
                                          'org.freesmartphone.GSM.Device')

        except Exception, e:
            logger.warning("can't use freesmartphone audio : %s", e)
            self.audio = None
            raise tichy.ServiceUnusable
        
        self.muted = 0

    @tichy.tasklet.tasklet
    def init(self):
        if self.audio != None:
            self.mic_state = self.get_mic_status()
            self.speaker_volume = self.get_speaker_volume()
        
        yield self._do_sth()
        
    def _do_sth(self):
        pass
        
    def get_mic_status(self):
        return self.audio.GetMicrophoneMuted()
        
    def set_mic_status(self, val):
        if self.muted != 1:
            self.audio.SetMicrophoneMuted(val)
    
    def get_speaker_volume(self):
        return self.audio.GetSpeakerVolume()
        
    def set_speaker_volume(self, val):
        if self.muted != 1:
            self.audio.SetSpeakerVolume(val)
        
    def audio_toggle(self):
      if self.audio != None:
          if self.muted == 0:
              self.muted = 1
              self.audio.SetMicrophoneMuted(True)
              logger.info(self.get_mic_status())
              # Notice: this does in no way affect the ringtone volume of an incoming call
              self.audio.SetSpeakerVolume(0)
              logger.info(self.get_speaker_volume())
          elif self.muted == 1:
              self.audio.SetMicrophoneMuted(self.mic_state)
              self.audio.SetSpeakerVolume(self.speaker_volume)
              self.muted = 0
          return 0
      else:
          return 1

class ParoliAudio(tichy.Service):

    service = 'Audio'
    name = 'Test'

    def __init__(self):
        
        self.audio = None        
        self.muted = 0

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
        return 100
        
    def set_speaker_volume(self, val):
        if self.muted != 1:
            pass
        
    def audio_toggle(self):
        return 0