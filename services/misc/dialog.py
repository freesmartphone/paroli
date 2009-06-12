# -*- coding: utf-8 -*-
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
logger = logging.getLogger('services.misc.dialog')

import tichy
from paroli import gui

# TODO: replace the etk code by something based on edje

class Dialog(tichy.Application):
    """Dialog application

    This application does nothing but show a message on the screen
    """
    def run(self, parent, title, msg, option1=None, option2=None):
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
        
        if option2 == None:
        
            self.button = gui.elementary.Button(self.window.elm_obj)
            label_text = option1 or "OK"
            self.button.label_set(label_text)
            self.button.on_mouse_up_add(self._on_ok_clicked)
            self.box.elm_obj.pack_end(self.button)
            self.button.show()
        else:
            self.box2 = gui.elm_box(self.window.elm_obj)
            self.box2.elm_obj.horizontal_set(True)
            self.box.elm_obj.pack_end(self.box2.elm_obj)
            self.button1 = gui.elementary.Button(self.window.elm_obj)
            self.button1.label_set(option1)
            self.button1.name_set(option1)
            self.button2 = gui.elementary.Button(self.window.elm_obj)
            self.button2.label_set(option2)
            self.button2.name_set(option2)
            self.box2.elm_obj.pack_end(self.button1)
            self.box2.elm_obj.pack_end(self.button2)
            
            self.button1.show()
            self.button1.on_mouse_up_add(self._on_clicked)
            self.button2.on_mouse_up_add(self._on_clicked)
            self.button2.show()
        
        self.window.elm_obj.layer_set(99)
        
        self.val = None
        
        yield tichy.Wait(self, 'done')
        logger.info("self.val = %s", self.val)   
        self.window.elm_obj.delete()
        yield self.val

    def _on_clicked(self, *args):
        self.val = args[0].name_get()
        logger.debug('_on_clicked %s %s', self.val, args[0], )
        self.emit('done')

    def _on_ok_clicked(self, *args):
        """called when we click the OK button"""
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
        if args != None:
            msg = msg % args
        else:
            msg = msg
        logger.debug("show %s dialog : %s", title, msg)
        
        self.error_msgs = tichy.config.getboolean('error_messages','activated', False)
        
        if self.error_msgs or title == "Ussd":
            yield Dialog(parent, title, msg)
        else:
            yield None

    @tichy.tasklet.tasklet
    def option_dialog(self, title, msg, option1, option2, *args):
        logger.info("trying to get option dialog")
        result = yield Dialog(None, title, msg, option1, option2)
        
        yield result

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

