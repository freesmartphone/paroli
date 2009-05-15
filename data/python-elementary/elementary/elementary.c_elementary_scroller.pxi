# Copyright (c) 2008-2009 Simon Busch
#
# This file is part of python-elementary.
#
# python-elementary is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-elementary is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with python-elementary.  If not, see <http://www.gnu.org/licenses/>.
#

cdef class Scroller(Object):
    def __init__(self, c_evas.Object parent):
        self._set_obj(elm_scroller_add(parent.obj))

    def content_set(self, c_evas.Object child):
        elm_scroller_content_set(self.obj, child.obj)

    def content_min_limit(self, int w, int h):
        elm_scroller_content_min_limit(self.obj, w, h)

    def region_show(self, x, y, w, h):
        elm_scroller_region_show(self.obj, x, y, w, h)
        
    def policy_set(self, h, v):
        elm_scroller_policy_set(self.obj, h, v)

    #results in segfault
    #def region_get(self, x, y, w, h):
        #elm_scroller_region_get(self.obj, x, y, w, h)
        
    def bounce_set(self, h_bounce, v_bounce):
        elm_scroller_bounce_set(self.obj, h_bounce, v_bounce)
