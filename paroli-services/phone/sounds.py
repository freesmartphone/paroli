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
#    along with paroli.  If not, see <http://www.gnu.org/licenses/>.

import dbus

import tichy
from tichy.tasklet import WaitDBus, WaitDBusName

import logging
logger = logging.getLogger('sounds')

class FallbackSoundsService(tichy.Service):

    service = 'Sounds'
    name = 'Fallback'

    def __init__(self):
        super(FallbackSoundsService, self).__init__()

    @tichy.tasklet.tasklet
    def init(self):
        logger.info('init')
        try:
            yield tichy.Service.get('GSM').wait_initialized()
            yield tichy.Service.get('Config').wait_initialized()
            self.config_service = tichy.Service.get('Config')
            self.audio_service = tichy.Service.get('Audio')
            self.vibra_service = tichy.Service.get('Vibrator')
            self.values = self.config_service.get_items("sounds")
            if self.config_service.get_items("sounds") == None:
                    self.config_service.set_item('sounds', "ringtone_file", "/usr/share/sounds/phone_ringing.ogg")
                    self.config_service.set_item('sounds', "smstone_file", "/usr/share/sounds/alarm.wav")
                    self.config_service.set_item('sounds', "callvibra", "1")
                    self.config_service.set_item('sounds', "smsvibra", "1")
            
            self.values = dict(self.config_service.get_items("sounds"))
            logger.info("sounds service active")
                
        except Exception, e:
            logger.exception("can't use sounds service : %s", e)
        
        yield None
        
    def call(self, *arg, **kargs):
        prefs = tichy.Service.get('Prefs')
        if prefs["phone"]["ring-volume"] != 0:
            self.audio_service.play(self.values["ringtone_file"], 1)
        if prefs["phone"]["ring-vibration"] == 1:
            self.vibra_service.IncomingCall()
            
    def Message(self, *arg, **kargs):
        prefs = tichy.Service.get('Prefs')
        if prefs["phone"]["message-volume"] != 0:
            self.audio_service.play(self.values["smstone_file"])
        if prefs["phone"]["message-vibration"] == 1:
            self.vibra_service.IncomingSMS()
            
    def Stop(self, *args, **kargs):
        try:
            self.audio_service.stop_all_sounds()
        except Exception, e:
            logger.exception("got error in Stop %s", str(e))
        try:
            self.vibra_service.stop()
        except Exception, e:
            logger.exception("got error in Stop %s", str(e))

