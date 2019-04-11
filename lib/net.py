"""
Network stuff
"""

import socket
import threading


_host_address = "localhost"
_host_port = 6600
_listening_port = 6601


class Client:
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
        :param s: Message that is to be sent to MPD
        :return:
        """
        pass

    def send_client(self, s):
        """
        :param s: Message that is to be sent to the client
        :return:
        """
        pass


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
        Client(conn, _host_address, _host_port)  # TODO decide how this is registered in main thingy


def init():
    threading.Thread(target=listener).start()
