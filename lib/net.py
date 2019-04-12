"""
Network stuff
"""

import socket
import threading
import logging
import selectors
from lib.util import Source

logging.basicConfig(filename='net.log',level=logging.DEBUG) # temporary DEBUG default
logging.info('Tut.')
logging.warning('Winter is coming!')
logging.error('Oh boy!')
logging.critical('It is the Night King - and he has a dragon!')


_host_address = "localhost"
_host_port = 6600
_listening_port = 6601


class Proxy:
    def __init__(self):
        self.connections = []
        self.selector = selectors.DefaultSelector()
        # todo launch mpd monitoring connection

    def recv_message(self, msg):
        """
        Is called when a message from mpd or a client is received.
        Updates mpd state and calls plugins.
        :param msg: net.Message object
        :return: None
        """
        raise NotImplementedError()

    def register_connection(self, conn):
        self.selector.register(conn.mpd_sock, selectors.EVENT_READ, (conn, conn.mpd_sock))
        if conn.client_sock is not None:
            self.selector.register(conn.client_sock, selectors.EVENT_READ, (conn, conn.client_sock))
        self.connections.append(conn)


class Connection:
    """
    We have one of these per client. This contains the client socket and the client-specific mpd socket.
    TODO handle disconnections
    """
    def __init__(self, proxy, client_sock, mpd_addr, mpd_port):
        """
        :param proxy: Proxy object
        :param client_sock: Client that initiated the connection; can be None for monitoring socket
        :param mpd_addr: MPD host address
        :param mpd_port: MPD port
        """
        self.proxy = proxy
        self.client_sock = client_sock
        self.mpd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mpd_sock.connect((mpd_addr, mpd_port))

    def disconnect(self):
        """
        Disconnects the client and mpd and cleans up.
        :return:
        """
        raise NotImplementedError()

    def recv(self, sock):
        """
        :param sock: socket the message came from; must be self.mpd_sock or self.client_sock
        :return:
        """
        source = Source.mpd
        if sock is self.mpd_sock:
            pass
        elif sock is self.client_sock:
            source = Source.client
        else:
            assert False

        bufsize = 1024  # make this less static
        try:
            chunk = sock.recv(bufsize)
        except (ConnectionResetError, OSError):
            self.disconnect()
            return

        if len(chunk) == 0:
            self.disconnect()
            return

        # todo continue
        msg = Message.deserialize(self, source, chunk)
        self.proxy.recv_message(msg)


    def send_mpd(self, msg):
        """
        :param msg: Message object that is to be sent to MPD
        :return:
        """
        raise NotImplementedError()

    def send_client(self, msg):
        """
        :param msg: Message object that is to be sent to the client
        :return:
        """
        raise NotImplementedError()


class Message:
    def __init__(self, connection=None, source=None):
        """
        :param connection: Connection object that this message occured in; can be None if this is an original message
        :param source: util.Source object; can be None if this is an original message
        """
        self.connection = connection
        self.source = source
        assert (connection is source is None) or (connection is not None and source is not None)

    @classmethod
    def deserialize(cls, connection, source, bytestream):
        """
        Factory method to deserialize an incoming message; parses a received bytestream
        :param connection: Connection object
        :param source: util.Source object
        :param bytestream: received bytes
        :return: Message object
        """
        raise NotImplementedError()

    @classmethod
    def original_message(cls):
        """
        Factory to build a completely new message.
        :return: Message object
        """
        raise NotImplementedError()

    def serialize(self):
        """
        :return: Serialized message that can be sent
        """
        raise NotImplementedError()


def connhandler(proxy):
    """
    Reads messages and calls proxy
    :param proxy: mpdproxy.Proxy object
    :return:
    """
    while True:
        events = proxy.selector.select()
        for key, bitmask in events:
            conn = key.data[0]
            sock = key.data[1]

            # Something to read
            if bitmask & selectors.EVENT_READ:
                conn.recv(sock)

            # Something to write
            if bitmask & selectors.EVENT_WRITE:
                pass


def listener(proxy):
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
        conn = Connection(conn, _host_address, _host_port)  # TODO decide how this is registered in main thingy
        proxy.register_connection(conn)


def init():
    """
    Does the I/O thread setup.
    :return: Proxy object
    """
    proxy = Proxy()
    threading.Thread(target=listener, args=(proxy,), name='thread-listener').start()
    # Should we maybe start the proxy via a main non-daemon thread but run the vital functions via a daemon-thread? 
    # To spare resources and not have a python script running 24/7. Not sure that makes sense though, tired and my eyes hurt. Gn8
    # mpdprox_main = threading.Thread(target=listener, name='thread-listener')
    # mpdprox_daemon = threading.Thread(target=vitalfunc_daemon, name=vitalfunc_daemon, daemon=True)
    # mpdprox_main.start()
    # mpdprox_daemon.start()

    return proxy
