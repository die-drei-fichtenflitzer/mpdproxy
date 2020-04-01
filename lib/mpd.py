from abc import ABC

from lib.statemachine import StateMachine
from lib.util import Source
from enum import Enum


class Event:
    """
    Occurs when a client issues a control command (e.g. playback control).
    """
    def __init__(self, source):
        """
        :param source: lib.util.Source object that indicates who made the event happen
        """
        self.source = source
        self._has_run = False

    def cancel(self):
        """
        Cancels the event; control command does not reach mpd.
        """
        raise NotImplementedError

    def run(self):
        if self._has_run:
            raise RuntimeError("Event has already run: " + str(self))

        self._has_run = True
        # TODO


class Events(Enum):
    PLAYBACK = 0  # start, stop, pause, seek
    OPTIONS = 1  # random, repeat etc
    QUEUE = 2  # add, remove
    VOLUME = 3  # volume change
    DATABASE = 4  # update started or db changed after update
    OUTPUT = 5  # audio output change


class ControlListener(ABC):
    """
    Listens to control events, i.e. control commands issued by clients.
    """
    def __init__(self, event, prio):
        self.event = event
        self.mode = prio

    def listen(self, event):
        raise NotImplementedError


class EventPriority(Enum):
    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    INFO = 4


class PlaybackStates(Enum):
    PLAY = 0
    PAUSE = 1
    STOP = 2
    UNDEFINED = 3


class MPD:
    def __init__(self):
        self.listeners = []
        self.playback_state = PlaybackStates.UNDEFINED

    def register_listener(self, listener, event, prio):
        self.listeners.append(listener)

    def unregister_listener(self, listener):
        pass
