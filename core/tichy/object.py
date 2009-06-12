# -*- coding: utf-8 -*-
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

"""Object module

This module define the Object class, that provides signal mechanism in
a way similar to gobject.
"""

__docformat__ = 'reStructuredText'

import os

from types import GeneratorType
from tichy.tasklet import Tasklet


class Object(object):
    """This class implements the observer patern

        I could use gobject.GObject instead.  But i think gobject may
        be overkill there... still thinking about it...
    """

    def __new__(cls, *argl, **argk):
        obj = super(Object, cls).__new__(cls)
        obj._listeners = {}
        return obj

    @classmethod
    def path(cls, path=None):
        """return the path of a file situated in the same directory than the
        source code of the object.

        :Parameters:

            `path` : str or None
                The name of the file, if set to None, then return
                the directory of the object.
        """
        # XXX: this path method sucks
        module_str = cls.__module__
        module = __import__(module_str)
        ret = os.path.dirname(module.__file__)
        if path:
            ret = os.path.join(ret, path)
        if os.path.exists(ret):
            return ret
        # If we didn't find the file then we check in the system dir
        for base in ['/usr/tichy', '/usr/share/tichy']:
            ret = os.path.join(base, path)
            if os.path.exists(ret):
                return ret

    @classmethod
    def open(cls, path):
        """Open a file that is located in the same directory than the object
        source code

        :Parameters:

            `path` : str
                The file name
        """
        return open(cls.path(path))

    def connect(self, event, callback, *args):
        """Connect the object to a given event

        This method has the same syntax than the gobject equivalent.

        :Parameters:

            `event` : str
                the name of the vent we connect to

            `callback` : callback method
                the method called when the event is emitted. The first
                argument of the method will be the calling object. All
                arguments passed to the connect method will be passed
                as well

        :Returns: The id of the connection
        """
        return self.connect_object(event, callback, self, *args)

    def connect_object(self, event, callback, obj, *args):
        """Connect an event using a given object instead of self"""
        connection = (callback, obj, args)
        self._listeners.setdefault(event, []).append(connection)
        return id(connection)

    def disconnect(self, oid):
        """remove a connection from the listeners

        :Parameters:

            oid : int
                The id returned by `Object.connect` method
        """
        for listener in self._listeners.itervalues():
            for connection in listener:
                if id(connection) == oid:
                    listener.remove(connection)
                    return

        raise Exception("trying to disconnect a bad id")

    def emit(self, event, *args):
        """Emit a signal

           All the listeners will be notified.

           All extra arguments will be passed to the listeners
           callback method.

           :Parameters:
               `event` : str
                   The name of the event to emit.
        """

        for callback, obj, extra_args in self._listeners.get(event, [])[:]:
            eargs = args + extra_args
            call = callback(obj, *eargs)
            # Now in case the callback is a generator, we turn it into a task
            # This allow us to directly connect to generators
            if type(call) is GeneratorType:
                Tasklet(generator=call).start()

    def monitor(self, obj, event, callback, *args):
        """connect an object to a callback, and automatically disconnect it
        when this object is destroyed.

        WARNING: This is still experimental, and should only be used
        with objects that have a 'destroyed' signal.
        """
        connection = obj.connect(event, callback, *args)

        def on_destroyed(self, obj, connection):
            obj.disconnect(connection)
        self.connect('destroyed', on_destroyed, obj, connection)
