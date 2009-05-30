# -*- coding: utf-8 -*-
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

__docformat__ = 'reStructuredText'

import tichy
from paroli.tel_number import TelNumber

import logging
logger = logging.getLogger('service.misc.messages')



class MessagesService(tichy.Service):
    """The service that stores all the messages

    This service provides access to the messages inbox and outbox
    """

    service = 'Messages'

    def __init__(self):
        super(FallbackMessagesService, self).__init__()
        self.messages = tichy.List()
        self.unread = tichy.Text(0)
        self.messages.connect('appended',self._update_unread)
        self.ready = False

    @tichy.tasklet.tasklet
    def init(self):
        yield self._load_all()
        self.emit('ready')
        self.ready = True

    @tichy.tasklet.tasklet
    def add(self, msg):
        """Add a `Message` into the message list

        :Parameters:
            msg : `Message`
                The message we add
        """
        logger.info("Add to messages : %s", unicode(msg).encode("utf-8"))
        assert isinstance(msg, Message)
        self.messages.append(msg)
        yield msg.save()

    @tichy.tasklet.tasklet
    def remove(self, msg):
        """remove a `Message` from the message list

        :Parameters:
            msg : `Message`
                The message we remove
        """
        logger.info("Remove from messages : %s", msg)
        assert isinstance(msg, Message)
        assert msg in self.messages
        self.messages.remove(msg)
        yield msg.delete()

    @tichy.tasklet.tasklet
    def _load_all(self):
        """load all the messages from all sources"""
        logger.info("load all messages")
        # TODO: make this coherent with contacts service method
        all_messages = []
        for cls in Message.subclasses:
            logger.info("loading messages from %s", cls.storage)
            try:
                messages = yield cls.load_all()
                logger.info("Got %d messages from %s", len(messages),
                            cls.storage)
                all_messages += messages
            except Exception, ex:
                logger.exception("can't get messages : %s", ex)
                continue
            assert all(isinstance(x, Message) for x in messages)
        self.messages[:] = all_messages
        self._update_unread()
        logger.info("Totally got %d messages", len(self.messages))


    @tichy.tasklet.tasklet
    def _save_all(self):
        logger.info("save all messages")
        for cls in Message.subclasses:
            logger.info("save all messages of type %s", cls.storage)
            cls._save_all()

    def create(self, number, text, direction, status=None,**kargs):
        """Create a new message
        The arguments are the same as `Message.__init__`
        """
        msg = PhoneMessage(number, text, direction, status, **kargs)
        if msg.status == 'unread':
            msg.connect('read',self._update_unread)
        return msg

    def _update_unread(self, *args, **kargs):
        self.unread.value = int(0)
        for msg in self.messages:
            if msg.status == 'unread':
                msg.connect('read',self._update_unread)
                self.unread.value = int(self.unread.value)+1
                
        self.unread.emit('updated')
        logger.debug("unread message count now: %s in total", self.unread)

