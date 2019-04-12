"""
Network stuff
"""

import socket
import threading
import logging
from lib.util import Source

logging.basicConfig(filename='net.log',level=logging.DEBUG) # temporary DEBUG default
logging.info('Tut.')
logging.warning('Winter is coming!')
logging.error('Oh boy!')
logging.critical('It is the Night King - and he has a dragon!')


_host_address = "localhost"
_host_port = 6600
_listening_port = 6601


class Connection:
    """
    We have one of these per client. This contains the client socket and the client-specific mpd socket.
    """
    def __init__(self, client_sock, mpd_addr, mpd_port):
        """
        :param client_sock: Client that initiated the connection; can be None for monitoring socket
        :param mpd_addr: MPD host address
        :param mpd_port: MPD port
        """
        self.client_sock = client_sock
        self.mpd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mpd_sock.connect((mpd_addr, mpd_port))

    def send_mpd(self, s):
        """
        :param msg: Message object that is to be sent to MPD
        :return:
        """
        pass

    def send_client(self, msg):
        """
        :param msg: Message object that is to be sent to the client
        :return:
        """
        pass


class Message:
    def __init__(self, connection=None, source=None):
        """
        :param connection: Connection object that this message occured in; can be None if this is an original message
        :param source: util.Source object; can be None if this is an original message
        """
        self.connection = connection
        self.source = source
        assert (connection is source is None) or (connection is not None and source is not None)


def connhandler(proxy):
    """
    Reads messages and calls proxy
    :param proxy: mpdproxy.Proxy object
    :return:
    """


def listener():
    """
    Listener thread; builds Clients
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", _listening_port))
    except OSError:
        # binding failed
        print("Listener not running: Binding to port " + str(_listening_port) + " failed")
        return

    s.listen(5)
    while True:

        conn, addr = s.accept()
        conn.setblocking(False)
        print("incoming connection from " + str(addr[0]))
        Connection(conn, _host_address, _host_port)  # TODO decide how this is registered in main thingy


def init(proxy):
    """
    Does the I/O thread setup.
    :param proxy: mpdclient.Proxy object
    :return:
    """
    threading.Thread(target=listener, name='thread-listener').start()
    # Should we maybe start the proxy via a main non-daemon thread but run the vital functions via a daemon-thread? 
    # To spare resources and not have a python script running 24/7. Not sure that makes sense though, tired and my eyes hurt. Gn8
    # mpdprox_main = threading.Thread(target=listener, name='thread-listener')
    # mpdprox_daemon = threading.Thread(target=vitalfunc_daemon, name=vitalfunc_daemon, daemon=True)
    # mpdprox_main.start()
    # mpdprox_daemon.start()
