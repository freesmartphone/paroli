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

from tichy.object import Object
from tichy.item import Item
from tichy import tasklet
        

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

    def __init__(self, group, name, type, value=None, setter=None, **kargs):
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
        self.__value = type.as_type(value) if value is not None else type()
        self.__setter = setter or self.setter

        # register the setting into the list of all settings
        Setting.groups.setdefault(group, {})[name] = self

    @property
    def value(self):
        """accessor to the actual value"""
        return self.__value.value
        
    @tasklet.tasklet
    def setter(self, value):
        """tasklet that is called when we try to set the value This
        should perform the action needed to actually set the value.

        :Params:
            value : object
                The value we want to set
        """
        yield None

    @tasklet.tasklet
    def set(self, value):
        """Try to set the Setting value and block until it is done"""
        yield self.__setter(value)
        self.__value.value = value

    # Redirect `connect` and `disconnect` to the value
    def connect(self, *args, **kargs):
        return self.__value.connect(*args, **kargs)

    def disconnect(self, *args, **kargs):
        return self.__value.disconnect(*args, **kargs)


class FSOSetting(Setting):
    """Special setting class that hooks into a FSO preference

    It relies on the 'Prefs' service.
    """
    @property
    def value(self):
        """accessor to the actual value"""
        prefs = tichy.Service.get('Prefs')
        return prefs[self.group][self.name]

    @tasklet.tasklet
    def set(self, value):
        """Try to set the Setting value and block until it is done"""
        prefs = tichy.Service.get('Prefs')
        # XXX: make this asynchronous
        prefs[self.group][self.name] = value
        yield None

if __name__ == '__main__':
    # Simple usage example

    import tichy
    import logging
    logging.basicConfig()

    def set_volume(value):
        print "set volume to %s" % value
        yield None

    def on_volume_modified(value):
        print "volume changed to %d" % value

    @tichy.tasklet.tasklet
    def my_task():
        volume = Setting('phone', 'volume', tichy.Int, setter=set_volume)
        Setting.groups['phone']['volume'].connect('modified', on_volume_modified)
        # Here we could also write :
        # volume.connect('modified', on_volume_modified)
        yield volume.set(10)
        assert volume.value == 10
        print "Done"

    my_task().start()

