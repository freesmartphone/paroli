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

"""Dialog module"""

from tichy.tasklet import Tasklet, Wait
import tichy


class Dialog(tichy.Application):
    """This application shows a message on the screen"""

    def run(self, parent, title, msg):
        w = tichy.gui.Window(parent)

        frame = self.view(w, title=title)
        vbox = tichy.gui.Box(frame, axis=1, expand=True)
        tichy.gui.Label(vbox, msg, expand=True)

        b = gui.Button(vbox)
        tichy.gui.Label(b, 'OK')
        yield Wait(b, 'clicked')
        w.destroy()
