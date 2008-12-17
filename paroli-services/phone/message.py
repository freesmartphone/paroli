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


class Message(tichy.Item):
    """Base class for all messages
    """

    def __init__(self, peer, text, direction, status=None, timestamp=None):
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
        self.peer = tichy.TelNumber.as_type(peer)
        self.text = tichy.Text.as_type(text)
        self.timestamp = tichy.Time.as_time(timestamp)
        assert direction in ['in', 'out'], direction
        self.direction = direction
        self.status = status or direction == 'out' and 'read' or 'unread'
        assert self.status in ['read', 'unread'], status

    def get_text(self):
        return tichy.Text("%s" % str(self.peer))

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
        return {'peer': str(self.peer),
                'text': str(self.text),
                'timestamp': str(self.timestamp),
                'direction': self.direction,
                'status': self.status}


class MessagesService(tichy.Service):
    """The service that stores all the messages

    This service provides access to the messages inbox and outbox
    """

    service = 'Messages'

    def __init__(self):
        self.outbox = tichy.List()
        self.inbox = tichy.List()
        # Prepare the future notification
        self.notification = None

    @tichy.tasklet.tasklet
    def init(self):
        yield self._load_all()
        self.outbox.connect('modified', self._on_lists_modified)
        self.inbox.connect('modified', self._on_lists_modified)

    def _on_lists_modified(self, box):
        print "TEST"
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

    def on_message_read(self, msg):
        self._update()

    def _update(self):
        """Update the notification according to the number of unread messages
        in the inbox.
        """
        nb_unread = len([m for m in self.inbox if m.status == 'unread'])
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
        data = tichy.Persistance('messages').load()
        if not data:
            yield None
        # TODO: check for data coherence
        all_messages = []
        for kargs in data:
            message = Message(**kargs)
            all_messages.append(message)
        logger.info("got %d messages", len(all_messages))
        for m in all_messages:
            # XXX: we need to rethink all this stuff...
            if m.direction == 'in':
                self.add_to_inbox(m)
            elif m.direction == 'out':
                self.add_to_outbox(m)

    @tichy.tasklet.tasklet
    def _save_all(self):
        logger.info("save all messages")
        data = [x.to_dict() for x in self.inbox + self.outbox]
        tichy.Persistance('messages').save(data)
        yield None
