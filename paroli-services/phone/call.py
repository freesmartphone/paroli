#
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

import logging
LOGGER = logging.getLogger('Call')

import tichy
from tel_number import TelNumber

class Call(tichy.Item):
    """Class that represents a voice call"""

    def __init__(self, number, direction='out', timestamp=None,
                 status='inactive'):
        """Create a new call object

        :Parameters:

            number : `tichy.TelNumber` | str
                The number of the peer

            direction : str
               'out' for outgoing call, 'in' for incoming call

            timestamp
                the time at which we created the call. If set to None
                we use the current time

            status : str | None
                Can be any of :
                    - 'inactive'
                    - 'outoing'
                    - 'activaing'
                    - 'active'
                    - 'releasing'
                    - 'released'
                (default to 'inactive')

        Signals

            initiating
                The call is being initiated

            outgoing
                The call is outgoing

            activated
                The call has been activated

            releasing
                The call is being released

            released
                The call has been released
        """
        self.number = TelNumber.as_type(number)
        self.direction = direction
        self.timestamp = tichy.Time.as_time(timestamp)
        self.status = status

    def get_text(self):
        return self.number.get_text()

    @tichy.tasklet.tasklet
    def initiate(self):
        """Initiate the call

        This will try to get the 'GSM' service and call its 'initiate'
        method.
        """
        LOGGER.info("initiate call")
        gsm_service = tichy.Service('GSM')
        yield gsm_service._initiate(self)
        self.status = 'initiating'
        self.emit(self.status)

    @tichy.tasklet.tasklet
    def release(self):
        LOGGER.info("release call")
        if self.status in ['releasing', 'released']:
            return
        gsm_service = tichy.Service('GSM')
        yield gsm_service._release(self)
        self.status = 'releasing'
        self.emit(self.status)

    @tichy.tasklet.tasklet
    def activate(self):
        """Activate the call"""
        LOGGER.info("activate call")
        gsm_service = tichy.Service('GSM')
        yield gsm_service._activate(self)
        self.status = 'activating'
        self.emit(self.status)

    def outgoing(self):
        self.status = 'outgoing'
        self.emit('outgoing')

    def active(self):
        self.status = 'active'
        self.emit('activated')

    def released(self):
        self.status = 'released'
        self.emit('released')


    # TODO: In the long run we should really use a system similar to
    #       PEAK, where we can define all the Items attributes and
    #       every atomic value has a save and load method.  So that we
    #       don't have to create all those `to_dict` and `from_dict`
    #       methods. We could use a Struct Item for this kind of
    #       things.

    def to_dict(self):
        """return all the attributes in a python dict"""
        return {'number': str(self.number),
                'status': str(self.status),
                'direction': self.direction,
                'timestamp': str(self.timestamp)}

    @classmethod
    def from_dict(self, kargs):
        """return a new Call object from a dictionary

        This should be compatible with the `to_dict` method
        """
        number = kargs['number']
        status = kargs['status']
        direction = kargs['direction']
        timestamp = kargs['timestamp']
        return Call(number, direction=direction, timestamp=timestamp,
                    status=status)
