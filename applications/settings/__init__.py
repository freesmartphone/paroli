# -*- coding: utf-8 -*-
#    Settings app
#
#    copyright 2009 Openmoko (mirko@openmoko.org)
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
logger = getLogger('applications.settings')

from os.path import join, dirname
from tichy.list import List
from tichy.text import Text
from tichy.service import Service
from tichy.application import Application
from tichy.tasklet import WaitFirst, Wait, tasklet
from tichy.settings import Setting
from tichy import config
from elementary import Entry
from paroli.gui import ElementaryListWindow, ElementaryList, ElementaryListSubwindow

##create your applications class
class Settings(Application):

    ##this name is used by paroli to find your application
    name = 'Settings'

    ##the icon attribute is currently unused
    icon = 'icon.png'

    ## the category is used by paroli when applications are to be grouped.
    ## Set it to 'launcher' if you want your application to appear 
    ## on the launcher screen
    category = 'launcher' # was 'settings'

    ##the run method of the app is called when the app is started
    def run(self, parent=None,  standalone=False):
        ##the edje file
        self.edje_file = join(dirname(__file__),'settings.edj')

        ##import a parameter which tells the app about paroli's window's size
        self.standalone = config.getboolean('standalone','activated', False)

        ##generate app-window
        self.window = ElementaryListWindow(self.edje_file, "main", "list",
                                           None, None, True)
        self.edje_obj = self.window.main_layout

        self.groups = List()

        for i in Setting.groups:
            t = Text(i)
            self.groups.append(Text(i))

        def comp(m1, m2):
            return cmp(str(m2).lower(), str(m1).lower())
        
        self.list_label = [('title', 'value')]
        self.item_list = ElementaryList(self.groups, self.window, self.edje_file, 
                                        "item", self.list_label, comp)
        
        self.item_list.add_callback("*", "sublist", self._show_sublist) 
        
        ## close the Tele app, with the back button (signal, source, method)
        self.edje_obj.add_callback("back", "edje", self.signal) 
        
        parent.emit("unblock")
        
        i, args = yield WaitFirst(Wait(self.window, 'delete_request'),
                                  Wait(self.window, 'back'),
                                  Wait(self.window.window,'closing'))
        ##we write a logger message that the application is closing
        logger.info('Settings closing')

        ##we delete the window object (the class would also delete all children object)
        if i != 2:
            self.item_list._remove_cb()
            self.window.delete()

    def signal(self, emission, signal, source):
        """ Callback function. It invokes, when the "back" button clicked."""
        logger.info("settings.py:signal() emmision: %s, signal: %s, source: %s", 
                    str(emission), str(signal), str(source))
        self.window.emit('back')

    def _show_sublist(self, emission, signal, source, group):
        logger.info("showing sublist from group %s; source: %s, signal: %s", 
                     str(group[0]), str(source), str(signal))
        SettingsSublist(self.window, self.edje_file, str(group[0]), self.edje_obj).start()

class SettingsSublist(Application):

    name = 'SettingsSublist'

    def run(self, parent, edje_file, group, layout, *args, **kargs):

        layout.elm_obj.hide()

        self.parent = parent

        self.window = ElementaryListSubwindow(parent, edje_file, "main", "list")
        self.edje_obj = self.window.main_layout

        self.edje_obj.edje.signal_emit("sublist_mode","*")

        self.settings = List()
        self.cb_list = List()

        for i in Setting.groups[group]:
            o = Setting.groups[group][i]
            self.settings.append(o)

        def comp(m1, m2):
            return cmp(m2.name, m1.name)

        self.list_label = [('title', 'name'),('subtitle', 'value')]
        self.item_list = ElementaryList(self.settings, self.window, edje_file,
                                        "item", self.list_label, comp)

        for i in self.settings:
            if hasattr(i, 'options'):
                oid = i.options.connect('updated', self.item_list._redraw_view)
                self.cb_list.append([i.options,oid])

        self.item_list.add_callback("*", "sublist", self.action)

        yield WaitFirst(Wait(self.window, 'delete_request'),
                        Wait(self.edje_obj, 'back'))

        for i in self.cb_list:
            i[0].disconnect(i[1])

        self.edje_obj.elm_obj.visible_set(False)
        self.edje_obj.delete()
        parent.restore_orig()
        layout.elm_obj.show()

    def action(self, emission, signal, source, item):
        item[0].rotate(self.parent, self.edje_obj)


class FreeEditService(Service):
    service = "FreeEdit"

    def __init__(self):
        super(FreeEditService, self).__init__()

    @tasklet
    def init(self):
        logger.info("FreeEdit service initializing")
        yield self._do_sth()

    def _do_sth(self):
        pass

    def StringEdit(self, setting, parent, layout):
        return StringSettingApp(setting, parent, layout)

    def NumberEdit(self, setting, parent, layout):
        return NumberSettingApp(setting, parent, layout)

    def ListEdit(self, setting, parent, model, ListLabel, layout, edje_group, save_button):
        return ListSettingApp(setting, parent, model, ListLabel, layout, edje_group, save_button)

class NumberSettingApp(Application):
    name = "NumberSetting"

    def run(self, setting, parent, layout):
        self.edje_file = join(dirname(__file__), 'settings.edj')

        layout.elm_obj.hide()
        self.window = ElementaryListSubwindow(parent, self.edje_file, "numbersetting","entry", layout.elm_obj)

        self.edje_obj = self.window.main_layout

        self.edje_obj.edje.signal_emit(str(setting.value),"set_text")

        i, args = yield WaitFirst(Wait(self.window.main_layout, 'save'),
                                  Wait(self.window.main_layout, 'back'),
                                  Wait(parent, 'back'))

        if i == 0: ##save clicked
            self.edje_obj.edje.signal_emit("save-notice","*")
            text = str(self.edje_obj.edje.part_text_get("num_field-text"))
            text = text.strip()
            setting.set(text).start()

        self.edje_obj.edje.visible_set(False)
        self.edje_obj.edje.delete()
        layout.elm_obj.show()

class ListSettingApp(Application):

    name = 'ListSetting'

    def run(self, setting, parent, model, list_label, layout, group="item", 
             save_button=False, *args, **kargs):
        layout.elm_obj.hide()

        self.parent = parent
        self.setting = setting

        self.edje_file = join(dirname(__file__), 'settings.edj')

        self.window = ElementaryListSubwindow(parent, self.edje_file, "main", "list")

        self.edje_obj = self.window.main_layout

        self.edje_obj.edje.signal_emit("sublist_mode","*")

        if save_button:
            self.edje_obj.edje.signal_emit("save_button","*")

        self.ItemList = model
        self.cb_list = List()

        #for i in Setting.groups[group]:
            #o = Setting.groups[group][i]
            #self.settings.append(o)

        def comp(m1, m2):
            if m1.name == None or m1.name == "":
                return cmp(m2, m1)
            else:
                return cmp(m2.name, m1.name)
        item_group = group or "item"
        
        self.list_label = list_label
        self.item_list = ElementaryList(self.ItemList, self.window, self.edje_file, 
                                        item_group, list_label, comp)
        
        for i in self.ItemList:
            if hasattr(i, 'connect'):
                oid = i.connect('updated', self.item_list._redraw_view)
                self.cb_list.append([i,oid])

        self.item_list.add_callback("*", "sublist", self.action)
        self.item_list.add_callback("pressed", "decrease", self.decrease)
        self.item_list.add_callback("pressed", "increase", self.increase)
        self.edje_obj.edje.signal_callback_add("pressed", "save", self.save)

        yield WaitFirst(Wait(self.window, 'delete_request'),Wait(self.edje_obj, 'back'),Wait(self.ItemList, 'save'))

        for i in self.cb_list:
            i[0].disconnect(i[1])

        self.edje_obj.elm_obj.visible_set(False)
        self.edje_obj.delete()
        self.item_list._remove_cb()
        layout.elm_obj.show()

    def action(self, emission, signal, source, item):
        item[0].action(item, self.parent, self.edje_obj)
        logger.info("action called")

    def EnableSaveButton(self, *args, **kargs):
        self.edje_obj.edje.signal_emit("EnableSave","*")

    def save(self, *args, **kargs):
        logger.info("save triggered")
        self.ItemList.emit('save')

    def increase(self, emission, signal, source, item):
        if item[0].val_type == "int":
            current = item[0].val_range.index(int(emission.part_text_get('value')))
        else:
            current = item[0].val_range.index(emission.part_text_get('value'))
        if len(item[0].val_range)-1 > current:
            new = item[0].val_range[current+1]
        else:
            new = item[0].val_range[0]

        item[0].value = new

        emission.part_text_set('value', str(new))

    def decrease(self, emission, signal, source, item):

        if item[0].val_type == "int":
            current = item[0].val_range.index(int(emission.part_text_get('value')))
        else:
            current = item[0].val_range.index(emission.part_text_get('value'))
        if current < 0:
            new = item[0].val_range[len(item[0].val_range)-1]
        else:
            new = item[0].val_range[current-1]

        item[0].value = new

        emission.part_text_set('value', str(new))

class StringSettingApp(Application):
    name = "StringSetting"

    def run(self, setting, parent, layout):
        self.edje_file = join(dirname(__file__), 'settings.edj')

        layout.elm_obj.hide()
        self.window = ElementaryListSubwindow(parent, self.edje_file, "stringsetting","entry", layout.elm_obj)
        self.edje_obj = self.window.main_layout

        if setting != None:
            self.edje_obj.edje.signal_emit(str(setting.name),"set_text")

        textbox = Entry(parent.window.elm_obj)

        if setting != None:
            textbox.entry_set(setting.value)

        textbox.size_hint_weight_set(1.0, 1.0)

        self.edje_obj.elm_obj.content_set("entry",textbox)

        textbox.editable_set(True)

        textbox.focus()

        textbox.show()

        i, args = yield WaitFirst(Wait(self.edje_obj,'save'),
                                  Wait(self.edje_obj,'back'),
                                  Wait(parent,'back'))

        if i == 0: ##save clicked
            text = str(textbox.entry_get()).replace("<br>","")
            text = text.strip()
            if setting != None:
                self.edje_obj.edje.signal_emit("save-notice","*")
                self.edje_obj.elm_obj.visible_set(False)
                self.edje_obj.delete()
                layout.elm_obj.show()
                setting.set(text).start()
                parent.window.elm_obj.keyboard_mode_set(gui.ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
            else:
                self.edje_obj.elm_obj.visible_set(False)
                #if setting != None:
                self.edje_obj.delete()
                layout.elm_obj.show()
                parent.window.elm_obj.keyboard_mode_set(gui.ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
                yield text
        else:
            self.edje_obj.elm_obj.visible_set(False)
            self.edje_obj.delete()
            layout.elm_obj.show()
         
        parent.window.elm_obj.keyboard_mode_set(gui.ecore.x.ECORE_X_VIRTUAL_KEYBOARD_STATE_OFF)
        
