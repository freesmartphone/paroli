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

"""
Define the Actor and Action classes

In tichy everything is an Item (contact, phone number, text, etc...)
Somethime we need to let the user act on an Item. To do this we can
use the Actor class. an Actor is an item that represents an item and a
list of actions that we can perform on this item.

For example, if `contact` is a Contact Item, We want to provide a way
for the user to perform a few action on the contacts (the default
actions beeing 'Call' and 'Edit'.

actor = contact.create_actor()
actor.view(parent)

If we want to add some specific actions to the actor, we can use the
new_action method :

def on_my_action(item, contact, view):
    print 'my action on', contact
actor.new_action('my-action-name').connect('activated', on_my_action)

An action can also have sub-actions, this is useful for creating a
tree of actions To create sub-actions just use the new_action on an
Action instance.
"""

import tichy
from tichy.object import Object
from tichy.application import Application
from tichy.tasklet import Wait, WaitFirst, Tasklet
from tichy.service import Service


class Action(Object):
    """ The Action class
    """

    def __init__(self, actor, name):
        """Create a new action into `actor`.

        You shouldn't call this method, but use the Actor.new_action
        method instead.

        :Parameters:

            actor : `Actor`
                the parent actor

            name : str
                the name of the action
        """
        super(Action, self).__init__()
        self.actor = actor
        self.name = name
        actor.add(self)
        self.sub_actor = None

    def activate(self, view=None):
        """trigger the action

        :Parameters:

            view : gui.Widget
                the widget from wich the action was activated.  It is
                useful to retreive the window if we want to start new
                applications
        """
        if self.sub_actor:
            # This mean that this action is in fact a menu of other
            # actions...  The sub actions are into a single actor, so
            # we can just ask the Design To do whatever is needed to
            # select this actor...
            design = Service('Design')
            design.select_actor(self.sub_actor, view)
        else:
            self.emit('activated', self.actor.item, view)

    def new_action(self, name):
        """Create a sub action of the action"""
        if not self.sub_actor:
            self.sub_actor = Actor(self)
        return self.sub_actor.new_action(name)


class Actor(tichy.Item):
    """Special item that represent a list of action on an item OR an Item
    class

    It is very usefull, because it abstract all the mechanism to
    select an action on an item.  You just need to create a actor on
    an object, maybe add a few specific action depending on the
    context, and then you add a view of this actor in your gui, and
    that's it.
    """

    def __init__(self, item):
        """Create a new Actor on an given Item

        You shouldn't call this directly but use the
        Item.create_actor() method

        :Parameters:

            item : `Item`
                The item the actor represents
        """
        super(Actor, self).__init__()
        self.item = item
        self.actions = []
        self.default_action = None

    def get_text(self):
        return self.item.get_text()

    def get_sub_text(self):
        return self.item.get_sub_text()

    def add(self, action):
        """Don't call this method, it is already called in Action.__init__"""
        self.actions.append(action)

    def new_action(self, name):
        """Create a new action in the Actor

        :Parameters:

            name : str
                the name of the action
        """
        return Action(self, name)

    def clear(self):
        del self.actions[:]

    def view(self, parent, **kargs):
        """Create a view of the Actor in a parent widget.
        """
        # The design service in in charge of doing it
        design = Service('Design')
        return design.view_actor(parent, self, **kargs)


class ChoicesApp(Application):
    # XXX: what is this thing doing here ?

    def run(self, parent, name, *choices):
        from ..gui import Box, Button, Label, Window, Scrollable

        window = Window(parent)
        frame = self.view(window, title=name)
        scrollable = Scrollable(frame, axis=1)
        box = Box(scrollable, axis=1)
        buttons = []
        for choice in choices:
            button = Button(box)
            Label(button, choice)
            buttons.append(button)

        ret = yield WaitFirst(*[Wait(b, 'clicked') for b in buttons])
        window.destroy()
        yield ret[0]
