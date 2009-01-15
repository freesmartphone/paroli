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

__docformat__ = 'reStructuredText'

from object import Object

from item import Item, ItemMetaClass

import logging
logger = logging.getLogger('Service')

# TODO : Try to fix the mess with the way services work internaly. In
#        the best case I shoud be able to create a new service by
#        giving an other service as a parent class : e.g : class
#        TestGSM(Service(GSM)): pass. But I don't know how to do that
#        correctly...


class BaseService(Item):
    """Base class for all services

    This class is used to have a common class associated with all
    service with the same 'service' attribute

    To define a new service, it is enough to create a class that
    inherit from the Service class. The service should have a
    'service' attribute with the name of the service. e.g :

    class MyService(Service):
        service = 'MyService'

    All the services are singleton and paroli will take care to create
    them and keep track of there instances.
    
    when a plugin/application need to use a given service, it create
    it like this :

    my_service = Service('MyService')

    paroli will return a service that as the given name. There are
    some additional mechanism to let paroli decide which service to
    use but it is not important.

    So why is it convenient to use this Service class ? Because then
    you can have several implementation of the same service, and the
    context decide *dynamically* which one is going to be used.

    Coupled with the plugin system this is very powerful because it
    let the plugins redefine internal behavior of paroli (it is in
    fact a kind of chain of responsibilty pattern)

    For example at initialization paroli may need to get a PIN code
    from the user. Do do so it will request the 'TextEdit'
    service. Then it is assumed that one of the plugins did register
    this service.
    """

    def __init__(self, service):
        self.service = service


class ServiceMetaClass(ItemMetaClass):
    """The meta class for Service class"""

    def __init__(cls, name, bases, dict):
        """Register a service class
        """
        if 'service' in dict:
            service_name = dict['service']
            if not cls.name:
                cls.name = cls.__name__
            if '__init__' in dict:
                cls._Service__init = dict['__init__']
                cls.__init__ = Service.__init__
            logger.debug("Register %s as service %s", cls, service_name)
            Service.__dict__['_Service__all_services'].setdefault(
                service_name, []).append(cls)
            service_bases = Service.__dict__['_Service__bases']
            if service_name not in service_bases:
                service_bases[service_name] = \
                    BaseService(service_name)
            cls.base = service_bases[service_name]
        ItemMetaClass.__init__(cls, name, bases, dict)


class ServiceUnusable(Exception):
    """Exception raised by a service if it not usable

    The service module will then try to use an other service.
    """

    def __init__(self, msg=None):
        super(ServiceUnusable, self).__init__(msg)


class Service(Item):
    """Service base class

    The service class is used by plugin to expose some functionalities
    that could be used by other plugins.

    A given service is defined by its `service` attribute, wich should
    be a string. All the services sharing the same name should have
    the same interface. When a plugin wants to use a service, it can
    get the most suitable service available by using the Service
    function (thanks to some python magic, Service can be used bot as
    a class name and a function).

    A service is also an item, so it can have a `name` attribute.
    """

    __metaclass__ = ServiceMetaClass
    # This attribute is a dict of list : (service_name -> [service_cls])
    __all_services = {}
    # A dict of the form (service_name -> service)
    __defaults = {}
    # Every service has a base service object associated This is used
    # to have a common object associated with all service of the same
    # group This object is put into the `base` attribute of every
    # service classes. That is a little bit tricky !
    __bases = {}

    # This is used to store the sigleton value of the service
    __singleton = None

    enabled = True
    name = None

    @classmethod
    def set_default(cls, service, default):
        """Set a given service as the default one"""
        if isinstance(default, str):
            default = Service(service, default)
        if cls.__defaults.get(service, None) == default:
            return
        cls.__defaults[service] = default
        Service.__bases[service].emit("changed", default)

    @classmethod
    def is_default(cls):
        """return true if a service is the default one"""
        default = cls.__defaults.get(cls.service, None)
        return default and isinstance(default, cls)

    @classmethod
    def get_all(cls, name):
        """return all the service that have a given name

        :Parameters:

            name : str
                The name of the service
        """
        ret = []
        for service in Service.__all_services.get(name, []):
            try:
                instance = service.__get()
                if not instance.enabled:
                    continue
                ret.append(instance)
            except ServiceUnusable:
                logger.warning("service %s unusable, skipped", service)
        return ret

    def __new__(cls, service=None, name=None):
        """Return a service instance that implement a given service

        :Parameters:

            service : str
                The service name

            name : str or None
                If given, specify the actual service name we want
        """
        logger.debug("try to get service %s", service)

        if service is None:
            return Item.__new__(cls)

        all_services = Service.__all_services.get(service, [])

        if service in cls.__defaults:
            all_services = [cls.__defaults[service]] + all_services

        for service_cls in all_services:
            if name and service_cls.name != name:
                continue
            try:
                ret = service_cls.__get()
                if not ret.enabled:
                    continue
                return ret
            except ServiceUnusable:
                logger.warning("service %s unusable, skipped", service_cls)
        raise KeyError("can't find any service '%s:%s'" % (service, name))

    def __init__(self, service=None, name=None):
        super(Service, self).__init__()

    def __init(self):
        pass

    @classmethod
    def __get(cls):
        """return the single service instance"""
        if cls.__singleton is None:
            singleton = cls()
            singleton.__init()
            cls.__singleton = singleton
        return cls.__singleton


# TODO: add more introspection of the services, we should be able to
#       get all the methods defined by a service as well

def print_infos():
    """print some info about all the registered services"""
    print "All services :"
    print
    for name, clss in Service._Service__all_services.items():
        print "Service '%s' :" % name
        for cls in clss:
            print "  * %s" % cls.name or 'unnamed',
            if cls.is_default():
                print " [default]"
            else:
                print
