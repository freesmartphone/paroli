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

# Set to true if we register experimental Items
EXPERIMENTAL = False

# Check the globale options for experimental support
if hasattr(sys.modules['__main__'], 'options'):
    options = sys.modules['__main__'].options
    if getattr(options, 'experimental', None):
        EXPERIMENTAL = True


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
                return
            if issubclass(base, Item):
                if cls.experimental and not EXPERIMENTAL:
                    return
                base.subclasses.append(cls)


class Item(tichy.Object):
    """Base class for all items.

       Item are used to separate the data from there view.  Every item
       has a view method that can generate of view of itself.  Items
       also need to expose a set of minimal information that can be
       used by the Design service. Those information are:
       - a name
       - an optional icon

       The subclasses class attribute of an Item class is a list of
       all its subclasses.

       An Item can also create an `Actor` item acting on itself.
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

    def __init__(self):
        super(Item, self).__init__()

    def view(self, parent, **kargs):
        """Create a view of the Item

        :Parameters:
            `parent` : gui.Widget
                The parent widget the view will be created in

        :Returns: the widget that represents the item
        """
        raise NotImplementedError

    def edit(self, parent):
        """return a tasklet that will edit the item value

        :Parameters:
            `parent` : gui.Widget
                The parent widget the view will be created in

        :Returns: a `tichy.Tasklet` that sill start the editing task
        """
        # TODO: now that we have a proper Actor system, we should be
        # able to remove this ?
        raise NotImplementedError

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

    def create_actor(self):
        """Return an actor acting on this item

        :Returns: `tichy.Actor`
        """
        from tichy.actor import Actor
        return Actor(self)

    def __unicode__(self):
        return unicode(self.get_text())

    def __repr__(self):
        return repr(self.get_text())
