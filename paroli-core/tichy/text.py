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

    def __init__(self, value="", editable=False):
        """Create a new text instance

        :Parameters:

            value : unicode
                The initial value of the text

            editable : bool
                If True then the text will be editable. Than means
                than the view of the text should provide a way to edit
                the text.
        """
        super(Text, self).__init__()
        self.__value = unicode(value)
        self.editable = editable

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

    def input_method(self):
        return None

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

    def view(self, parent, editable=None, **kargs):
        """Create a view of the text

        :Parameters:

            parent : gui.Widget
                The parent widget we create the view in

            editable : bool or None
                If True then the view will be editable, if False it
                won't be. If set to None it will use the value
                provided in the `__init__` method.
        """
        from .gui import Label, Edit
        editable = editable if editable is not None else self.editable
        if not editable:
            ret = Label(parent, self.__value, **kargs)
        else:
            ret = Edit(parent, item=self, **kargs)

        connection = self.connect('modified', Text.on_modified, ret)
        ret.connect('destroyed', self.on_view_destroyed, connection)
        return ret

    def edit(self, window, **kargs):
        """return a `Tasklet` that can be used to edit the widget"""
        # first we get the appropriate TextEdit Service
        text_edit = Service('TextEdit')
        # Then we call the service with our text
        return text_edit.edit(
            window, self, input_method=self.input_method(), **kargs)

    def on_modified(self, view):
        view.text = self.__value

    def on_view_destroyed(self, view, connection):
        self.disconnect(connection)

    def create_actor(self):
        from actor import Actor
        ret = Actor(self)

        def on_edit(actor, item, view):
            yield item.edit(view.window)

        ret.new_action("Edit").connect('activated', on_edit)
        return ret
