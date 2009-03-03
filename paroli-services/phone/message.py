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

"""Message module"""

import logging
logger = logging.getLogger('Messages')

import tichy
from tel_number import TelNumber



class Message(tichy.Item):
    """Base class for all messages
    """

    def __init__(self, peer, text, direction, status=None, timestamp=None, **kargs):
        """Create a new message

        :Parameters:

            peer : `TelNumber` | str
                the number / contact of the peer of the message. Its
                __repr__ method will be used as the item's name.

            text : `Text` | unicode
                The text of the message

            direction : str
                the direction of the message. Can be 'in' or 'out'

            status : str
                the status of the message. Can be 'read' or
                'unread'. If set to None, incoming message will have
                'unread' status and outgoing message will have 'read'
                status

            timestamp
                the time at which we received the message. If set to
                None we use the current time
        """
        super(Message, self).__init__()
        storage = None
        
        self.peer = TelNumber.as_type(peer)
        self.text = tichy.Text.as_type(text)
        self.timestamp = tichy.Time.as_type(timestamp)
        # TODO: use a boolean here
        assert direction in ['in', 'out'], direction
        self.direction = direction
        self.status = status or direction == 'out' and 'read' or 'unread'
        assert self.status in ['read', 'unread'], status

    def get_text(self):
        return self.text

    def read(self):
        """Mark the message as read

        This will set the status of the message to 'read' and also
        send the 'read' signal.
        """
        if self.status == 'read':
            return
        self.status = 'read'
        self.emit('read')
        self.emit('modified')

    def save(self):
        raise NotImplementedError('save not implemeted for %s' % type(self))

    @tichy.tasklet.tasklet
    def send(self):
        """Tasklet that will send the message"""
        ret = yield tichy.Service.get('SMS').send(self)
        yield ret

    def to_dict(self):
        """return the message attributes in a python dict"""
        service = tichy.Service.get('SIM')
        return {'peer': str(self.peer),
                'text': unicode(self.text),
                'timestamp': str(self.timestamp),
                'direction': self.direction,
                'status': self.status}

class PhoneMessage(Message):
    """Message that is stored on the phone"""

    storage = 'Phone'

    def __init__(self, peer, text, direction, **kargs):
        super(PhoneMessage, self).__init__(peer, text, direction, **kargs)
        self.connect('modified', self._on_modified)

    def _on_modified(self, message):
        logger.info("Phone message modified %s message", message)
        yield self.save()

    @classmethod
    def import_(cls, message):
        """import a contact into the phone"""
        assert not isinstance(message, PhoneMessage)
        yield PhoneMessage(peer=message.peer,text=message.text,timestamp=message.timestamp,direction=message.direction,status=message.status)

    @classmethod
    def save(cls):
        """Save all the phone messages"""
        logger.info("Saving phone messages")
        messages = tichy.Service.get('Messages').messages
        data = [c.to_dict() for c in messages if isinstance(c, PhoneMessage)]
        tichy.Persistance('messages/phone').save(data)
        yield None

    @classmethod
    def delete(cls):
        """Delete the message from the phone memory"""
        # In fact we re-save every messages
        yield cls.save()


    @classmethod
    def load_all(cls):
        """Load all the phone msgs

        Return a list of all the contacts
        """
        logger.info("Loading phone messages")
        ret = []
        data = tichy.Persistance('messages/phone').load()
        for kargs in data:
            try:
                message = PhoneMessage(**kargs)
                ret.append(message)
            except Exception, ex:
                logger.error("can't create message : %s", ex)
        yield ret
        
    def __get_number(self):
        return self.peer
    number = property(__get_number)

class MessagesService(tichy.Service):
    """The service that stores all the messages

    This service provides access to the messages inbox and outbox
    """

    service = 'Messages'

    def __init__(self):
        super(MessagesService, self).__init__()
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
        logger.info("Add to messages : %s", msg)
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
        logger.info("load all messages")
        """load all the messages from all sources"""
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
                logger.warning("can't get messages : %s", ex)
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

    def create(self, number, text, direction, **kargs):
        """Create a new message
        The arguments are the same as `Message.__init__`
        """
        msg = PhoneMessage(number, text, direction, **kargs)
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
