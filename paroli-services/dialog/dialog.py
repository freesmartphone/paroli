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
import tichy.gui_paroli as gui

# TODO: replace the etk code by something based on Edje

class Dialog(tichy.Application):
    """Dialog application

    This application does nothing but show a message on the screen
    """
    def run(self, parent, title, msg):
        """Create an etk window and show the message"""
        import etk
        self.window = etk.Window(w=480, h=640)
        box = etk.VBox()
        self.window.add(box)
        title_label = etk.Label(title)
        box.add(title_label)
        msg_label = etk.Label(msg)
        box.add(msg_label)
        button = etk.Button()
        box.add(button)
        ok_label = etk.Label("OK")
        button.add(ok_label)
        self.window.show_all()
        button.connect('clicked', self._on_ok_clicked)
        yield tichy.Wait(self, 'done')

    def _on_ok_clicked(self, *args):
        """called when we clock the OK button"""
        self.window.destroy()
        self.emit('done')


class DialogService(tichy.Service):
    """Service that can be used to show dialog to the user"""
    service = 'Dialog'

    @tichy.tasklet.tasklet
    def dialog(self, parent, title, msg, *args):
        """Show a dialog and wait for the user to close it

        :Parameters:

            parent : gui.Widget | None
                The parent widget. If None the dialog has no parent.

            title : unicode
                The title of the dialog

            msg : unicode
                The message
        """
        assert isinstance(msg, basestring)
        msg = msg % args
        logger.debug("show %s dialog : %s", title, msg)
        yield Dialog(parent, title, msg)

    @tichy.tasklet.tasklet
    def error(self, parent, msg, *args):
        """Show an error message and wait for the user to close it

        :Paramters:

            parent : gui.Widget | None
                The parent widget. If None the dialog has no parent.

            msg : unicode
                The message
        """
        yield self.dialog(parent, "Error", msg, *args)
