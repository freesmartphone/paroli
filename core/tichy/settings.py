# -*- coding: utf-8 -*-
#    Paroli
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
import logging
logger = logging.getLogger('core.tichy.settings')

from object import Object
from item import Item
from list import List
from int import Int
from tasklet import tasklet
from service import Service
from object import Object

class Setting(Object):
    """Represents a setting value

    Setting values are similar to Item, but allow to give more
    information about there type and the values they can contain.

    Setting can also be linked to external state, so setting a Setting
    value is an asynchronise operation.

    All the settings value are stored into the Setting.groups
    dictionnary, which could be used for example for a setting
    application who needs to know about all the settings in the
    system.
    """

    # contains a map : { group : { name : setting } }
    groups = {}

    def __init__(self, group, name, type, value=None, setter=None, options="", listenObject=False, signal=False, arrayElement=False, **kargs):
        """Create a new setting

        :Parameters:
           group : str
               The group the setting belongs to.

           name : str
               The actual name of the setting

           type : tichy.Item
               The type of the setting value. This should be a
               tichy.Item, so we need to use tichy.Int instead of int,
               tichy.Text instead of str, etc..

           value
               Optional intialization value

           setter
               A tasklet that will be called every time we try to set
               the Setting value. It takes the new value as
               argument. The Setting value will actually be set
               only after this tasklet returns.
        """
        assert issubclass(type, Item), type
        self.group = group
        self.name = name
        self.type = type
        self.Value = type.as_type(value) if value is not None else type()
        self.Setter = setter or self.setter
        self.options = List(options)
        self.arrayElement = arrayElement
        
        if listenObject:
            listenObject.connect_to_signal(signal, self.change_val)

        # register the setting into the list of all settings
        Setting.groups.setdefault(group, {})[name] = self

    @property
    def value(self):
        """accessor to the actual value"""
        return self.Value.value

    @tasklet
    def setter(self, value):
        """tasklet that is called when we try to set the value This
        should perform the action needed to actually set the value.

        :Params:
            value : object
                The value we want to set
        """
        yield None

    @tasklet
    def set(self, value):
        """Try to set the Setting value and block until it is done"""
        if value == None:
            value = ''
        yield self.Setter(value)
        self.Value.value = value
        self.options.emit('updated')
        logger.info("%s set to %s", self.name, self.value)

    def rotate(self, *args):
        if self.value != None:
            if self.options.count(self.value) != 0:
                current_index = self.options.index(self.value)
                logger.info("current index: %d", current_index)
                if len(self.options)-1 == current_index:
                    new = self.options[0]
                else:
                    new = self.options[current_index + 1]
            else:
                new = self.options[0]

            logger.info("new value: %s", new)
            self.set(new).start()

    def change_val(self, val):
        logger.info("set to: %s", val)
        self.Value.value = val
        self.options.emit('updated')

    # Redirect `connect` and `disconnect` to the value
    def connect(self, *args, **kargs):
        return self.Value.connect(*args, **kargs)

    def disconnect(self, *args, **kargs):
        return self.Value.disconnect(*args, **kargs)


class StringSetting(Setting):
    """ Setting for string values, on click it will produce a text-edit dialog and show a kbd
    """

    def rotate(self, parent, layout):
        fe = Service.get("FreeEdit")
        fe.StringEdit(self, parent, layout).start()

class NumberSetting(Setting):
    """ Setting for string values, on click it will produce a text-edit dialog and show a kbd
    """

    def rotate(self, parent, layout):
        fe = Service.get("FreeEdit")
        fe.NumberEdit(self, parent, layout).start()

class ListSetting(Setting):
    """ Setting for List values, on click it will produce a list-window
    """

    def __init__(self, group, name, type, value=None, setter=None, options="", model=None, ListLabel=None, edje_group=None, save_button=False, **kargs):

        assert issubclass(type, Item), type
        self.group = group
        self.edje_group = edje_group
        self.save_button = save_button
        self.name = name
        self.type = type
        self.Value = type.as_type(value) if value is not None else type()
        self.Setter = setter or self.setter
        self.options = List(options)

        self.model = model
        self.ListLabel = ListLabel

        # register the setting into the list of all settings
        Setting.groups.setdefault(group, {})[name] = self

    def rotate(self, parent, layout):
        self.Setter("scan").start()
        fe = Service.get("FreeEdit")
        fe.ListEdit(self, parent, self.model, self.ListLabel, layout, self.edje_group, self.save_button).start()

class ToggleSetting(Setting):
    """ Setting for toggle values, on click it will only start an action, nothing else, it sends the value along, so that it can be changed by the setter
    """

    def sub_init(self):
        self.listenObject.connect_to_signal(signal, self.change_val)

    def change_val(self, val):
        logger.info("status change")
        if self.arrayElement:
            val = val[self.arrayElement]
        #self.Value.value = val
        self.preset(val).start()
    
    @tasklet
    def preset(self, val):
        yield self.set(val)

    def rotate(self, *args):
        self.set(self.value).start()

    @tasklet
    def set(self, value):
        """Try to set the Setting value and block until it is done"""
        val = yield self.Setter(value)
        self.Value.value = val
        self.options.emit('updated')
        logger.info("%s set to %s", self.name, self.value)

if __name__ == '__main__':
    # Simple usage example

    import logging
    logging.basicConfig()

    def set_volume(value):
        logger.debug( "set volume to %s", value)
        yield None

    def on_volume_modified(value):
        logger.debug( "volume changed to %d", value)

    @tasklet
    def my_task():
        volume = Setting('phone', 'volume', Int, setter=set_volume)
        Setting.groups['phone']['volume'].connect('modified', on_volume_modified)
        # Here we could also write :
        # volume.connect('modified', on_volume_modified)
        yield volume.set(10)
        assert volume.value == 10
        logger.debug("Done")

    my_task().start()

