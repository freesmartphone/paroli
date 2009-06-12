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
"""Notifications module"""
import logging
logger = logging.getLogger('core.tichy.notifications')

__docformat__ = 'reStructuredText'

from service import Service
from item import Item


class Notification(Item):
    """Notification class

    Notifications can be used by plugin to notify the user of an event
    or a condition. A typical example is to signal an unread message.

    The plugin should use the 'Notifications' service to create new
    notifications.

    Signals:

        'released'
            emitted when the notification is released and shouldn't be
            taken care of anymore.

        'modified'
            emitted when the message of a notification has beed
            modified
    """

    def __init__(self, service, msg, icon=None):
        super(Notification, self).__init__()
        self.service = service
        self.__msg = msg
        self.icon = icon

    def __get_msg(self):
        return self.__msg

    def __set_msg(self, msg):
        self.__msg = msg
        self.emit('modified')

    msg = property(__get_msg, __set_msg)

    def __repr__(self):
        return str(self.msg)

    def release(self):
        """To be called when the notification can be removed"""
        if self not in self.service.notifications:
            return
        self.service._remove(self)
        self.emit('released')


class Notifications(Service):
    """Notification service

    This service can be used by any plugin that wants to notify the
    user about something, but doesn't want to open a new window for
    that. That is useful for things like notify incoming SMS, etc.

    The system can see all the pending notifications, and also be
    notified whenever a new notification arrives.

    Signals

        'new-notification'
            emitted when a new notification arrives
    """
    service = 'Notifications'

    def __init__(self):
        self.notifications = []

    def notify(self, msg, icon=None):
        """add a new notification

        :Parameters:

            msg : `Text` or unicode
                the message of the notification

            icon : `Image`
                an optional icon for the notification
        """
        notification = Notification(self, msg, icon)
        self.notifications.append(notification)
        logger.info("Notify : %s", notification)
        self.emit('new-notification', notification)
        return notification

    def _remove(self, notification):
        logger.info("Remove : %s", notification)
        self.notifications.remove(notification)
