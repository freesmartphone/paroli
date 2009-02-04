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

    def __init__(self, peer, text, direction, status=None, timestamp=None, sim_index=None,sim_imsi=None,msg_hash=None):
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
        
        storage = None
        
        if sim_imsi == None:
            sim_imsi = tichy.Service('SIM').sim_info['imsi']
        
        self.peer = TelNumber.as_type(peer)
        self.text = tichy.Text.as_type(text)
        self.sim_index = sim_index
        self.sim_imsi = sim_imsi
        #TODO: fix timestamp to recognize timezones        
        import time
        if timestamp == None:
            my_time = time.localtime()
        else:
            my_time = timestamp[:24]
        self.timestamp = tichy.Time.as_time(my_time)
        assert direction in ['in', 'out'], direction
        self.direction = direction
        self.status = status or direction == 'out' and 'read' or 'unread'
        assert self.status in ['read', 'unread'], status
        self.msg_hash = str(self.sim_imsi)+str(self.sim_index)+str(self.timestamp)

    def get_text(self):
        return tichy.Text("%s" % str(self.msg_hash))

    def read(self):
        """Mark the message as read

        This will set the status of the message to 'read' and also
        send the 'read' signal.
        """
        if self.status == 'read':
            return
        self.status = 'read'
        self.emit('read')

    def create_actor(self):
        """Return an actor on this message"""
        actor = super(Message, self).create_actor()

        def on_view_action(action, msg, view):
            self.read()
            yield self.edit(view.window)
        view_action = actor.new_action("View")
        view_action.connect('activated', on_view_action)

        def on_details_action(action, msg, view):
            yield self.view_details(view.window)
        details_action = actor.new_action("Details")
        details_action.connect('activated', on_details_action)

        return actor

    def edit(self, window):
        """Return a `tasklet` that can be used to edit the message

        :Parameters:

            window : gui.Widget
               The window where we start the edit application
        """
        editor = tichy.Service('EditMessage')
        yield editor.edit(self, window)

    def view_details(self, window):
        """return a `Tasklet` that can be used to view the message details

        :Parameters:

            window : gui.Widget
               The window where we start the application
        """
        editor = tichy.Service('EditMessage')
        yield editor.view_details(self, window)

    @tichy.tasklet.tasklet
    def send(self, sms):
        """Tasklet that will send the message"""
        raise NotImplementedError

    def to_dict(self):
        """return the message attributes in a python dict"""
        service = tichy.Service('SIM')
        return {'peer': str(self.peer),
                'text': str(self.text),
                'timestamp': str(self.timestamp),
                'direction': self.direction,
                'status': self.status,
                'sim_index': self.sim_index,
                'sim_imsi': service.sim_info['imsi'],
                'msg_hash': self.msg_hash}

class PhoneMessage(Message):
    """Message that is stored on the phone"""

    storage = 'Phone'

    #peer = TelNumber.as_type(peer)
    #text = tichy.Text.as_type(text)
    #timestamp = tichy.Time.as_time(timestamp)
    #direction = tichy.Text.as_type(text)
    #status = tichy.Text.as_type(text)
    #fields = [name, text, timestamp, direction, status]

    def __init__(self, **kargs):
        super(PhoneMessage, self).__init__(**kargs)
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
        """Save all the phone contacts"""
        logger.info("Saving phone messages")
        messages = tichy.Service('Messages').messages
        data = [c.to_dict() for c in messages if isinstance(c, PhoneMessage)]
        tichy.Persistance('messages/Phone').save(data)
        yield None

    @classmethod
    def load(cls):
        """Load all the phone contacts

        Return a list of all the contacts
        """
        logger.info("Loading phone messages")
        ret = []
        data = tichy.Persistance('messages/phone').load()
        for kargs in data:
            message = PhoneMessage(**kargs)
            ret.append(message)
        yield ret
        
    def __get_number(self):
        return self.peer
    number = property(__get_number)

    @tichy.tasklet.tasklet
    def send(self):
        """Tasklet that will send the message"""
        sms_service = tichy.Service('SMS')
        yield sms_service.send(self)

class MessagesService(tichy.Service):
    """The service that stores all the messages

    This service provides access to the messages inbox and outbox
    """

    service = 'Messages'

    def __init__(self):
        self.outbox = tichy.List()
        self.inbox = tichy.List()
        self.messages = tichy.List()
        # Prepare the future notification
        self.notification = None
        self.ready = False

    @tichy.tasklet.tasklet
    def init(self):
        yield self._load_all()
        self.emit('ready')
        self.ready = True
        self.outbox.connect('modified', self._on_lists_modified)
        self.inbox.connect('modified', self._on_lists_modified)
        self.messages.connect('modified', self._on_lists_modified)

    def _on_lists_modified(self, box):
        yield self._save_all()

    def add_to_inbox(self, msg):
        """Add a `Message` into the inbox

        :Parameters:
            msg : `Message`
                The message we add
        """
        logger.info("Add to inbox : %s", msg)
        assert(isinstance(msg, Message))
        self.inbox.insert(0, msg)
        if msg.status != 'read':
            msg.connect('read', self.on_message_read)
        self._update()

    def add_to_outbox(self, msg):
        """Add a `Message` into the outbox

        :Parameters:
            msg : `Message`
                The message we add
        """

        logger.info("Add to outbox : %s", msg)
        assert(isinstance(msg, Message))
        self.outbox.insert(0, msg)

    def add_to_messages(self, msg):
        """Add a `Message` into the outbox

        :Parameters:
            msg : `Message`
                The message we add
        """

        logger.info("Add to messages : %s", msg)
        assert(isinstance(msg, Message))
        self.messages.append(msg)

    def delete_message(self,msg):
        current_imsi = tichy.Service('SIM').sim_info['imsi']
        if msg.sim_imsi == current_imsi:
            logger.info('deleting message: ' + msg.sim_index)
            try:
                tichy.Service('SIM').remove_message(msg)
            except Exception, e:
                print e
        self.messages.remove(msg)

    def on_message_read(self, msg):
        self._update()

    def _update(self):
        """Update the notification according to the number of unread messages
        in the inbox.
        """
        nb_unread = len([m for m in self.messages if m.status == 'unread'])
        logger.debug("%d unread messages", nb_unread)
        if nb_unread == 0 and self.notification:
            self.notification.release()
            self.notification = None
        elif nb_unread > 0 and not self.notification:
            notifications = tichy.Service('Notifications')
            self.notification = notifications.notify(
                "You have a new message")
        elif nb_unread > 0 and self.notification:
            self.notification.msg = "You have %d unread messages" % nb_unread

    @tichy.tasklet.tasklet
    def _load_all(self):
        logger.info("load all messages")
        """load all the messages from all sources"""
        # TODO: make this coherent with contacts service method
        all_messages = []
        for cls in Message.subclasses:
            logger.info("loading messages from %s", cls.storage)
            try:
                #print cls
                messages = yield cls.load() 
                logger.info("Got %d messages from %s", len(messages),
                            cls.storage)
            except Exception, ex:
                logger.warning("can't get messages : %s", ex)
                continue
            assert all(isinstance(x, Message) for x in messages)
            hashes_before = []
            for z in all_messages:
                hashes_before.append(z.msg_hash)
            for x in messages:
              if x.msg_hash not in hashes_before:
                all_messages.append(x)
        self.messages[:] = all_messages
        logger.info("Totally got %d messages", len(self.messages))


    @tichy.tasklet.tasklet
    def _save_all(self):
        logger.info("save all messages")
        #for x in self.messages:
          #print x.msg_hash
          #print x.sim_index
        data = [x.to_dict() for x in self.messages]
        #print dir(data)
        
        #print data.keys()
        tichy.Persistance('messages/phone').save(data)
        yield None
