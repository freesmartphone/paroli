# -*- coding: utf-8 -*-
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

import tichy
from paroli.tel_number import TelNumber
from contact import Contact

import logging
logger = logging.getLogger('core.paroli.sim')

class PINError(Exception):
    def __init__(self, pin):
        super(PINError, self).__init__("wrong PIN : %s" % pin)


class SIMContact(Contact):
    storage = 'SIM'

    name = Contact.Field('name', tichy.Text, True)
    tel = Contact.Field('tel', TelNumber)
    fields = [name, tel]

    def __init__(self, sim_index=None, **kargs):
        super(SIMContact, self).__init__(sim_index=sim_index, **kargs)
        self.sim_index = sim_index
        self.icon = 'pics/sim.png'

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        assert not isinstance(contact, SIMContact)
        sim = tichy.Service.get('SIM')
        ret = yield sim.add_contact(contact.name, contact.tel)
        yield ret

    def delete(self):
        sim = tichy.Service.get('SIM')
        yield sim.remove_contact(self)

    @classmethod
    @tichy.tasklet.tasklet
    def load(cls):
        sim = tichy.Service.get('SIM')
        yield sim.wait_initialized()
        ret = yield sim.get_contacts()
        yield ret

