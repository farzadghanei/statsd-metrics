"""
statsdmetrics.client
--------------------
Statsd client to send metrics to server
"""

import socket
from random import random

from .metrics import (Counter, Timer, Gauge, GaugeDelta, Set,
                      normalize_metric_name, is_numeric)


DEFAULT_PORT = 8125


class Client(object):
    """Statsd client

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
        self._remote_address = None
        self._socket = None
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
        self._remote_address = None

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        self._remote_address = None

    @property
    def remote_address(self):
        if self._remote_address is None:
            self._remote_address = (socket.gethostbyname(self.host), self.port)
        return self._remote_address

    def increment(self, name, count=1, rate=1):
        if self._should_send_metric(name, rate):
            self._request(
                Counter(
                    self._create_metric_name_for_request(name),
                    int(count),
                    rate
                ).to_request()
            )

    def decrement(self, name, count=1, rate=1):
        if self._should_send_metric(name, rate):
            self._request(
                Counter(
                    self._create_metric_name_for_request(name),
                    -1 * int(count),
                    rate
                ).to_request()
            )

    def timing(self, name, milliseconds, rate=1):
        if self._should_send_metric(name, rate):
            if not is_numeric(milliseconds):
                milliseconds = float(milliseconds)
            self._request(
                Timer(
                    self._create_metric_name_for_request(name),
                    milliseconds,
                    rate
                ).to_request()
            )

    def gauge(self, name, value, rate=1):
        if self._should_send_metric(name, rate):
            if not is_numeric(value):
                value = float(value)
            self._request(
                Gauge(
                    self._create_metric_name_for_request(name),
                    value,
                    rate
                ).to_request()
            )

    def gauge_delta(self, name, delta, rate=1):
        if self._should_send_metric(name, rate):
            if not is_numeric(delta):
                delta = float(delta)
            self._request(
                GaugeDelta(
                    self._create_metric_name_for_request(name),
                    delta,
                    rate
                ).to_request()
            )

    def set(self, name, value, rate=1):
        if self._should_send_metric(name, rate):
            value = str(value)
            self._request(
                Set(
                    self._create_metric_name_for_request(name),
                    value,
                    rate
                ).to_request()
            )

    def batch_client(self, size=512):
        batch_client = BatchClient(self.host, self.port, self.prefix, size)
        batch_client._remote_address = self._remote_address
        return batch_client

    def _create_metric_name_for_request(self, name):
        return self.prefix + normalize_metric_name(name)

    def _should_send_metric(self, name, rate):
        return rate >= 1 or random() <= rate

    def _get_open_socket(self):
        if self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self._socket

    def _request(self, data):
        self._get_open_socket().sendto(str(data).encode(), self.remote_address)

    def __del__(self):
        if self._socket is not None:
            self._socket.close()


class BatchClient(Client):
    """Statsd client buffering requests and send in batch requests

    >>> client = BatchClient("stats.example.org")
    >>> client.increment("event")
    >>> client.decrement("event.second", 3, 0.5)
    >>> client.flush()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix="", batch_size=512):
        super(BatchClient, self).__init__(host, port, prefix)
        batch_size = int(batch_size)
        assert batch_size > 0, "BatchClient batch size should be positive"
        self._batch_size = batch_size
        self._batches = []

    @property
    def batch_size(self):
        return self._batch_size

    def _request(self, data):
        """Override parent by buffering the metric instead of sending now"""
        data = bytearray("{}\n".format(data).encode())
        self._prepare_batches_for_storage(len(data))
        self._batches[-1].extend(data)

    def _prepare_batches_for_storage(self, data_size=None):
        batch_size = self._batch_size
        data_size = data_size or batch_size
        if data_size > batch_size:
            self._batches.append(bytearray())
        elif not self._batches or\
                        (len(self._batches[-1]) + data_size) >= batch_size:
            self._batches.append(bytearray())

    def clear(self):
        self._batches = []

    def flush(self):
        """Send buffered metrics in batch requests"""
        address = self.remote_address
        socket_ = self._get_open_socket()
        while len(self._batches) > 0:
            socket_.sendto(self._batches[0], address)
            self._batches.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.flush()


__all__ = (Client, BatchClient)
