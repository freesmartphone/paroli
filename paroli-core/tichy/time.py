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

from __future__ import absolute_import

import time

import tichy


class Time(tichy.Item):
    """Item that represent a time"""

    def __init__(self, value=None):
        if isinstance(value, str):
            value = time.strptime(value)
        self.__value = value or time.gmtime()

    @classmethod
    def as_time(self, value):
        if isinstance(value, Time):
            return value
        return Time(value)

    def __str__(self):
        return time.asctime(self.__value)

    def get_text(self):
        return tichy.Text(str(self))

    def view(self, parent, **kargs):
        return self.get_text().view(parent, **kargs)

    def __cmp__(self, other):
        if isinstance(other, Time):
            other = other.__value
        return cmp(self.__value, other)
