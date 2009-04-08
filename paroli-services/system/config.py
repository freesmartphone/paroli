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

import os
import logging
import ConfigParser
import tichy

logger = logging.getLogger('ConfigService')

class ConfigService(tichy.Service):
    service = 'ConfigService'
  
    def __init__(self):
        super(ConfigService, self).__init__()

    @tichy.tasklet.tasklet
    def init(self):
        logger.info('Config service init')
        self.parser = ConfigParser.SafeConfigParser()
        self.base_path = os.path.expanduser('~/.paroli/')
        self.path = "settings/settings"
        logger.info("settings service")
        self.main_cfg = self._read()
        yield "none"    
    
    def _open(self, path, mod='r'):
        compl_path = os.path.join(self.base_path, path)
        dir = os.path.dirname(compl_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            return open(compl_path, mod)
        except IOError, ex:
            logger.warning("can't open file : %s", ex)
            raise

    def _read(self, path=None):
        try:
            compl_path = path or self.path
            file = self._open(compl_path)
            return self.parser.readfp(file)
        except IOError, ex:
            return None
            raise
    
    def get_items(self, section, path=None):
        if path:
            contents = self._read(path)
        else:
            contents = self.main_cfg

        if contents == None:
            ret = None
        elif contents.has_section(section):
            ret = contents.items(section)
        else:
            ret = None
        return ret
        
    def set_item(self, section, option, value, path=None):
        if path:
            file = self._open(path,'w')
        else:
            file = self._open(self.path, 'w')
        
        if not self.main_cfg.has_section(section):
            self.main_cfg.add_section(section)
            
        self.main_cfg.set(section, option, value)
        self.main_cfg.write(file)
        self.main_cfg = self._read()
