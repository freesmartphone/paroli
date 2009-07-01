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

import elementary
import e_dbus
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.x
import ecore.evas
#import etk

import logging
logger = logging.getLogger('gui')

import tichy

class EventsLoop(tichy.Object):

    def __init__(self):
        self.dbus_loop = e_dbus.DBusEcoreMainLoop()
        try:
            elementary.c_elementary.theme_overlay_add("/usr/share/elementary/themes/paroli.edj")
        except:
            logger.info("can't add elementary theme overlay, please update your bindings")
        elementary.init()

    def run(self):
        """start the main loop

        This method only return after we call `quit`.
        """


        ecore.main_loop_begin()
        ecore.x.on_window_delete_request_add(self.test)
        #elementary.run()
        # XXX: elementary also has a run method : elementary.run(),
        #      how does it work with ecore.main_loop ?

    def test(self, *args, **kargs):
        logger.info("delete request with %s %s", args, kargs)

    def timeout_add(self, time, callback, *args):
        return ecore.timer_add(time / 1000., callback, *args)
        pass

    def source_remove(self, timer):
        pass
        timer.delete()

    def quit(self):
        self.emit("closing")
        logger.info("emitted closing")
        ecore.main_loop_quit()
        elementary.shutdown()

    def iterate(self):
        #ecore.main_loop_iterate()
        pass

class elm_window(tichy.Object):
    def __init__(self, title="Paroli"):
        self.elm_obj = elementary.Window(title, elementary.ELM_WIN_BASIC)
        self.elm_obj.title_set(title)
        self.elm_obj.autodel_set(True)
        self.elm_obj.on_del_add(self.closing)

    def printer(self, *args, **kargs):
        logger.info("window printer called with %s and %s", args, kargs)

    def closing(self, *args, **kargs):
        self.emit("closing")

    def info(self, *args, **kargs):
        print self.elm_obj.size_get()
        layer = self.elm_obj.layer_get()
        print layer
        if self.elm_obj.size_get() != self.size:
            if self.size[0] == 1:
                self.size = self.elm_obj.size_get()
            else:
                self.elm_obj.layer_set(layer-1)
                print self.elm_obj.layer_get()
                self.elm_obj.resize(self.size[0],self.size[1])


class elm_layout(tichy.Object):
    def __init__(self, win, edje_file, group, x=1.0, y=1.0):
        self.elm_obj = elementary.Layout(win.elm_obj)
        self.elm_obj.file_set(edje_file, group)
        self.elm_obj.show()
        self.add_callback("*", "main_command", self.relay)
        self.Edje = self.elm_obj.edje_get()

    def relay(self, emission, signal, source):
        logger.debug("%s relaying %s", str(self), str(signal))
        self.emit(signal)

    def add(self, part, element):
        self.elm_obj.content_set(part, element)

    def add_callback(self, signal, source, func):
        self.elm_obj.edje_get().signal_callback_add(signal, source, func)

    def delete(self, *args, **kargs):
        self.elm_obj.hide()
        self.elm_obj.delete()

class elm_scroller(tichy.Object):
    def __init__(self, win):
        self.elm_obj = elementary.Scroller(win.elm_obj)
        self.elm_obj.size_hint_weight_set(1.0, 1.0)
        self.elm_obj.size_hint_align_set(-1.0, -1.0)
        if hasattr(self.elm_obj, "bounce_set"):
            self.elm_obj.bounce_set(0, 0)
        self.elm_obj.show()

class elm_box(tichy.Object):
    def __init__(self, win):
        self.elm_obj = elementary.Box(win)
        self.elm_obj.size_hint_weight_set(0.0, 0.0)
        self.elm_obj.size_hint_align_set(0.0, 0.0)
        self.elm_obj.show()

class elm_tb(tichy.Object):
    def __init__(self, parent, onclick, edje_file, standalone=False):
        self.parent = parent
        self.onclick = onclick
        self.standalone = tichy.config.getboolean('standalone','activated', False)
        if self.standalone == True:
            self.bg = elm_layout(parent.window, edje_file, "bg-tb-on")
            self.tb = elm_layout(parent.window, edje_file, "tb")
            self.bg.elm_obj.content_set("tb-swallow", self.tb.elm_obj)
            self.tb.elm_obj.edje_get().signal_callback_add("top-bar", "*", self.signal)
        else:
            self.bg = elm_layout(parent.window, edje_file, "bg-tb-off")

    def signal(self, emission, signal, source):
        logger.info(" %s emitting %s", str(self.parent), str(self.onclick))
        self.parent.emit(self.onclick)

class elm_layout_window(tichy.Object):
    def __init__(self, edje_file, group, x=1.0, y=1.0, tb=False, onclick=None):
        self.window = elm_window()  
        self.window.elm_obj.show()

        self.tb_action = onclick or 'back'

        self.bg_m = tichy.Service.get("TopBar").create(self, self.tb_action, tb)

        self.bg = self.bg_m.bg

        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def tb_action_set(self, func):
        self.tb_action = func

    def delete(self, *args, **kargs):
        self.window.elm_obj.delete()

    def printer(self, *args, **kargs):
        print args

    def restore_orig(self, *args, **kargs):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)

    def empty_window(self, *args, **kargs):
        self.bg.elm_obj.resize_object_del(self.main_layout.elm_obj)

class elm_layout_subwindow(elm_layout_window):
    def __init__(self, window, edje_file, group):
        self.window = window.window
        self.bg = window.bg_m.bg
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        #print self.bg.Edje.part_exists("content-swallow")
        #self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

    def restore_orig(self):
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)

class elm_list_subwindow(elm_layout_window):
    def __init__(self, window, edje_file, group, swallow, layout=None):
        self.window = window.window
        self.bg = window.bg_m.bg
        self.bg_m = window.bg_m
        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = elm_scroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        if layout != None:
            self.window.elm_obj.resize_object_del(layout)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

class elm_list_window(elm_layout_window):
    def __init__(self, edje_file, group, swallow , sx=None, sy=None, tb=False, onclick=None):
        self.window = elm_window()  
        self.window.elm_obj.show()

        self.tb_action = onclick or 'back'

        self.bg_m = tichy.Service.get("TopBar").create(self, self.tb_action, tb)

        self.bg = self.bg_m.bg

        self.main_layout = elm_layout(self.window, edje_file, group, x=1.0, y=1.0)
        self.scroller = elm_scroller(self.window)
        self.main_layout.elm_obj.content_set(swallow, self.scroller.elm_obj)
        self.bg.elm_obj.content_set("content-swallow", self.main_layout.elm_obj)
        self.window.elm_obj.resize_object_add(self.bg.elm_obj)
        self.bg.elm_obj.show()

class elm_list(tichy.Object):
    def __init__(self, model, Parent, EdjeFile, EdjeGroup, label_list, comp_fct,LetterDict=False):

        self.model = model
        self.parent = Parent
        self.EdjeFile = EdjeFile
        self.EdjeGroup = EdjeGroup
        self.Elm_win = Parent.window
        self.label_list = label_list    
        self._comp_fct = comp_fct
        self.LetterDict = LetterDict
        self.cb_list = []
        self.cb_list.append(self.model.connect('appended', self._redraw_view))
        self.cb_list.append(self.model.connect('inserted', self._redraw_view))
        self.cb_list.append(self.model.connect('removed', self._redraw_view))
        self.box = elm_box(self.Elm_win.elm_obj)
        self.callbacks = []
        self.sort()
        self.items = []
        self.letter_index = {}
        self._redraw_view()
        self.Elm_win.elm_obj.on_del_add(self._remove_cb)

    def _redraw_view(self, *args, **kargs):
        #logger.info("list redrawing")
        if self.Elm_win.elm_obj.is_deleted() == True:
            self._remove_cb()
        else:
            self.sort()
            if self.box.elm_obj.is_deleted() == False:
                self.box.elm_obj.delete()
            self.box = elm_box(self.Elm_win.elm_obj)
            self.items = []
            self.letter_index = {}
            #self.model.sort()
            for item in self.model:
                if self.Elm_win.elm_obj.is_deleted() == True:
                    logger.info(str(self.model))
                    logger.info("window deleted")
                ly = elementary.Layout(self.Elm_win.elm_obj)
                ly.file_set(self.EdjeFile, self.EdjeGroup)              
                edje_obj = ly.edje_get()
                for part, attribute in self.label_list:
                    if hasattr(item, attribute):
                        value = getattr(item, attribute)
                        if (isinstance(value, str) and not len(value)) or\
                           value == None: 
                            value = " " #bugfix for empty name
                        if self.LetterDict:
                            if self.label_list.index((part, attribute)) == 0:
                                letter = value[0]
                                letter = letter.lower()
                                if self.letter_index.has_key(letter) == False:
                                    self.letter_index[letter] = self.model.index(item)

                        if isinstance(value, tichy.Item):
                            value = unicode(value.get_text())
                        elif isinstance(value, tichy.Text):
                            value = value.value

                        txt = unicode(value).encode('utf-8')
                        edje_obj.part_text_set(part,txt)
                    else:
                        logger.info(" %s doesn't have attribute %s", str(item), str(attribute))

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

                ly.size_hint_min_set(470,96)
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
                logger.debug("ooops wrong oid")

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

    def jump_to_index(self, *args, **kargs):
        if self.LetterDict:
            key = args[2]
            if self.letter_index.has_key(key):
                position = self.letter_index[key]
                point_y = 100 * int(position)
                if hasattr(self.parent.scroller.elm_obj, 'region_show'):
                    self.parent.scroller.elm_obj.region_show(0, point_y, 480, 60)
                else:
                    logger.info("scroller doesn't have method bounce_set please update your bindings")

            edje = self.parent.main_layout.elm_obj.edje_get()
            edje.signal_emit( "close-dict", "dict-button")
        else:
            logger.info("this list does not carry a dict, this call does not work here")