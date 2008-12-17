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

from tichy.tasklet import Tasklet
from tichy.item import Item
from tichy.service import Service
import tichy

# TODO: shouldn't we rename this to Applet ???


class Application(Tasklet, Item):
    """This class represents an application

    To create a new application just subclass this class, the new
    application will be automatically registered thanks to the Item
    class "magic".

    you can create the following class attributes

    - name : the name of the app

    - icon : an optional path to an icon

    - category : a string represneting the category in which the
      application should appears in the launcher application If the
      name or category is not defined, then the app won't show up in
      the laucher application

    The view method of an application instance will create a frame
    that the application can use.
    """

    design = 'Default'  # Set this to the name of a Design service to
                        # specify the optimal design.

    category = None

    @classmethod
    def create_actor(cls):
        from tichy import Actor
        ret = Actor(cls)
        run_action = ret.new_action("Run")

        def on_run_action(action, app, view):
            yield app(view.window)

        ret.default_action = run_action    # So that by default we run
                                           # the application
        run_action.connect('activated', on_run_action)

        return ret

    @classmethod
    def get_text(cls):
        """
        Return the name of the application

        default to the class 'name' attribute
        """
        from .text import Text
        return Text(cls.name)

    @classmethod
    def get_sub_text(cls):
        return None

    def view(self, parent, **kargs):
        """Create a view of a frame for the application in the parent widget

        :Parameters:

            parent : gui.Widget
                The parent widget we create the view in
        """
        # The 'Design' service is in charge of creating the frame
        design = Service('Design')
        return design.view_application(parent, self, **kargs)

    def do_run(self, parent, *args, **kargs):
        """You shouldn't change this, redefine the run method instead"""
        # Before trunning the app we set the default design the the
        # one specified by the application
        if self.design:
            old_design = tichy.Service('Design')
            tichy.Service.set_default('Design', self.design)
        window = tichy.gui.Window(parent, modal=True, expand=True)
        ret = yield super(Application, self).do_run(window, *args, **kargs)
        window.destroy()
        if self.design:
            tichy.Service.set_default('Design', old_design)
        yield ret


class Gadget(Tasklet, Item):
    """Special Application that can be put in a bar.
    """
    design = None
