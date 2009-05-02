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
        self.window = gui.elm_window(str(title))
        self.window.elm_obj.show()
        self.window.elm_obj.color_set(0, 0, 0, 255)
        self.box = gui.elm_box(self.window.elm_obj)
        self.window.elm_obj.resize_object_add(self.box.elm_obj)
        
        self.label = gui.elementary.Label(self.window.elm_obj)
        self.label.label_set(str(title))
        self.box.elm_obj.pack_end(self.label)
        self.label.size_hint_min_set(440, 50)
        self.label.show()
        
        self.scroller = gui.elm_scroller(self.window)
        self.entry = gui.elementary.Entry(self.window.elm_obj)
        self.entry.entry_set(str(msg))
        self.entry.size_hint_weight_set(1.0, 0.6)
        self.entry.editable_set(False)
        self.entry.show()
        self.scroller.elm_obj.content_set(self.entry)
        
        self.box.elm_obj.pack_end(self.scroller.elm_obj)
        
        self.button = gui.elementary.Button(self.window.elm_obj)
        self.button.label_set("OK")
        self.button.on_mouse_up_add(self._on_ok_clicked)
        self.box.elm_obj.pack_end(self.button)
        self.button.show()
        
        self.window.elm_obj.layer_set(99)
        
        yield tichy.Wait(self, 'done')

    def _on_ok_clicked(self, *args):
        """called when we clock the OK button"""
        self.window.elm_obj.delete()
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
        
        self.error_msgs = tichy.config.getboolean('error_messages','activated', False)
        
        if self.error_msgs or title == "Ussd":
            yield Dialog(parent, title, msg)
        else:
            yield None

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
