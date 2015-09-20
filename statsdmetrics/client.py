"""
statsdmetrics.client
--------------------
Statsd client to send metrics to server
"""

import socket
from random import random

from .metrics import (Counter, Timer, normalize_metric_name, is_numeric)


DEFAULT_PORT = 8125


class Client(object):
    """Statsd Client

    >>> client = Client("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4) # specify count and sample rate
    >>> # able to change configurations
    >>> client.port = 8126
    >>> client.prefix = "region"
    >>> client.decrement("event", rate=0.2)
    """
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
        if self._should_send_metric(name, rate):
            self._send(
                Counter(
                    self._get_metric_name(name),
                    int(count),
                    rate
                ).to_request()
            )

    def decrement(self, name, count=1, rate=1):
        if self._should_send_metric(name, rate):
            self._send(
                Counter(
                    self._get_metric_name(name),
                    -1 * int(count),
                    rate
                ).to_request()
            )

    def timing(self, name, milliseconds, rate=1):
        if self._should_send_metric(name, rate):
            if not is_numeric(milliseconds):
                milliseconds = float(milliseconds)
            self._send(
                Timer(
                    self._get_metric_name(name),
                    milliseconds,
                    rate
                ).to_request()
            )

    def _get_metric_name(self, name):
        return self.prefix + normalize_metric_name(name)

    def _should_send_metric(self, name, rate):
        return rate >= 1 or random() <= rate

    def _send(self, data):
        self.socket.sendto(str(data).encode(), self.remote_addr)

    def __del__(self):
        self.socket.close()
