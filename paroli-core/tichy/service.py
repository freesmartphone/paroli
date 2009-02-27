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

import tichy
from object import Object

from item import Item, ItemMetaClass

import logging
logger = logging.getLogger('Service')

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

    # This attribute is a dict of list : (service_name -> [service_cls])
    __all_services = {}
    # This is used to store the sigleton value of the service
    __singleton = None

    service = None
    name = None

    @classmethod
    @tichy.tasklet.tasklet
    def init_all(cls, defaults={}):
        logger.info("init all services")
        logger.info("defaults service are %s", defaults)
        for service_cls in cls.subclasses:
            service = service_cls.service
            name = service_cls.name
            if not service:
                logger.debug("skip service %s : no name", service_cls)
                continue
            if service in cls.__all_services:
                logger.debug("skip service %s : already there", service_cls)
                continue
            if service in defaults and name != defaults[service]:
                logger.debug("skip service %s : no default", service_cls)
                continue
            logger.debug("register service %s : %s", service, name)
            instance = service_cls()
            cls.__all_services[service] = instance

        for service in cls.__all_services.values():
            service._init().start()
        logger.info("waiting for all services to init")
        for service in cls.__all_services.values():
            yield service.wait_initialized()
        logger.info("all services have been initialized")

    def __init__(self):
        super(Service, self).__init__()
        self.initialized = False

    @tichy.tasklet.tasklet
    def _init(self):
        logger.debug("init service %s", self.service)
        yield self.init()
        logger.debug("init service %s done", self.service)
        self.initialized = True
        self.emit('initialized')

    @tichy.tasklet.tasklet
    def wait_initialized(self):
        if not self.initialized:
            logger.debug("Wait for %s %s", self.service, id(self))
            yield tichy.tasklet.Wait(self, 'initialized')
            logger.debug("Done waiting for %s", self.service)

    @tichy.tasklet.tasklet
    def init(self):
        yield None

    @staticmethod
    def get(name):
        """Get a service instance by name

        We are supposed to only call this after the service have been
        initialized.
        """
        try:
            return Service.__all_services[name]
        except KeyError:
            # This is a hack to allow plugins to require service
            # before they have been initialized. It should be avoided,
            # and so we log a warning in that case.
            if name not in [x.service for x in Service.subclasses]:
                raise
            msg = "trying to access service '%s' before call to init"
            logger.warning(msg, name)
            cls = [x for x in Service.subclasses if x.service == name][0]
            instance = cls()
            Service.__all_services[name] = instance
            return instance

def get(name):
    return Service.get(name)
