#    Paroli
#
#    copyright 2008 OpenMoko
#
#    This file is part of Paroli.
#
#    Paroli is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paroli is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#    You should have received a copy of the GNU General Public License


__docformat__ = 'reStructuredText'

"""Dialog service"""

import logging
logger = logging.getLogger('Dialog')

import tichy
import tichy.gui as gui

class DialogService(tichy.Service):
    """Service that can be used to show dialog to the user"""
    service = 'Dialog'

    @tichy.tasklet.tasklet
    def dialog(self, parent, title, msg):
        """Show a dialog and wait for the user to close it

        :Parameters:

            parent : gui.Widget | None
                The parent widget. If None the dialog has no parent.

            title : unicode
                The title of the dialog

            msg : unicode
                The message
        """
        logger.info("show %s dialog : %s", title, msg)
        # XXX: implement the dialog here
        yield None

    @tichy.tasklet.tasklet
    def error(self, parent, msg):
        """Show an error message and wait for the user to close it

        :Paramters:

            parent : gui.Widget | None
                The parent widget. If None the dialog has no parent.

            msg : unicode
                The message
        """
        yield self.dialog(parent, "Error", msg)
