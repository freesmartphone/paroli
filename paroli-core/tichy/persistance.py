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


"""Persistance module"""

# TODO: turn the save and load methods into a `Tasklet`. Saving into a
#       file can take a lot of time.

import os

#import yaml
#try:
    #from yaml import CLoader as Loader
    #from yaml import CDumper as Dumper
#except ImportError: 
    #from yaml import Loader, Dumper

import logging
try:
	import cPickle as pickle
except:
	import pickle

logger = logging.getLogger('persistance')


class Persistance(object):
    """Use this class to save and load data from file

    All the data will be placed into ~/.tichy directory."""

    base_path = os.path.expanduser('~/.paroli/')

    def __init__(self, path):
        self.path = path

    def _open(self, mod='r'):
        path = os.path.join(self.base_path, self.path)
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            return open(path, mod)
        except IOError, ex:
            logger.warning("can't open file : %s", ex)
            raise

    def save(self, data):
        """Save a data into the file

        :Parameters:

            data
                Any kind of python structure that can be
                serialized. Usually dictionary or list.
        """

	# Save the object to a python pickle:
	# http://docs.python.org/library/pickle.html
        file = self._open('w')
        pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)

    def load(self):
        """Load data from the file

        :Returns: The structure previously saved into the file
        """
        
        try:
            file = self._open()
        except IOError, ex:
            return None

        # Try to load it as a pickle first
        try:
            return pickle.load(file)
        except:
            pass

        # Try to load the legacy format
        import ConfigParser
        parser = ConfigParser.ConfigParser()
        parser.readfp(file)
        
        #return yaml.load(file, Loader=Loader)
        result = []
        
        for s in parser.sections():
            sub_result = {}
            for k, v in parser.items(s):
                #d = [k, v]<<<d
                sub_result[k]=v.decode('utf-8')
            
            result.append(sub_result)
        
        #print result
        return result
        return None
