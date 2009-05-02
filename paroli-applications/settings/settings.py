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

##import logging facilities to produce logging messages from within you app
import logging

##name the logger
logger = logging.getLogger('settings')

##import os module to load edj files
import os

##import main paroli-core module
import tichy

##import gui module to access paroli's gui classes
from tichy import gui
from tichy import Service

##import services module to retrieve data from services throughout tichy
from tichy.service import Service

##create your applications class
class Settings(tichy.Application):

    ##this name is used by paroli to find your application
    name = 'Settings'
    
    ##the icon attribute is currently unused
    icon = 'icon.png'
    
    ##the category is used by paroli when applications are to be grouped.Set it to 'launcher' if you want your application to appear on the launcher screen
    category = 'settings'
    
    ##the run method of the app is called when the app is started
    def run(self, parent=None,  standalone=False):
        ##the edje file
        self.edje_file = os.path.join(os.path.dirname(__file__),'settings.edj')
    
        ##import a parameter which tells the app about paroli's window's size
        self.standalone = tichy.config.getboolean('standalone','activated', False)
        
        ##generate app-window
        self.window = gui.elm_list_window(self.edje_file, "main", "list", None, None, True)
        self.edje_obj = self.window.main_layout
        
        self.groups = tichy.List()
        
        for i in tichy.Setting.groups:
            t = tichy.Text(i)
            self.groups.append(tichy.Text(i))
        
        def comp(m1, m2):
            return cmp(m2, m1)
        
        self.list_label = [('title', 'value')]
        self.item_list = gui.elm_list(self.groups, self.window, self.edje_file, "group", self.list_label, comp)
        
        self.item_list.add_callback("*", "sublist", self._show_sublist)
        
        yield tichy.WaitFirst(tichy.Wait(self.window, 'delete_request'),tichy.Wait(self.window, 'back'))
        #,tichy.Wait(self.button, 'aux_button_pressed')
        ##we write a logger message that the application is closing
        logger.info('Settings closing')
        
        ##we delete the window object (the class would also delete all children object)
        #del self.groups
        self.item_list._remove_cb()
        self.window.delete()
        
    def _show_sublist(self, emission, signal, source, group):
        logger.info("showing sublist from group %s", str(group[0]))
        SettingsSublist(self.window, self.edje_file, str(group[0]), self.edje_obj).start()

class SettingsSublist(tichy.Application):
    
    name = 'SettingsSublist'

    def run(self, parent, edje_file, group, layout, *args, **kargs):
    
        layout.elm_obj.hide()
      
        self.parent = parent
      
        self.window = gui.elm_list_subwindow(parent, edje_file, "main", "list")
        self.edje_obj = self.window.main_layout
        
        self.edje_obj.Edje.signal_emit("sublist_mode","*")
        
        self.settings = tichy.List()
        self.cb_list = tichy.List()
        
        for i in tichy.Setting.groups[group]:
            o = tichy.Setting.groups[group][i]
            self.settings.append(o)
            
        def comp(m1, m2):
            return cmp(m2.name, m1.name)
        
        self.list_label = [('title', 'name'),('subtitle', 'value')]
        self.item_list = gui.elm_list(self.settings, self.window, edje_file, "group", self.list_label, comp)
        
        for i in self.settings:
            if hasattr(i, 'options'):
                oid = i.options.connect('updated', self.item_list._redraw_view)
                self.cb_list.append([i.options,oid])
        
        self.item_list.add_callback("*", "sublist", self.action)
    
        yield tichy.WaitFirst(tichy.Wait(self.window, 'delete_request'),tichy.Wait(self.edje_obj, 'back'))
    
        for i in self.cb_list:
            i[0].disconnect(i[1])

        self.edje_obj.elm_obj.visible_set(False)
        self.edje_obj.delete()
        parent.restore_orig()
        layout.elm_obj.show()
        
    def action(self, emission, signal, source, item):
        item[0].rotate(self.parent, self.edje_obj)
        

class FreeEditService(tichy.Service):
    service = "FreeEdit"
    
    def __init__(self):
        super(FreeEditService, self).__init__()
    
    @tichy.tasklet.tasklet
    def init(self):
        logger.info("FreeEdit service initializing")
        yield self._do_sth()
        
    def _do_sth(self):
        pass    

    def StringEdit(self, setting, parent, layout):
        return StringSettingApp(setting, parent, layout)
        
    def NumberEdit(self, setting, parent, layout):
        return NumberSettingApp(setting, parent, layout)

    def ListEdit(self, setting, parent, model, ListLabel, layout):
        return ListSettingApp(setting, parent, model, ListLabel, layout)

class NumberSettingApp(tichy.Application):
    name = "NumberSetting"
    
    def run(self, setting, parent, layout):
        self.edje_file = os.path.join(os.path.dirname(__file__), 'settings.edj')
        
        layout.elm_obj.hide()
        self.window = gui.elm_list_subwindow(parent, self.edje_file, "numbersetting","entry", layout.elm_obj)
        
        self.edje_obj = self.window.main_layout
        
        self.edje_obj.Edje.signal_emit(str(setting.value),"set_text")
        
        i, args = yield tichy.WaitFirst(tichy.Wait(self.window.main_layout, 'save'), tichy.Wait(self.window.main_layout, 'back'),tichy.Wait(parent, 'back'))
        
        if i == 0: ##save clicked
            self.edje_obj.Edje.signal_emit("save-notice","*")
            text = str(self.edje_obj.Edje.part_text_get("num_field-text"))
            text = text.strip()
            setting.set(text).start()
        
        self.edje_obj.Edje.visible_set(False)
        self.edje_obj.Edje.delete()
        layout.elm_obj.show()

class ListSettingApp(tichy.Application):
    
    name = 'ListSetting'

    def run(self, setting, parent, model, list_label, layout, *args, **kargs):
    
        layout.elm_obj.hide()
      
        self.parent = parent
      
        self.edje_file = os.path.join(os.path.dirname(__file__), 'settings.edj')
      
        self.window = gui.elm_list_subwindow(parent, self.edje_file, "main", "list")
        
        self.edje_obj = self.window.main_layout
        
        self.edje_obj.Edje.signal_emit("sublist_mode","*")
        
        self.ItemList = model
        self.cb_list = tichy.List()
        
        #for i in tichy.Setting.groups[group]:
            #o = tichy.Setting.groups[group][i]
            #self.settings.append(o)
            
        def comp(m1, m2):
            if m1.name == None or m1.name == "":
                return cmp(m2, m1)
            else:  
                return cmp(m2.name, m1.name)
        
        self.list_label = list_label
        self.item_list = gui.elm_list(self.ItemList, self.window, self.edje_file, "group", list_label, comp)
        
        #for i in self.settings:
            #if hasattr(i, 'options'):
                #oid = i.options.connect('updated', self.item_list._redraw_view)
                #self.cb_list.append([i.options,oid])
        
        self.item_list.add_callback("*", "sublist", self.action)
    
        yield tichy.WaitFirst(tichy.Wait(self.window, 'delete_request'),tichy.Wait(self.edje_obj, 'back'))
    
        #for i in self.cb_list:
            #i[0].disconnect(i[1])

        self.edje_obj.elm_obj.visible_set(False)
        self.edje_obj.delete()
        self.item_list._remove_cb()
        layout.elm_obj.show()
        
    def action(self, emission, signal, source, item):
        item[0].action(item, self.parent, self.edje_obj)
        logger.info("action called")

class StringSettingApp(tichy.Application):
    name = "StringSetting"
    
    def run(self, setting, parent, layout):
        self.edje_file = os.path.join(os.path.dirname(__file__), 'settings.edj')
        
        layout.elm_obj.hide()
        self.window = gui.elm_list_subwindow(parent, self.edje_file, "stringsetting","entry", layout.elm_obj)
        self.edje_obj = self.window.main_layout
        
        self.edje_obj.Edje.signal_emit(str(setting.name),"set_text")
        
        textbox = gui.elementary.Entry(parent.window.elm_obj)

        textbox.entry_set("")
        
        textbox.size_hint_weight_set(1.0, 1.0)
        
        self.edje_obj.elm_obj.content_set("entry",textbox)
        
        textbox.editable_set(True)        
                  
        textbox.focus()
        
        textbox.show()
        
        i, args = yield tichy.WaitFirst(tichy.Wait(self.window.main_layout, 'save'), tichy.Wait(self.window.main_layout, 'back'),tichy.Wait(parent, 'back'))
        
        if i == 0: ##save clicked
            text = str(textbox.entry_get()).replace("<br>","")
            text = text.strip()
            self.edje_obj.Edje.signal_emit("save-notice","*")
            setting.set(text).start()
            
        self.edje_obj.elm_obj.visible_set(False)
        self.edje_obj.delete()
        layout.elm_obj.show()
