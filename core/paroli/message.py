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
logger = logging.getLogger('core.paroli.messages')


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
        assert self.status in ['read', 'unread', 'unsent', 'sent'], status

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

    def __init__(self, peer, text, direction, status=None, **kargs):
        super(PhoneMessage, self).__init__(peer, text, direction, status, **kargs)
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
        if data:
            for kargs in data:
                try:
                    message = PhoneMessage(**kargs)
                    ret.append(message)
                except Exception, ex:
                    logger.exception("can't create message : %s", ex)
        yield ret
        
    def __get_number(self):
        return self.peer
    number = property(__get_number)

class SMS(Message):

    storage = 'SIM'

    def __init__(self, peer, text, direction, status=None, timestamp=None,
                 sim_index=None, **kargs):
        super(SMS, self).__init__(peer, text, direction,
                                         status=status, timestamp=timestamp,
                                         sim_index=sim_index, **kargs)
        self.sim_index = sim_index

    @classmethod
    def import_(cls, contact):
        """create a new contact from an other contact)
        """
        assert not isinstance(message, PhoneMessage)
        ret = PhoneMessage(peer=message.peer,text=message.text,timestamp=message.timestamp,direction=message.direction,status=message.status)
        yield ret

    def delete(self):
        sim = tichy.Service.get('SIM')
        yield sim.remove_message(self)

    def save(self):
        logger.warning("save SIM message not implemented yet")
        yield None

    @classmethod
    @tichy.tasklet.tasklet
    def load_all(cls):
        sim = tichy.Service.get('SIM')
        yield sim.wait_initialized()
        ret = yield sim.get_messages()
        yield ret

