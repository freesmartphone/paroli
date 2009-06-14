# -*- coding: utf-8 -*-
#    Paroli
#
#    copyright 2008 Openmoko
#    copyright 2009 Openmoko
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
#    along with Paroli.  If not, see <http://www.gnu.org/licenses/>.


from logging import getLogger
logger = getLogger('core.paroli.gui')

import elementary
from tichy import config
from tichy.service import Service
from tichy.item import Item
from tichy.text import Text
from tichy.object import Object

class ElementaryWindow(Object):
    def __init__(self, title="Paroli"):
        self.elm_obj = elementary.Window(title, elementary.ELM_WIN_BASIC)
        self.elm_obj.title_set(title)
        self.elm_obj.show()
        self.elm_obj.autodel_set(True)
        self.elm_obj.on_del_add(self.closing)
        #self.elm_obj.on_resize_add(self.info)

        #self.size = self.elm_obj.size_get()
        #print dir(self.size)
        #print self.size[0]

    def closing(self, *args, **kargs):
        self.emit("closing")

    def info(self, *args, **kargs):
        logger.debug('info %s', self.elm_obj.size_get())
        layer = self.elm_obj.layer_get()
        logger.debug('%s', layer)
        if self.elm_obj.size_get() != self.size:
            if self.size[0] == 1:
                self.size = self.elm_obj.size_get()
            else:
                self.elm_obj.layer_set(layer-1)
                logger.debug('%s', self.elm_obj.layer_get())
                self.elm_obj.resize(self.size[0],self.size[1])


class ElementaryLayout(Object):
    def __init__(self, win, edje_file, group, x=1.0, y=1.0):
        self.elm_obj = elementary.Layout(win.elm_obj)
        self.elm_obj.file_set(edje_file, group)
        self.elm_obj.show()
        self.add_callback("*", "main_command", self.relay)
        self.edje = self.elm_obj.edje_get()

    def relay(self, emission, signal, source):
        logger.info("%s relaying %s", self, signal)
        logger.debug('relay %s', type(signal))
        self.emit(signal)

    def add(self, part, element):
        self.elm_obj.content_set(part, element)

    def add_callback(self, signal, source, func):
        self.elm_obj.edje_get().signal_callback_add(signal, source, func)

    def delete(self, *args, **kargs):
        self.elm_obj.hide()
        self.elm_obj.delete()

class ElementaryScroller(Object):
    def __init__(self, win):
        self.elm_obj = elementary.Scroller(win.elm_obj)
        self.elm_obj.size_hint_weight_set(1.0, 1.0)
        self.elm_obj.size_hint_align_set(-1.0, -1.0)
        if hasattr(self.elm_obj, "bounce_set"):
            self.elm_obj.bounce_set(0, 0)
        self.elm_obj.show()

class ElementaryBox(Object):
    def __init__(self, win):
        self.elm_obj = elementary.Box(win)
        self.elm_obj.size_hint_weight_set(0.0, 0.0)
        self.elm_obj.size_hint_align_set(0.0, 0.0)
        self.elm_obj.show()

class ElementaryTopbar(Object):
    def __init__(self, parent, onclick, edje_file, standalone=False):
        self.parent = parent
        self.onclick = onclick
        self.standalone = config.getboolean('standalone','activated', False)
        if self.standalone == True:
            self.bg = ElementaryLayout(parent.window, edje_file, "bg-tb-on")
            self.tb = ElementaryLayout(parent.window, edje_file, "tb")
            self.bg.elm_obj.content_set("tb-swallow", self.tb.elm_obj)
            self.tb.elm_obj.edje_get().signal_callback_add("top-bar", "*", self.signal)
        else:
            self.bg = ElementaryLayout(parent.window, edje_file, "bg-tb-off")

    def signal(self, emission, signal, source):
        logger.info(" %s emitting %s", self.parent, self.onclick)
        self.parent.emit(self.onclick)

class ElementaryLayoutWindow(Object):
    def __init__(self, edje_file, group, x=1.0, y=1.0, tb=False, onclick=None):
        self.window = ElementaryWindow()
        self.window.elm_obj.show()

        self.tb_action = onclick or 'back'

        self.topbar = Service.get("TopBar").create(self, self.tb_action, tb)

        self.bg = self.topbar.bg

        self.main_layout = ElementaryLayout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def tb_action_set(self, func):
        self.tb_action = func

    def delete(self, *args, **kargs):
        self.window.elm_obj.delete()

    def printer(self, *args, **kargs):
        logger.debug('printer %s', args)

    def restore_orig(self, *args, **kargs):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)

    def empty_window(self, *args, **kargs):
        self.bg.elm_obj.resize_object_del(self.main_layout.elm_obj)

class ElementaryLayoutSubwindow(ElementaryLayoutWindow):
    def __init__(self, window, edje_file, group):
        self.window = window.window
        self.bg = window.topbar.bg
        self.main_layout = ElementaryLayout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        #print self.bg.edje.part_exists("content-swallow")
        #self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def restore_orig(self):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)

class ElementaryListSubwindow(ElementaryLayoutWindow):
    def __init__(self, window, edje_file, group, swallow, layout=None):
        self.window = window.window
        self.bg = window.topbar.bg
        self.topbar = window.topbar
        self.main_layout = ElementaryLayout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = ElementaryScroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        if layout != None:
            self.window.elm_obj.resize_object_del(layout)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

class ElementaryListWindow(ElementaryLayoutWindow):
    def __init__(self, edje_file, group, swallow , sx=None, sy=None, tb=False, onclick=None):
        self.window = ElementaryWindow()
        self.window.elm_obj.show()

        self.tb_action = onclick or 'back'

        self.topbar = Service.get("TopBar").create(self, self.tb_action, tb)

        self.bg = self.topbar.bg

        self.main_layout = ElementaryLayout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = ElementaryScroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

class ElementaryList(Object):
      def __init__(self, model, parent, edje_file, group, label_list, comp_fct):

          self.model = model
          self.parent = parent
          self.edje_file = edje_file
          self.group = group
          self.elm_window = parent.window
          self.label_list = label_list
          self._comp_fct = comp_fct
          self.cb_list = []
          self.cb_list.append(self.model.connect('appended', self._redraw_view))
          self.cb_list.append(self.model.connect('inserted', self._redraw_view))
          self.cb_list.append(self.model.connect('removed', self._redraw_view))
          self.box = ElementaryBox(self.elm_window.elm_obj)
          self.callbacks = []
          self.sort()
          self.items = []
          self.letter_index = {}
          self._redraw_view()
          self.elm_window.elm_obj.on_del_add(self._remove_cb)

      def _redraw_view(self, *args, **kargs):
          #logger.info("list redrawing")
          if self.elm_window.elm_obj.is_deleted() == True:
                self._remove_cb()
          else:
              self.sort()
              if self.box.elm_obj.is_deleted() == False:
                  self.box.elm_obj.delete()
              self.box = ElementaryBox(self.elm_window.elm_obj)
              self.items = []
              self.letter_index = {}
              #self.model.sort()
              for item in self.model:
                  if self.elm_window.elm_obj.is_deleted() == True:
                      logger.info('window deleted %s', self.model)
                  ly = elementary.Layout(self.elm_window.elm_obj)
                  ly.file_set(self.edje_file, self.group)
                  edje_obj = ly.edje_get()
                  for part, attribute in self.label_list:
                    if hasattr(item, attribute):
                        value = getattr(item, attribute)
                        if self.label_list.index((part, attribute)) == 0:
                            if self.letter_index.has_key(value[0]) == False:
                                self.letter_index[value[0]] = self.model.index(item)

                        if isinstance(value, Item):
                            value = unicode(value.get_text())
                        elif isinstance(value, Text):
                            value = value.value

                        txt = unicode(value).encode('utf-8')
                        edje_obj.part_text_set(part,txt)
                    else:
                        logger.info(" %s doesn't have attribute %s", item, attribute)

                  ##check for optional display elements
                  if edje_obj.data_get('attribute1') != None:
                      attribute = edje_obj.data_get('attribute1')
                      if edje_obj.data_get('attribute2') != None:
                          item_cp = getattr(item,attribute)
                          attribute = edje_obj.data_get('attribute2')
                      else:
                          item_cp = item
                      if edje_obj.data_get('value') == 'None':
                          value = None
                      else:
                          value = edje_obj.data_get('value')
                      signal = edje_obj.data_get('signal')
                      if attribute[-2] == "(":
                          test = getattr(item_cp,attribute[:-2])()
                      else:
                          test = getattr(item_cp,attribute)
                      if test == value:
                          edje_obj.signal_emit(signal,'*')

                  ly.size_hint_min_set(470,60)
                  self.box.elm_obj.pack_end(ly)
                  ly.show()
                  self.items.append([item,edje_obj,ly])
                  edje_obj.signal_callback_add("*", "list_command", self.signal_send_others, [item,edje_obj,ly])

              self.parent.scroller.elm_obj.content_set(self.box.elm_obj)
              self.box.elm_obj.show()

              self.parent.scroller.elm_obj.show()

              self._renew_callbacks()

      def _renew_callbacks(self, *args, **kargs):
          logger.info("renewing callbacks")
          for cb in self.callbacks:
                for i in self.items:
                    i[1].signal_callback_add(cb[0], cb[1] , cb[2], i)

      def sort(self,*args,**kargs):
          logger.debug("list sorting")
          self.model.sort(self._comp_fct)

      def _remove_cb(self, *args, **kargs):
          logger.debug('window removed, removing cb')
          for i in self.cb_list :
              try:
                  self.model.disconnect(i)
              except Exception, e:
                  logger.exception("ooops wrong oid")

      def _modified(self, *args, **kargs):
          logger.info('scrolled')
          logger.info(args)
          logger.info(kargs)

      def add_callback(self, signal, source, func):
          self.callbacks.append([signal, source, func])
          for i in self.items:
              i[1].signal_callback_add(signal, source , func, i)

      def signal_send_others(self, emission, signal, source, item):
          for i in self.items:
              if i != item:
                  i[1].signal_emit(signal, "list")

      def signal_send(self, signal, source):
          for i in self.items:
              i[1].signal_emit(signal, source)

      def _remove_item(self, list, removed_item):
          logger.info('remove called')
          for item in self.items:
              if item[0] is removed_item:
                  index = item
                  item[2].remove_all()

          self.items.remove(index)
          self._redraw_box()

      def jump_to_index(self, key):
          if self.letter_index.has_key(key):
              position = self.letter_index[key]
              point_y = 60 * int(position)
              if hasattr(self.parent.scroller.elm_obj, 'region_show'):
                  self.parent.scroller.elm_obj.region_show(0, point_y, 480, 60)
              else:
                  logger.info("scroller doesn't have method bounce_set please update your bindings")

