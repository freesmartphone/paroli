#    Tichy
#    copyright 2008 Guillaume Chereau (charlie@openmoko.org)
#
#    This file is part of Tichy.
#
#    Tichy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tichy is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Tichy.  If not, see <http://www.gnu.org/licenses/>.

__docformat__ = 'reStructuredText'

"""tichy package"""

import sys

from tichy.object import Object
from tasklet import Tasklet, Wait, WaitFirst

from application import Gadget
from service import Service
import plugins

from list import List
from text import Text
from int import Int
from item import Item
from ttime import Time
from persistance import Persistance
import notifications
import config
from settings import Setting

mainloop = None # set from outside in this singleton

