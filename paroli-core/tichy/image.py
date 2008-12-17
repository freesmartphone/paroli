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

import tichy


class Image(tichy.Item):
    """Base class for images"""

    def __init__(self, path, size=None):
        """create a new image from a file
        """
        super(Image, self).__init__()
        assert isinstance(path, basestring), type(path)
        self.__path = path
        self.surf = None
        self.size = size

    def __get_path(self):
        return self.__path

    def __set_path(self, value):
        assert isinstance(value, basestring)
        self.__path = value
        self.surf = None
        self.emit('modified')

    path = property(__get_path, __set_path)

    def __repr__(self):
        return "Image(%s)" % self.path

    def load(self, painter):
        if self.surf:
            return
        self.surf = painter.surface_from_image(self.path)

    def view(self, parent):
        import tichy.gui
        return tichy.gui.ImageWidget(parent, self)

    def draw(self, painter, size=None):
        self.load(painter)
        painter.draw_surface(self.surf)
