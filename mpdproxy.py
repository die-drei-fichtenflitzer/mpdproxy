#!/usr/bin/env python3

import sys
import lib.net as net
from lib.util import Source

class Proxy:
    def __init__(self):
        pass

    def recv_message(self, msg):
        """
        Is called when a message from mpd or a client is received.
        Updates mpd state and calls plugins.
        :param msg: net.Message object
        :return: None
        """
        pass


def main(args):
    net.init(Proxy())

if __name__ == "__main__":
    main(sys.argv)
