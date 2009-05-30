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

import os
import logging
import ConfigParser
import tichy

logger = logging.getLogger('services.misc.config')

class ConfigService(tichy.Service):

    service = 'Config'
  
    def __init__(self):
        super(FallbackConfigService, self).__init__()

    @tichy.tasklet.tasklet
    def init(self):
        logger.info('Config service init')
        self.main_cfg = ConfigParser.SafeConfigParser()
        self.base_path = os.path.expanduser('~/.paroli/')
        self.path = "settings/settings"
        compl_path = os.path.join(self.base_path, self.path)
        dir = os.path.dirname(compl_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.main_cfg.read(compl_path)
        logger.info("settings service %s", compl_path)
        yield "none"    
    
    def _open(self, path, mod='r'):
        compl_path = os.path.join(self.base_path, path)
        dir = os.path.dirname(compl_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            return open(compl_path, mod)
        except IOError, ex:
            logger.exception("can't open file : %s", ex)
            raise

    def _read(self, path=None):
        try:
            compl_path = path or self.path
            file = self._open(compl_path)
            return self.parser.readfp(file)
        except IOError, e:
            logger.exception("can't use freesmartphone IdleNotifier service : %s", e)
            return None
            raise
    
    def get_items(self, section, path=False):
        try:
            contents = self.main_cfg

            logger.debug("sections: %s", contents.sections())

            if contents == None:
                ret = None
            elif contents.has_section(section):
                ret = contents.items(section)
            else:
                logger.info("doesn't have section %s", section)
                logger.info("valid sections are %s", contents.sections())
                ret = None
            return ret
            
        except Exception, e:
            logger.exception("can't get item : %s", e)
        
    def set_item(self, section, option, value, path=False):
        #if path:
            #file = self._open(path,'w')
        #else:
        try:
            path = self.base_path + self.path
            file = open(path, 'w+')
            
            
            logger.info("parsing done")
            if not self.main_cfg.has_section(section):
                self.main_cfg.add_section(section)
                
            self.main_cfg.set(section, option, value)
            self.main_cfg.write(file)
            file.close()
        except Exception, e:
            logger.exception("can't set item : %s", e)
        #self.main_cfg = self._read()
        logger.debug('set_item %s', self.main_cfg.sections())
