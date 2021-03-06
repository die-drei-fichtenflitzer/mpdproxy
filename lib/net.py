"""
Network stuff
"""

import socket
import threading
import logging
import selectors
import traceback
from lib.util import Source

# logging.basicConfig(filename='net.log', level=logging.DEBUG) # temporary DEBUG default
logging.basicConfig(level=logging.DEBUG)
logging.info('Tut.')
logging.warning('Winter is coming!')
logging.error('Oh boy!')
logging.critical('It was the Night King - and he had a dragon!')


_host_address = "192.168.0.2"
#_host_address = "localhost"
_host_port = 6600
_listening_port = 6601


class Proxy:
    def __init__(self):
        self.connections = []
        self.selector = selectors.DefaultSelector()
        # todo launch mpd monitoring connection

    def recv_messages(self, msg_list):
        """
        Receives multiple messages in a bunch.
        :param msg_list:
        :return:
        """
        if not msg_list:
            return
        conn = msg_list[0].connection
        source = msg_list[0].source
        if source == Source.mpd:
            conn.send_bunch(msg_list, Source.client)
        elif source == Source.client:
            conn.send_bunch(msg_list, Source.mpd)

    def recv_message(self, msg):
        """
        Is called when a message from mpd or a client is received.
        Updates mpd state and calls plugins.
        :param msg: net.Message object
        :return: None
        """
        if msg.source == Source.mpd:
            msg.connection.send(msg, Source.client)
        elif msg.source == Source.client:
            msg.connection.send(msg, Source.mpd)
        else:
            assert False

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
    def __init__(self, proxy, client_sock, client_addr, mpd_addr, mpd_port):
        """
        :param proxy: Proxy object
        :param client_sock: Client that initiated the connection; can be None for monitoring socket
        :param mpd_addr: MPD host address
        :param mpd_port: MPD port
        """
        self.proxy = proxy
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.client_msg_buf = []
        self.mpd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mpd_sock.connect((mpd_addr, mpd_port))
        self.mpd_sock.setblocking(False)
        self.mpd_msg_buf = []

    def disconnect(self):
        """
        Disconnects the client and mpd and cleans up.
        :return:
        """
        logging.info("Disconnecting " + self.client_addr[0])
        self.proxy.selector.unregister(self.client_sock)
        self.proxy.selector.unregister(self.mpd_sock)
        self.client_sock.close()
        self.mpd_sock.close()

    def recv(self, sock):
        """
        :param sock: socket the message came from; must be self.mpd_sock or self.client_sock
        :return:
        """

        # Stores the received message until it is concluded with \n
        msg_buf = self.mpd_msg_buf
        source = Source.mpd
        if sock is self.client_sock:
            source = Source.client
            msg_buf = self.client_msg_buf
        elif sock is not self.mpd_sock:
            assert False

        # Stores the received bytes until recv() fails
        recv_buf = []

        bufsize = 1024
        while True:
            try:
                chunk = sock.recv(bufsize)
            except BlockingIOError:
                break
            except (ConnectionResetError, OSError):
                self.disconnect()
                return

            if len(chunk) == 0:
                if source == Source.mpd:
                    logging.info("MPD disconnected.")
                else:
                    logging.info("Client disconnected.")
                self.disconnect()
                return

            recv_buf.append(chunk)

        chunk = b"".join(recv_buf)

        # Split up received messages by \n and process already received lines
        split = chunk.split(b"\n")
        messages = []
        for i in range(len(split)):

            # Last message; message was incomplete
            if i == len(split) - 1 and split[i] != b"":
                msg_buf.append(split[i])

            # Previous message was incomplete; this message completes it
            elif i == 0 and len(msg_buf) != 0:
                assert len(split) > 1
                msg = b""
                for el in msg_buf:
                    msg += el
                msg += split[i]
                messages.append(msg)

                if source is Source.mpd:
                    self.mpd_msg_buf = []
                else:
                    self.client_msg_buf = []

            # Empty message or last message was complete
            elif split[i] == b"":
                pass

            # Complete message
            else:
                messages.append(split[i])

        msg_deserialized = []
        for msg in messages:
            msg = msg.decode("utf-8")
            if source == Source.mpd:
                logging.debug("<-    mpd: " + msg)
            else:
                logging.debug("<- client: " + msg)

            msg = Message.deserialize(self, source, msg)
            msg_deserialized.append(msg)
        self.proxy.recv_messages(msg_deserialized)

    def send(self, msg, target):
        """
        :param msg: Message object
        :param target: util.Source object
        :return:
        """
        sock = self.mpd_sock
        t = "   mpd"
        if target is Source.client:
            sock = self.client_sock
            t = "client"
        elif target is not Source.mpd:
            assert False

        msg = msg.serialize()
        sock.sendall(msg.encode("utf-8"))
        logging.debug("-> " + t + ": " + msg)

    def send_bunch(self, msg_list, target):
        """
        Sends a list of messages in one message.
        :param msg_list: List of message objects
        :param target: util.Source object
        :return:
        """
        sock = self.mpd_sock
        t = "   mpd"
        if target is Source.client:
            sock = self.client_sock
            t = "client"
        elif target is not Source.mpd:
            assert False

        for i in range(len(msg_list)):
            msg_list[i] = msg_list[i].serialize()
        msg = "".join(msg_list)
        sock.sendall(msg.encode("utf-8"))
        logging.debug("-> " + t + ": " + msg)

    def send_mpd(self, msg):
        """
        :param msg: Message object that is to be sent to MPD
        :return:
        """
        msg = msg.serialize().decode("utf-8")
        self.mpd_sock.sendall(msg)
        logging.debug("->    mpd: " + msg)

    def send_client(self, msg):
        """
        :param msg: Message object that is to be sent to the client
        :return:
        """
        msg = msg.serialize().decode("utf-8")
        self.client_sock.sendall(msg.serialize())


class Message:
    def __init__(self, connection=None, source=None):
        """
        :param connection: Connection object that this message occured in; can be None if this is an original message
        :param source: util.Source object; can be None if this is an original message
        """
        self.connection = connection
        self.source = source
        self.message = None
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
        msg = cls(connection, source)
        msg.message = bytestream
        return msg

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
        return self.message + "\n"


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
        logging.error("Listener not running: Binding to port " + str(_listening_port) + " failed")
        return

    s.listen(5)
    while True:
        conn, addr = s.accept()
        logging.info("incoming connection from " + str(addr[0]))
        conn.setblocking(False)
        conn = Connection(proxy, conn, addr, _host_address, _host_port)  # TODO decide how this is registered in main thingy
        proxy.register_connection(conn)


def init():
    """
    Does the I/O thread setup.
    :return: Proxy object
    """
    proxy = Proxy()
    threading.Thread(target=listener, args=(proxy,), name='thread-listener').start()
    threading.Thread(target=connhandler, args=(proxy,)).start()
    # Should we maybe start the proxy via a main non-daemon thread but run the vital functions via a daemon-thread? 
    # To spare resources and not have a python script running 24/7. Not sure that makes sense though, tired and my eyes hurt. Gn8
    # mpdprox_main = threading.Thread(target=listener, name='thread-listener')
    # mpdprox_daemon = threading.Thread(target=vitalfunc_daemon, name=vitalfunc_daemon, daemon=True)
    # mpdprox_main.start()
    # mpdprox_daemon.start()

    return proxy
