#    Settings app
#
#    copyright 2008 Openmoko
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
logger = logging.getLogger('hello_world')

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
        self.window = gui.elm_list_window(self.edje_file, "main", "list")
        self.edje_obj = self.window.main_layout
        
        self.groups = tichy.List()
        
        for i in tichy.Setting.groups:
            #print tichy.Setting.groups[i]
            t = tichy.Text(i)
            self.groups.append(tichy.Text(i))
        
        def comp(m1, m2):
            return cmp(m2.lower(), m1.lower())
        
        self.list_label = [('title', 'value')]
        self.item_list = gui.elm_list(self.groups, self.window, self.edje_file, "group", self.list_label, comp)
        
        self.item_list.add_callback("*", "sublist", self._show_sublist)
        
        yield tichy.WaitFirst(tichy.Wait(self.window, 'delete_request'),tichy.Wait(self.window, 'back'))
        #,tichy.Wait(self.button, 'aux_button_pressed')
        ##we write a logger message that the application is closing
        logger.info('Settings closing')
        
        ##we delete the window object (the class would also delete all children object)
        del self.groups
        self.window.delete()
        
    def _show_sublist(self, emission, signal, source, group):
        logger.info("showing sublist from group %s", str(group[0]))
        SettingsSublist(self.window, self.edje_file, str(group[0]), self.edje_obj).start()

class SettingsSublist(tichy.Application):
    
    name = 'SettingsSublist'

    def run(self, parent, edje_file, group, layout, *args, **kargs):
    
        while True:
            layout.elm_obj.hide()
          
            self.window = gui.elm_list_subwindow(parent, edje_file, "main", "list")
            self.edje_obj = self.window.main_layout
            
            self.edje_obj.Edje.signal_emit("sublist_mode","*")
            
            self.settings = tichy.List()
            self.cb_list = tichy.List()
            self.prefs = tichy.Service.get("Prefs")
            self.group_service = self.prefs.Service(self.prefs, group)
            
            for i in tichy.Setting.groups[group]:
                o = tichy.Setting.groups[group][i]
                self.settings.append(o)
                print type(o)
                
            def comp(m1, m2):
                return cmp(m2.name, m1.name)
            
            self.list_label = [('title', 'name'),('subtitle', 'value')]
            self.item_list = gui.elm_list(self.settings, self.window, edje_file, "group", self.list_label, comp)
        
            for i in self.settings:
                oid = i.options.connect('updated', self.item_list._redraw_view)
                self.cb_list.append([i.options,oid])
            
            self.item_list.add_callback("*", "sublist", self.action)
        
            yield tichy.WaitFirst(tichy.Wait(self.window, 'delete_request'),tichy.Wait(self.edje_obj, 'back'))
        
            for i in self.cb_list:
                i[0].disconnect(i[1])
            self.edje_obj.delete()
            parent.restore_orig()
            layout.elm_obj.show()
        
    def action(self, emission, signal, source, item):
        item[0].rotate()
        
        #self.service_service = tichy.Service('SettingsService')
        #self.button = tichy.Service('Buttons')
        
        #box = gui.edje_box(self,'V',1)
        #box.box.show()
        
        #for name, clss in Service._Service__all_services.items() :
            
            #for cls in clss:
                #if hasattr(cls,'settings'):
                    #print cls
                    #for s in cls.settings:
                        #print s
                        ###create canvas
                        #canvas = gui.etk.Canvas()
                        ###create edje object depending on option
                        #button = gui.EdjeObject(self.window, self.edje_file, s[3] + '_setting')
                        ###add edje to canvas
                        #canvas.object_add(button.Edje)
                        ###append canvas to box
                        #box.box.append(canvas, gui.etk.VBox.START, gui.etk.VBox.NONE, 0)
                        ###set text
                        #subtitle = getattr(tichy.Service(cls.service), s[1])()
                        #button.Edje.part_text_set("title", s[0])
                        #button.Edje.part_text_set("subtitle", subtitle)
                        
                        #button.Edje.signal_callback_add("callback", "*", self.toggle, cls.service, s[2])
                        
                        #button.Edje.layer_set(5)
                        #button.Edje.show()
        
        ###create the main gui object
        ### the gui.EdjeObject class needs 3 arguments:
        ### 1: a gui.Window object
        ### 2: and edje file
        ### 3: the group in the given edje file it should create the object from
        #self.edje_obj = gui.EdjeWSwallow(self.window, self.edje_file, 'main', 'swallow')
        
        #self.edje_obj.embed(box.scrolled_view,box,"swallow")
        #box.box.show()
        ###we lower the gui object to allow paroli's top-bar to be used
        #self.edje_obj.Edje.pos_set(40,70)
        
        #self.edje_obj.Edje.size_set(400, 500)
        
        ###the EdjeObject class is initialized hidden by default, so we need to show it
        #self.edje_obj.show()
        
        ##add the callback to the edje object to listen for certain signals from the gui
        ## the add_callback method takes three arguments:
        ## 1: the signal to listen for
        ## 2: the source of the signal
        ## 3: the function to call when the signal is received
        ## the first 2 arguments must be the same as used in the corresponding edc program
        #self.edje_obj.add_callback("button-pressed","gui",self.button_pressed)
        #self.edje_obj.add_callback("service-button-pressed","gui",self.service_button_pressed)
        
        ##applications are scripts that are kept running until a certain signal is emitted by the main gui object everything after this statement will only be executed once the application is closed - the signal is emitted by launcher, so no further funcitons needed here
        #the signal could also be comming from the window-manager so we prepare this for both events
    
    #def toggle(self, emission, signal, source, name, func):
        #new = getattr(tichy.Service(name),func)()
        #emission.part_text_set("subtitle", new)


## a basic service that does nothing but deliver a static value
#class SettingsService(tichy.Service):
    ### this is the service's name which is used to get the service and run methods etc
    #service = 'SettingsService'
    
    ###the init function sets our static value and initializes the class itself
    #def __init__(self):
        #super(SettingsService, self).__init__()
    
    #def get_all_settings(self):
        #ret = []
        #for cls in SettingsService.subclasses:
            #ret.append(cls)
        
        #return ret
        
#class SettingsToggle(SettingsService):
    
    #service = "monoservice"
    #option = "mono"
    
    #def __init__(self, func):
          #super(MonoService, self).__init__()
          #self.func = func
    
    #def toggle():
        #self.func()