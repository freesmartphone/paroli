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
import logging
logger = logging.getLogger('core.tichy.persistance')

from os import makedirs
from os.path import expanduser, join, dirname, exists
try:
    import cPickle as pickle
except:
    import pickle


class Persistance(object):
    """Use this class to save and load data from file

    All the data will be placed into ~/.paroli directory."""

    base_path = expanduser('~/.paroli/')

    def __init__(self, path):
        self.path = path
        logger.info("path = %s", path)

    def _open(self, mod='r'):
        path = join(self.base_path, self.path)
        dir = dirname(path)
        if not exists(dir):
            makedirs(dir)
        try:
            return open(path, mod)
        except IOError, ex:
            logger.exception("can't open file : %s", ex)
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
        except IOError, e:
            logger.exception('load %s', e)
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
