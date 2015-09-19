"""
statsdmetrics.client
--------------------
Statsd client to send metrics to server
"""

import socket
from .metrics import Counter

DEFAULT_PORT = 8125


class Client(object):
    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        self._port = None
        self._host = None
        self._remote_addr = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.prefix = prefix

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        port = int(port)
        assert 0 < port < 65536
        self._port = port
        self._remote_addr = None

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        self._remote_addr = None

    @property
    def remote_addr(self):
        if self._remote_addr is None:
            self._remote_addr = (socket.gethostbyname(self.host), self.port)
        return self._remote_addr

    def increment(self, name, count=1, rate=1):
        self._send(Counter(name, count, rate).to_request())

    def _send(self, data):
        self.socket.sendto(str(data).encode(), self.remote_addr)

    def __del__(self):
        if self.socket:
            self.socket.close()