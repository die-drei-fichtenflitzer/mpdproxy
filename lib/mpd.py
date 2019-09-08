from lib.statemachine import StateMachine
from lib.util import Source
from enum import Enum

class Event:
    def __init__(self, source):
        """
        :param source: lib.util.Source object that indicates who made the event happen
        """
        self.source = source
        self._has_run = False

    def close(self):
        pass

    def run(self):
        if self._has_run:
            raise RuntimeError("Event has already run: " + str(self))

        self._has_run = True
        # TODO

class Events(Enum):
    PLAYBACK = 0
    QUEUE = 1

class Listener:
    def __init__(self, event, callback, mode):
        self.event = event
        self.callback = callback
        self.mode = mode

    def fire(self, event):
        self.callback(event)

class ListenerModes(Enum):
    NOTIFY = 0
    BLOCK = 1

class PlaybackStates(Enum):
    PLAY = 0
    PAUSE = 1
    STOP = 2
    UNDEFINED = 3

class MPD:
    def __init__(self):
        self.listeners = []
        self.playback_state = PlaybackStates.UNDEFINED

    def register_listener(self, event, callback, mode):
        listener =  Listener(event, callback, mode)
        self.listeners.append(listener)
        return listener

    def unregister_listener(self, listener):
        pass
