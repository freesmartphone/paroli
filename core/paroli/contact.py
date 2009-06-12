# coding=utf8
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

"""contact module"""

__docformat__ = 'reStructuredText'

import logging
logger = logging.getLogger('core.paroli.contact')

from elementary import Box, Label
from tichy import Item, Text, Service
from tichy.persistance import Persistance
from paroli.tel_number import TelNumber


# TODO: also the Field / Attr thing is good, but it should be a subset
# of a higher level module Struct.


class ContactField(object):
    """Represent a field in a contact class

    When we create a new Contact type, we can decide what fields can
    be used with it. For example a SIM contact will only have a name
    and tel fields.

    typical fields are : name, tel, note...

    A Field is a python descriptor. It means we can declare fields in
    a Contact class, and when we try to access them we will get the
    attribute instead of the field itself.
    """

    def __init__(self, name, type_, requiered=False):
        """Create a new field

        :Parameters:

            name : str
                The name of the field

            type_ : `tichy.Item`
                The requiered type of the field attribute

            requiered : bool
                If set to True then the field is compulsory
        """
        self.name = name
        self.type = type_
        self.requiered = requiered

    def __get__(self, obj, type_=None):
        return obj.attributes[self.name].value

    def __set__(self, obj, value):
        obj.attributes[self.name].value = value

    def __repr__(self):
        return self.name


class ContactAttr(Item):
    """represent an attribute of a contact

    This is different from the field. The filed contains only meta
    information about a contact attribute, the attribute contains the
    value itself.
    """

    def __init__(self, contact, field):
        super(ContactAttr, self).__init__()
        self.contact = contact
        self.field = field

    def get_text(self):
        return self

    def __repr__(self):
        return "%s : %s" % (self.field.name, self.value)

    def __unicode__(self):
        return unicode(self.field.name)

    def view(self, parent, **kargs):
        """Create a view of the Item

        :Parameters:
            `parent` : gui.Widget
                The parent widget the view will be created in

        :Returns: the widget that represents the item
        """
        ret = Box(parent, axis=0, border=0)
        Label(ret, "%s:" % self.field.name)
        if self.value:
            self.value.view(ret)
        return ret

    def __get_value(self):
        return getattr(self.contact, '_attr_%s_' % self.field.name, None)

    def __set_value(self, value):
        value = self.field.type.as_type(value)
        setattr(self.contact, '_attr_%s_' % self.field.name, value)
        if value is not None:
            value.connect('modified', self._on_value_modified)
        self.emit('modified')

    value = property(__get_value, __set_value)

    def _on_value_modified(self, value):
        self.emit('modified')

    def _on_edit(self, action, attr, view):
        assert self.value
        yield self.value.edit(view.window, name=self.field.name)


class Contact(Item):
    """base class for tichy's contacts

    We have to redo this class better. So far a contact can only have
    one backend. The backend method (`import_`) being a class method. If
    we want to have several backends per contacts we need (and should)
    to change that...
    """

    storage = None

    Field = ContactField        # Alias for the ContactField class

    name = ContactField('name', Text, True)
    tel = ContactField('tel', TelNumber)
    fields = [name, tel]

    def __init__(self, **kargs):
        """Create a new contact

        Every contact class can specify the `ContactField` it
        accepts. All the keyword arguments passed to the method will
        be checked to match an available field. If the keyword doesn't
        match, then it is ignored.
        """
        super(Contact, self).__init__()
        self.attributes = dict((x.name, ContactAttr(self, x)) \
                                   for x in self.fields)
        for key, attr in self.attributes.items():
            if key in kargs:
                attr.value = kargs[key]
            attr.connect('modified', self._on_attr_modified)

    def _on_attr_modified(self, attr):
        self.emit('modified')

    def get_text(self):
        """Return the name of the item as a tichy.Text object
        """
        return self.name

    def get_sub_text(self):
        """Return an optional sub text for the item"""
        return getattr(self, 'tel', None)

    def view(self, parent, **kargs):
        """Create a view of the Item

        :Parameters:
            `parent` : gui.Widget
                The parent widget the view will be created in

        :Returns: the widget that represent the item
        """
        return self.name.view(parent, **kargs)

    def _on_copy_to(self, action, contact, view, cls):
        try:
            contact = yield cls.import_(self)
            Service.get('Contacts').add(contact)
        except Exception, ex:
            logger.exception("can't import contact : %s", ex)
            yield Dialog(view.window, "Error", # TODO where does this "Dialog" come from?!?
                               "can't import the contact")

    def delete(self):
        """delete the contact

        This perform the action to delete a contact
        """
        yield None

    def to_dict(self):
        """return all the attributes in a python dict"""
        return dict((str(f.field.name), unicode(f.value)) \
                        for f in self.attributes.values() \
                        if f.value is not None)

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        yield None


class PhoneContact(Contact):
    """Contact that is stored on the phone"""

    storage = 'Phone'

    name = ContactField('name', Text, True)
    tel = ContactField('tel', TelNumber)
    note = ContactField('note', Text)
    tel_type = ContactField('tel_type', Text)
    fields = [name, tel, note, tel_type]

    def __init__(self, **kargs):
        super(PhoneContact, self).__init__(**kargs)
        self.connect('modified', self._on_modified)

    def _on_modified(self, contact):
        logger.info("Phone contact modified %s contact", contact)
        yield self.save()

    @classmethod
    def import_(cls, contact):
        """import a contact into the phone"""
        assert not isinstance(contact, PhoneContact)
        yield PhoneContact(name=contact.name, tel=contact.tel)

    @classmethod
    def save(cls):
        """Save all the phone contacts"""
        logger.info("Saving phone contacts")
        contacts = Service.get('Contacts').contacts
        data = [c.to_dict() for c in contacts if isinstance(c, PhoneContact)]
        Persistance('contacts/phone').save(data)
        yield None

    @classmethod
    def load(cls):
        """Load all the phone contacts

        Return a list of all the contacts
        """
        logger.info("Loading phone contacts")
        ret = []
        data = Persistance('contacts/phone').load()
        if data:
            for kargs in data:
                contact = PhoneContact(**kargs)
                ret.append(contact)
        yield ret

