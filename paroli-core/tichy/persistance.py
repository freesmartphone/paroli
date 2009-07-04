# -*- coding: utf-8 -*-
#    Tichy
#
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#    copyright 2009 Mirko Lindner (mirko@openmoko.org)
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


"""Persistance module"""

# TODO: turn the save and load methods into a `Tasklet`. Saving into a
#       file can take a lot of time.

import os

import logging
try:
    import cPickle as pickle
except:
    import pickle

logger = logging.getLogger('persistance')


class Persistance(object):
    """Use this class to save and load data from file

    All the data will be placed into ~/.paroli directory."""

    base_path = os.path.expanduser('~/.paroli/')

    def __init__(self, path):
        self.path = path
        logger.info("path = %s", str(path))

    def _open_readonly(self):
        path = os.path.join(self.base_path, self.path)
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if os.path.isfile(path):
            try:
                f = open(path, 'r')
                return f
            except IOError, ex:
                logger.warning("can't open file : %s, path: %s", ex, path)
                return None
        return None
        
    def _open_write(self):
        path = os.path.join(self.base_path, self.path)
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            if os.path.isfile(path): self._backup(path)
            f = open(path, 'w')
            return f
        except IOError, ex:
            logger.warning("can't open file : %s, path: %s", ex, path)
            raise
            

    def _backup(self, path):
        """Make automatic backups of everything (contacts, sms, etc)"""
        import time
        
        # We need to open the file ourselve, because the mode can be 'w', 
        # as in the case of 'calls/logs'
        f = open(path, 'r')
        file_content = f.read()
        f.close()
            
        # create backup dir
        (dir, filename) = os.path.split(path)
        dir_backup = os.path.join(dir, 'backup')
        if not os.path.exists(dir_backup):
            os.makedirs(dir_backup)
        # save to filename-currenttime format
        curtime = str(int(time.time()))
        out_filename = os.path.join(dir_backup, filename+"-"+curtime)
        out_file = open(out_filename, 'w')
        out_file.write(file_content)
        out_file.flush()
        out_file.close()
        
        
    def save(self, data):
        """Save a data into the file

        :Parameters:
            data
                Any kind of python structure that can be
                serialized. Usually dictionary or list.
        """
        self._save_pickle(data)
        
    def _save_pickle(self, data):
        # Save the object to a python pickle:
        # http://docs.python.org/library/pickle.html
        try:
            file = self._open_write()
            pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)
            file.flush()
            file.close()
        except:
            logger.exception("The pickle save was unsuccessful")

    def _load_pickle(self, file):
        """Load data from a pickle file"""
        content = None
        try:
            content = pickle.load(file)
        except IOError, ex:
            pass
        return content

    def _load_ini(self, file):
        """Load data from a .ini (configuration) file """
        import ConfigParser
        parser = ConfigParser.ConfigParser()
        try:
            parser.readfp(file)
        except:
            return None
        
        result = []
        for s in parser.sections():
            sub_result = {}
            for k, v in parser.items(s):
                #d = [k, v]<<<d
                sub_result[k]=v.decode('utf-8')

            result.append(sub_result)
        return result
    
    def load(self):
        """Load data from the file

        :Returns: The structure previously saved into the file
        """
        
        file = self._open_readonly()
        if not file: return None

        # Try to load it as a pickle first
        content = self._load_pickle(file)
        if not content:
            # Try to load it as .ini config file next
            # if file.tell(): file.seek(0) # after successful pickle reading 
            # the current file position is set at the end. (but we should never 
            # get here in that case)
            content = self._load_ini(file)
        file.close()
        return content
