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

__docformat__ = 'reStructuredText'

from tichy.item import Item
from tichy.service import Service


class Text(Item):
    """Base class for all text in tichy

    Signals:
        "modified": emitted when the text has been modified
    """

    def __init__(self, value=""):
        """Create a new text instance

        :Parameters:

            value : unicode
                The initial value of the text
        """
        super(Text, self).__init__()
        self.__value = unicode(value)

    @classmethod
    def as_type(cls, value):
        """Return a `Text` instance from a given value

        This will convert the value only if it not already a `Text`
        instance.
        """
        if isinstance(value, cls):
            return value
        if value is None:
            return value
        return cls(unicode(value))

    def get_text(self):
        return self

    def __get_value(self):
        return self.__value

    def __set_value(self, v):
        self.__value = unicode(v)
        self.emit('modified')

    value = property(__get_value, __set_value)

    def __repr__(self):
        return self.__value.encode('ascii', 'replace')

    def __unicode__(self):
        return self.__value

    def __len__(self):
        return len(self.__value)

    def __getitem__(self, index):
        return self.__value[index]

    def __cmp__(self, o):
        return cmp(self.__value, unicode(o))
