import lib.mpd

class Plugin:
    def __init__(self, mpd):
        self.mpd  = mpd
        self.playback_listener = mpd.register_listener(lib.mpd.Events.PLAYBACK)

    def unload(self):
        pass

    def on_playback_event(self, event):
        pass