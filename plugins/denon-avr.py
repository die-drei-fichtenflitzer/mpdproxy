import lib.mpd

# config
STANDBYTIME = 20*60
###


class Plugin(lib.mpd.Listener):
    def __init__(self, mpd):
        self.mpd = mpd
        self.playback_listener = mpd.register_listener(lib.mpd.Events.PLAYBACK)

    def unload(self):
        pass

    def load(self):
        pass

    def on_playback_event(self, event):
        pass