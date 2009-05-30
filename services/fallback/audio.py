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

import tichy

import logging
logger = logging.getLogger('services.fallback.audio')

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

