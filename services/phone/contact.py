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
logger = logging.getLogger('Contact')

import tichy
from paroli.contact import Contact, PhoneContact

# TODO: Redo the whole contact things. We should have a single contact
# class, no subclass for different backends, instead we have
# ContactStorage classes where we define storage functions.  A contact
# should have any fields (dictionary style), and each storage can
# define which fields are supported.


class FallbackContactsService(tichy.Service):
    """Allow to add and get the phone or sim contacts"""

    service = 'Contacts'
    name = 'Fallback'

    def __init__(self):
        super(FallbackContactsService, self).__init__()
        self.contacts = tichy.List()
        # TODO: the problem here is that when we load the contacts we
        # are going to rewrite them !
        self.contacts.connect('modified', self._on_contacts_modified)
        # For optimization we keep a map of number to contact
        self._number_to_contact = {}

    def _on_contacts_modified(self, contacts):
        yield PhoneContact.save()
        # update the map of number to contact
        self._number_to_contact = \
            dict((str(x.tel), x) for x in self.contacts)

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
            logger.info("loading contacts from %s", cls.storage)
            try:
                contacts = yield cls.load()
                logger.info("Got %d contacts from %s", len(contacts),
                            cls.storage)
            except Exception, ex:
                logger.exception("can't get contacts : %s", ex)
                continue
            assert all(isinstance(x, Contact) for x in contacts)
            all_contacts.extend(contacts)
        self.contacts[:] = all_contacts
        logger.info("Totally got %d contacts", len(self.contacts))

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
        return self._number_to_contact.get(str(number), None)

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
