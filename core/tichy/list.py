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

__docformat__ = 'reStructuredText'

from tichy.item import Item
from tichy.service import Service


# XXX: We need to remove the removed, appended and cleared signal


class List(list, Item):
    """Base class for list

    It is better to use this class instead of python list in the case
    we want to monitor the list modifications.

    Signals
        'modified' : emitted any time the list has been modified
        'cleared' : emitted when the list has been cleared
        'removed' : emitted when an item has been removed
        'appended' : emitted when an item has been appened
    """

    def __init__(self, values=[]):
        list.__init__(self, values)
        Item.__init__(self)
        assert hasattr(self, '_Object__listeners'), self
        self.sort()

    def clear(self):
        """Remove all the items from a list"""
        self[:] = []
        self.emit('cleared')
        self.emit('modified')

    def append(self, value):
        """Add a new item in the list"""
        # This assertion is not true anymore ?
        # assert isinstance(value, Item), type(value)
        list.append(self, value)
        self.emit('appended', value)
        self.emit('modified')

    def insert(self, index, value):
        """insert an item into the list at a given position

        :Parameters:
            index : int
                The index where we insert the item
            value
                The inserted value
        """
        list.insert(self, index, value)
        self.emit('inserted', index, value)
        self.emit('modified')

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.emit('modified')

    def extend(self, values):
        list.extend(self, values)
        self.emit('modified')

    def remove(self, value):
        """Remove one item from the list"""
        list.remove(self, value)
        self.emit('removed', value)
        self.emit('modified')

    def remove_group(self, value_list):
        """Remove group of items from the list"""
        for value in value_list:
            list.remove(self, value)
        self.emit('removed', value_list[0])
        self.emit('modified')
  
    def sort(self, *args, **kargs):
        """Sort the list inplace"""
        list.sort(self, *args, **kargs)
        self.emit('modified')
