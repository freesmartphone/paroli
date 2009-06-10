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

"""Item class module"""

__docformat__ = "restructuredtext en"

import sys

import tichy


class ItemMetaClass(type):
    """The Meta class for Item class

    It is there so that we register every Item classes automatically
    """

    def __init__(cls, name, bases, dict):
        # put the Item class in its parent subclass list
        cls.subclasses = []
        super(ItemMetaClass, cls).__init__(name, bases, dict)
        for base in bases:
            if base is tichy.Object:
                continue
            while issubclass(base, tichy.item.Item):
                base.subclasses.append(cls)
                base = base.__base__


class Item(tichy.Object):
    """Base class for all items.

       The subclasses class attribute of an Item class is a list of
       all its subclasses.
    """
    __metaclass__ = ItemMetaClass

    subclasses = [] # This contains the list of all subclasses of this
                    # class It is automaticaly filled by the meta
                    # class

    name = None                 #: The name of the item

    icon = None

    experimental = None

    @classmethod
    def find_by_name(cls, name):
        """Return the first class of that type that has the given name

        :Parameters:
            name : str
                the name of the class we are looking for
        """
        for subclass in cls.subclasses:
            if subclass.name == name:
                return subclass
        raise KeyError(name)

    def get_text(self):
        """Return the name of the item as a tichy.Text object

        By default this method will check for the 'name' attribute of
        the item.  You need to override it for special item name.

        :Returns: `tichy.Text` object
        """
        return tichy.Text(self.name)

    def get_sub_text(self):
        """Return an optional sub text for the item

        :Returns: `tichy.Text` | None
        """
        return None

    def __unicode__(self):
        return unicode(self.get_text())

    def __repr__(self):
        return repr(self.get_text())
