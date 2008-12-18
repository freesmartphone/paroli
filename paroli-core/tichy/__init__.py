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

from application import Application, Gadget
from service import Service, ServiceUnusable
import plugins

from list import List, ActorList
from text import Text
from item import Item
from actor import Actor
from image import Image
from time import Time
from persistance import Persistance
import notifications

from dialog import Dialog

mainloop = None
gui = None

def init_gui(backends=None):
    """Initialize tichy gui

    This method will manually set tichy.gui module as the proper gui
    backend.

    This has to be called once before we can import tichy.gui

    :Parameters:

        backends : list | str
            backend name or list of backends names that we want to try
    """
    global mainloop
    global gui

    import logging
    logger = logging.getLogger('')

    backends = backends or ['paroli', 'csdl', 'sdl']  # default backends
    if isinstance(backends, str):
        backends = [backends]

    for backend in backends:
        try:
            if backend == 'csdl':
                import gui
                gui = guic
            elif backend == 'sdl':
                import guip
                gui = guip
            elif backend == 'gtk':
                import guig
                gui = guig
            elif backend == 'etk':
                import guie
                gui = guie
            elif backend == 'paroli':
                import gui_paroli
                gui = gui_paroli
            elif backend == 'edje':
                import gui_edje
                gui = gui_edje
            logger.info("using backend %s", backend)
            sys.modules['tichy.gui'] = gui
            mainloop = gui.EventsLoop()

        except Exception, e:
            logger.warning("can't use backend %s : %s", backend, e)
            if backend == backends[-1]:
                raise
        else:
            break
