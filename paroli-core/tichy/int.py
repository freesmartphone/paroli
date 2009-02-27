#    Paroli
#
#    copyright 2008 OpenMoko
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

__docformat__ = 'reStructuredText'

from item import Item

class Int(Item):
    """Base class for all integer in tichy

    Signals:
        "modified": emitted when the integer has been modified
    """

    def __init__(self, value=0):
        """Create a new integer instance

        :Parameters:

            value : int
                The initial value of the integer
        """
        super(Int, self).__init__()
        self.__value = int(value)

    @classmethod
    def as_type(cls, value):
        """Return an `Int` instance from a given value
        """
        if isinstance(value, cls):
            return value
        if value is None:
            return value
        return cls(value)

    def __get_value(self):
        return self.__value

    def __set_value(self, v):
        self.__value = int(v)
        self.emit('modified')

    value = property(__get_value, __set_value)

    def __int__(self):
        return self.__value

    def __repr__(self):
        return str(self.__value)

    def __cmp__(self, o):
        return cmp(self.__value, int(o))
