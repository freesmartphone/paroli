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
LOGGER = logging.getLogger('Contact')

import tichy
from tel_number import TelNumber

# TODO: Redo the whole contact things. We should have a single contact
# class, no subclass for different backends, instead we have
# ContactStorage classes where we define storage functions.  A contact
# should have any fields (dictionary style), and each storage can
# define which fields are supported.

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


class ContactAttr(tichy.Item):
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
        ret = tichy.gui.Box(parent, axis=0, border=0)
        tichy.gui.Label(ret, "%s:" % self.field.name)
        if self.value:
            self.value.view(ret)
        return ret

    def create_actor(self):
        """Return an actor acting on this item

        :Returns: `tichy.Actor`
        """
        actor = super(ContactAttr, self).create_actor()
        actor.new_action('Edit').connect('activated', self._on_edit)
        return actor

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


class Contact(tichy.Item):
    """base class for tichy's contacts

    We have to redo this class better. So far a contact can only have
    one backend. The backend method (`import_`) being a class method. If
    we want to have several backends per contacts we need (and should)
    to change that...
    """

    storage = None

    Field = ContactField        # Alias for the ContactField class

    name = ContactField('name', tichy.Text, True)
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

    def create_actor(self):
        """Return an actor acting on this contact

        :Returns: `tichy.Actor`
        """
        actor = tichy.Item.create_actor(self)
        actor.new_action("Call").connect('activated', self._on_call)
        actor.new_action("Edit").connect('activated', self._on_edit)
        actor.new_action("Delete").connect('activated', self._on_delete)

        for cls in Contact.subclasses:
            if isinstance(self, cls):
                continue
            import_ = actor.new_action("Copy to %s" % cls.storage)
            import_.connect('activated', self._on_copy_to, cls)

        return actor

    def _on_copy_to(self, action, contact, view, cls):
        try:
            contact = yield cls.import_(self)
            tichy.Service.get('Contacts').add(contact)
        except Exception, ex:
            LOGGER.error("can't import contact : %s", ex)
            yield tichy.Dialog(view.window, "Error",
                               "can't import the contact")

    def _on_call(self, _action, contact, view):
        if not self.tel:
            yield tichy.Dialog(view.window, "Error", "Contact has no tel")
        else:
            caller = tichy.Service.get('Caller')
            yield caller.call(view.window, contact.tel)

    def _on_edit(self, item, contact, view):
        editor = tichy.Service.get('EditContact')
        yield editor.edit(self, view.window)

    def _on_delete(self, item, contact, view):
        try:
            yield contact.delete()
            yield tichy.Service.get('Contacts').remove(contact)
        except Exception, ex:
            LOGGER.error("can't delete contact : %s", ex)
            yield tichy.Dialog(view.window, "Error",
                               "can't delete the contact")

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

    name = ContactField('name', tichy.Text, True)
    tel = ContactField('tel', TelNumber)
    note = ContactField('note', tichy.Text)
    tel_type = ContactField('tel_type', tichy.Text)
    fields = [name, tel, note, tel_type]

    def __init__(self, **kargs):
        super(PhoneContact, self).__init__(**kargs)
        self.connect('modified', self._on_modified)

    def _on_modified(self, contact):
        LOGGER.info("Phone contact modified %s contact", contact)
        yield self.save()

    @classmethod
    def import_(cls, contact):
        """import a contact into the phone"""
        assert not isinstance(contact, PhoneContact)
        yield PhoneContact(name=contact.name, tel=contact.tel)

    @classmethod
    def save(cls):
        """Save all the phone contacts"""
        LOGGER.info("Saving phone contacts")
        contacts = tichy.Service.get('Contacts').contacts
        data = [c.to_dict() for c in contacts if isinstance(c, PhoneContact)]
        tichy.Persistance('contacts/phone').save(data)
        yield None

    @classmethod
    def load(cls):
        """Load all the phone contacts

        Return a list of all the contacts
        """
        LOGGER.info("Loading phone contacts")
        ret = []
        data = tichy.Persistance('contacts/phone').load()
        for kargs in data:
            contact = PhoneContact(**kargs)
            ret.append(contact)
        yield ret


class ContactsService(tichy.Service):
    """Allow to add and get the phone or sim contacts"""

    service = 'Contacts'

    def __init__(self):
        super(ContactsService, self).__init__()
        self.contacts = tichy.List()
        # TODO: the problem here is that when we load the contacts we
        # are going to rewrite them !
        self.contacts.connect('modified', self._on_contacts_modified)

    def _on_contacts_modified(self, contacts):
        yield PhoneContact.save()

    @tichy.tasklet.tasklet
    def init(self):
        """init the service"""
        yield self._load_all()

    @tichy.tasklet.tasklet
    def _load_all(self):
        """load all the contacts from all the sources

        We need to call this before we can access the contacts
        """
        all_contacts = []
        for cls in Contact.subclasses:
            LOGGER.info("loading contacts from %s", cls.storage)
            try:
                contacts = yield cls.load()
                LOGGER.info("Got %d contacts from %s", len(contacts),
                            cls.storage)
            except Exception, ex:
                LOGGER.warning("can't get contacts : %s", ex)
                continue
            assert all(isinstance(x, Contact) for x in contacts)
            all_contacts.extend(contacts)
        self.contacts[:] = all_contacts
        LOGGER.info("Totally got %d contacts", len(self.contacts))

    @tichy.tasklet.tasklet
    def copy_all(self):
        """copy all the contacts into the phone"""
        to_add = []
        for contact in self.contacts:
            if isinstance(contact, PhoneContact):
                continue
            if any([isinstance(c, PhoneContact) for c in \
                        self.find_by_number(contact.tel)]):
                continue
            contact = yield PhoneContact.import_(contact)
            to_add.append(contact)
        self.contacts.extend(to_add)

    def add(self, contact):
        """Add a contact into the contact list"""
        self.contacts.append(contact)

    def remove(self, contact):
        """Remove a contact from the contact list"""
        self.contacts.remove(contact)

    def _new_name(self):
        name = 'new'
        i = 2
        while name in [unicode(c.name) for c in self.contacts]:
            name = "new%d" % i
            i += 1
        return name

    def find_by_number(self, number):
        """Return all the contacts having a given number

        :Parameters:
            number : str
               The number of the contact

        :Returns: list of `Contact`
        """
        return [x for x in self.contacts if x.tel == number]

    def get_by_number(self, number):
        """return the first contacts having a given number, or None"""
        for contact in self.contacts:
            if contact.tel == number:
                return contact
        return None

    def create(self, name=None, **kargs):
        """Create a new `Contact` instance

        This will create a contact using the most appropriate
        storage. (For the moment is is always a `PhoneContact`)

        :Parameters:

            kargs: dict
                The attributes used for the contact. If 'name' is not
                given, a new name will be generated.
        """
        name = name or self._new_name()
        return PhoneContact(name=name, **kargs)
