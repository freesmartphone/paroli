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
import calendar
import logging

import tichy


logger = logging.getLogger('')

class Time(tichy.Item):
    """Item that represent a time

    Internally the value is stored as a floating point number
    expressed in seconds since the epoch, in UTC (that is the value
    returned by time.time() )
    """

    def __init__(self, value=None):
        self.timeshift = None
        # TODO: maybe deprecate creating time from a string ?
        if isinstance(value, basestring):
            # We check for timezone information (e.g '+0800')
            if value[-5] == '+':
                self.timeshift = value[-5:]
                value = value[:-5].strip()
                value = time.mktime(time.strptime(value))
            else:
                # if we don't have a timezone, then we assume UTC time
                value = float(calendar.timegm(time.strptime(value)))
        self.__value = value or time.time()
        assert isinstance(self.__value, float)

    @property
    def value(self):
        return self.__value

    @classmethod
    def as_type(self, value):
        if isinstance(value, Time):
            return value
        return Time(value)

    def __str__(self):
        return time.asctime(time.gmtime(self.__value))

    def local_repr(self):
        return time.asctime(time.localtime(self.__value))

    def simple_repr(self):
        if self.__is_the_same_day():
            return self.time_repr()
        else:
            return self.date_repr()

    def __is_the_same_day(self):
        now = time.localtime()
        t = time.localtime(self.__value)
        if now[0] == t[0] and now[1] == t[1] and now[2] == t[2]:
            return True
        return False

    def time_repr(self):
        t = time.localtime(self.__value)
        repr = str(t[3]) + ":" + str(t[4])
        return repr

    def date_repr(self):
        t = time.localtime(self.__value)
        repr = str(t[1]) + "/" + str(t[2])
        return repr
        

    def get_text(self):
        return tichy.Text(self.local_repr())

    def __cmp__(self, other):
        if isinstance(other, Time):
            other = other.__value
        return cmp(self.__value, other)
