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


# XXX: To we still use this ??

from item import Item
from text import Text


class Menu(Item):
    """Item that represents a menu"""

    def __init__(self, parent=None, item=None):
        super(Menu, self).__init__()
        self.children = []
        if isinstance(item, str):
            item = Text(item)
        self.item = item
        if parent:
            parent.add(self)

    def add(self, m):
        self.children.append(m)
        m.connect_object('activated', Menu.emit, self, 'activated')

    def view(self, parent, axis=0):
        from ..gui import Scrollable, Box, Button, Label
        ret = Scrollable(parent, axis=axis, item=self)

        box = Box(ret, axis=axis, spacing=0, border=0)

        for c in self.children:
            b = Button(box)
            if c.item:
                c.item.view(b)
            if c.children:
                b.connect('clicked', self.on_clicked, c)
            else:
                b.connect_object('clicked', Menu.emit, c, 'activated')
                b.connect_object('clicked', Scrollable.destroy, ret)
        return ret

    @staticmethod
    def on_clicked(b, menu_item):
        import tichy.gui as gui

        w = gui.Window(b.window, modal=False)
        abox = gui.Fixed(w)

        box = gui.Box(abox, axis=1, border=0, spacing=0)
        # Compute the optimal rect for the menu (just bellow the
        # button) TODO: make it better
        box.pos = b.abs_pos() + b.size.set(0, 0)
        box.size = gui.Vect(240, 640)

        view = menu_item.view(box, axis=1)

        gui.Spring(box, axis=1)

        w.clickable = True

        def on_w_click(o, *args):
            w.destroy()
        w.connect('mouse-down', on_w_click)
        view.connect('destroyed', on_w_click)
