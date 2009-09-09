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

from tichy.text import Text
from tichy.service import Service


class TelNumber(Text):
    """Telephone number class"""

    def __init__(self, text='', **kargs):
        """Create a new TelNumber instance

        :Parameters:

            text : `Text`
                The number itself
        """

        super(TelNumber, self).__init__(text, **kargs)
        # This is the text that is used for the view of the number It
        # can be either the number, either the name of the contact
        # TODO: we could not do like this but instead have the
        # get_text method return a basestring object and then connect
        # the actor view to the modified signal
        self.view_text = Text(text)
        self.connect('modified', TelNumber.update_view_text)

    def is_emergency(self):
        """return True is the number is an emergency one"""
        return self.value == '112'

    def get_contact(self):
        """Return the `Contact` that has this number

        :Returns: `Contact` | None
        """
        contacts_service = Service.get('Contacts')
        return contacts_service.get_by_number(self.value)

    def get_text(self):
        self.update_view_text()
        return self.view_text

    def update_view_text(self):
        # We check if the number is from a contact.  If so we set the
        # view text
        contact = self.get_contact()
        if contact:
            self.view_text.value = contact.get_text()
        else:
            self.view_text.value = self.value

class ListSettingObject(object):

    def __init__(self, name, action):
        self.name = name
        self.action = action

