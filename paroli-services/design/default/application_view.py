# coding=utf8
#
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
from tichy import gui
from tichy.gui import Vect


class ActionBar(gui.Widget):
    """Action bar widget class

    This it the bar we can see at the bottom of the application frame
    where we can trigger actions on the selected actor.
    """

    def __init__(self, parent):
        super(ActionBar, self).__init__(parent)
        scrollable = gui.Scrollable(self, axis=0)
        self.box = gui.Box(scrollable, axis=0, border=0, spacing=0)
        self.buttons = []

    def clear(self):
        for b in self.buttons:
            b.destroy()

    def set_actor(self, actor, view):
        """Show the actions from an actor"""
        self.clear()
        for a in actor.actions:
            b = gui.Button(self.box)
            gui.Label(b, a.name)

            def on_clicked(b, a):
                a.activate(b)
                tichy.Service('Design').unselect(actor, view)
            b.connect('clicked', on_clicked, a)
            self.buttons.append(b)


class ApplicationFrame(gui.Frame):
    """Application Frame Widget

    This widget is the main frame for every applications. It contains
    a top bar with an icon, the name of the application, and an
    optional 'back' button. It also contains a bottom bar to show the
    actions on the selected actor.
    """

    icon = None

    class Bar(gui.Frame):

        def __init__(self, parent, app, back_button=False, **kargs):
            self.app = app
            super(ApplicationFrame.Bar, self).__init__(
                parent, min_size=Vect(0, 96),
                tags=['application-bar'], **kargs)
            box = gui.Box(self, axis=0)
            app.actor.view(box, expand=True)
            if back_button:
                msg = "back" if back_button is True else back_button
                back = gui.Button(box, min_size=Vect(0, 0),
                                  tags=['back-button'])
                gui.Label(back, msg)
                back.connect('clicked', self.on_back)

        def on_back(self, b):
            self.app.emit('back')

    class Content(gui.Frame):
        """The widget that is given as a parent to the applications"""

        def __init__(self, parent):
            super(ApplicationFrame.Content, self).__init__(
                parent, min_size=Vect(480, 0), border=0, expand=True)

    def get_text(self):
        return tichy.Text(self.title)

    def get_sub_text(self):
        return None

    def path(self, file_name=None):
        return self.app.path(file_name)

    def __init__(self, parent, app, title=None, border=0, back_button=False,
                 expand=True, **kargs):
        assert isinstance(app, tichy.Application), app
        self.app = app
        super(ApplicationFrame, self).__init__(parent, border=0,
                                               expand=expand, **kargs)
        self.title = title or app.name
        self.icon = app.icon
        self.content = self
        self.box = gui.Box(self, axis=1, border=0, spacing=0, expand=True)
        # self.bar = ApplicationFrame.Bar(self.box, title=title)
        self.actor = tichy.Actor(self)
        self.bar = ApplicationFrame.Bar(self.box, self,
                                        back_button=back_button)
        self.content = ApplicationFrame.Content(self.box)
        self.action_bar = ActionBar(self.box)
        self.menu_view = None

    def get_contents_child(self):
        """Override Widget method"""
        return self.content
