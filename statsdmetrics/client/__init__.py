"""
statsdmetrics.client
--------------------
Statsd client to send metrics to server
"""

import socket
from abc import ABCMeta
from random import random

from ..metrics import (Counter, Timer, Gauge, GaugeDelta, Set,
                      normalize_metric_name, is_numeric)


DEFAULT_PORT = 8125


class AutoClosingSharedSocket(object):
    """Decorate sockets to attach metadata required by clients,
    and release system resources asap.

    The socket object is shared between multiple clients to use
    and will automatically close the socket when there are
    no more clients for the socket.
    """

    def __init__(self, sock):
        self._closed = False
        self._socket = sock
        self._clients = []

    @property
    def closed(self):
        return self._closed

    def close(self):
        """Close the socket to free system resources.

        After the socket is closed, further operations with socket
        will fail. Multiple calls to close will have no effect.
        """

        if self._closed:
            return
        self._socket.close()
        self._closed = True

    def add_client(self, client):
        """Add a client as a user of the socket.

        As long as the socket has users, it keeps the underlying
        socket object open for operations.
        """

        self._clients.append(id(client))

    def remove_client(self, client):
        """Remove the client from the users of the socket.

        If there are no more clients for the socket, it
        will close automatically.
        """

        try:
            self._clients.remove(id(client))
        except ValueError:
            pass

        if not self._clients:
            self.close()

    def __del__(self):
        self.close()

    def __getattr__(self, name):
        return getattr(self._socket, name)


class AbstractClient(object):
    __metaclass__ = ABCMeta

    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        self._port = None
        self._host = None
        self._remote_address = None
        self._socket = None
        self._host = host
        self._set_port(port)
        self.prefix = prefix

    @property
    def port(self):
        return self._port

    def _set_port(self, port):
        port = int(port)
        assert 0 < port < 65536
        self._port = port

    @property
    def host(self):
        return self._host

    @property
    def remote_address(self):
        if self._remote_address is None:
            self._remote_address = (socket.gethostbyname(self.host), self.port)
        return self._remote_address

    def increment(self, name, count=1, rate=1):
        """Increment a Counter metric"""

        if self._should_send_metric(name, rate):
            self._request(
                Counter(
                    self._create_metric_name_for_request(name),
                    int(count),
                    rate
                ).to_request()
            )

    def decrement(self, name, count=1, rate=1):
        """Decrement a Counter metric"""

        if self._should_send_metric(name, rate):
            self._request(
                Counter(
                    self._create_metric_name_for_request(name),
                    -1 * int(count),
                    rate
                ).to_request()
            )

    def timing(self, name, milliseconds, rate=1):
        """Send a Timer metric with the specified duration in milliseconds"""

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
        """Send a Gauge metric with the specified vlaue"""

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
        """Send a GaugeDelta metric to change a Gauge by the specified value"""

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
        """Send a Set metric with the specified unique value"""

        if self._should_send_metric(name, rate):
            value = str(value)
            self._request(
                Set(
                    self._create_metric_name_for_request(name),
                    value,
                    rate
                ).to_request()
            )

    def _create_metric_name_for_request(self, name):
        return self.prefix + normalize_metric_name(name)

    def _should_send_metric(self, name, rate):
        return rate >= 1 or random() <= rate

    def _get_open_socket(self):
        if self._socket is None:
            self._socket = AutoClosingSharedSocket(
                    socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                )
            self._socket.add_client(self)
        return self._socket

    def _request(self, data):
        self._get_open_socket().sendto(str(data).encode(), self.remote_address)

    def _configure_client(self, other):
        other._remote_address = self._remote_address
        sock = self._get_open_socket()
        other._socket = sock
        sock.add_client(other)

    def __del__(self):
        if self._socket:
            self._socket.remove_client(self)
            self._socket = None


class BatchClientMixIn(object):
    """MixIn class to clients that buffer metrics and send batch requests"""

    def __init__(self, batch_size=512):
        batch_size = int(batch_size)
        assert batch_size > 0, "BatchClient batch size should be positive"
        self._batch_size = batch_size
        self._batches = []

    @property
    def batch_size(self):
        return self._batch_size

    def clear(self):
        """Clear buffered metrics"""

        self._batches = []
        return self

    def flush(self):
        """Send buffered metrics in batch requests"""

        address = self.remote_address
        sock = self._get_open_socket()
        while len(self._batches) > 0:
            sock.sendto(self._batches[0], address)
            self._batches.pop(0)
        return self

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.flush()


class Client(AbstractClient):
    """Statsd client, using UDP to send metrics

    >>> client = Client("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    """

    def batch_client(self, size=512):
        """Return a batch client with same settings of the client"""

        batch_client = BatchClient(self.host, self.port, self.prefix, size)
        self._configure_client(batch_client)
        return batch_client


class BatchClient(BatchClientMixIn, AbstractClient):
    """Statsd client buffering requests and send in batch UDP requests

    >>> client = BatchClient("stats.example.org")
    >>> client.increment("event")
    >>> client.decrement("event.second", 3, 0.5)
    >>> client.flush()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix="", batch_size=512):
        AbstractClient.__init__(self, host, port, prefix)
        BatchClientMixIn.__init__(self, batch_size)


__all__ = (Client, BatchClient)