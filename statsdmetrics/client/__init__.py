"""
statsdmetrics.client
--------------------
Statsd client to send metrics to server
"""

import socket
from abc import ABCMeta
from random import random
from collections import deque
from time import time

from datetime import datetime

try:
    from typing import Tuple, Union
except ImportError:
    Tuple, Union = None, None

from .timing import Chronometer, Stopwatch
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
        # type: (socket.socket) -> None
        self._closed = False  # type: bool
        self._socket = sock  # type: socket.socket
        self._clients = deque()  # type: deque

    @property
    def closed(self):
        # type: () -> bool
        return self._closed

    def close(self):
        # type: () -> None
        """Close the socket to free system resources.

        After the socket is closed, further operations with socket
        will fail. Multiple calls to close will have no effect.
        """

        if self._closed:
            return
        self._socket.close()
        self._closed = True

    def add_client(self, client):
        # type: (object) -> None
        """Add a client as a user of the socket.

        As long as the socket has users, it keeps the underlying
        socket object open for operations.
        """

        self._clients.append(id(client))

    def remove_client(self, client):
        # type: (object) -> None
        """Remove the client from the users of the socket.

        If there are no more clients for the socket, it
        will close automatically.
        """

        try:
            self._clients.remove(id(client))
        except ValueError:
            pass

        if len(self._clients) < 1:
            self.close()

    def __del__(self):
        self.close()

    def __getattr__(self, name):
        return getattr(self._socket, name)


class AbstractClient(object):
    __metaclass__ = ABCMeta

    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        # type: (str, int, str) -> None
        self._port = None  # type: int
        self._host = host  # type: str
        self._remote_address = None  # type: Tuple[str, int]
        self._socket = None  # type: AutoClosingSharedSocket
        self.prefix = prefix  # type: str
        self._set_port(port)
        self._socket = self._create_socket()

    @property
    def port(self):
        # type: () -> int
        return self._port

    def _set_port(self, port):
        # type: (int) -> None
        port = int(port)
        assert 0 < port < 65536
        self._port = port

    @property
    def host(self):
        # type: () -> str
        return self._host

    @property
    def remote_address(self):
        # type: () -> Tuple[str, int]
        if self._remote_address is None:
            self._remote_address = (socket.gethostbyname(self.host), self.port)
        return self._remote_address

    def increment(self, name, count=1, rate=1):
        # type: (str, int, float) -> None
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
        # type: (str, int, float) -> None
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
        # type: (str, float, float) -> None
        """Send a Timer metric with the specified duration in milliseconds"""

        if self._should_send_metric(name, rate):
            milliseconds = int(milliseconds)
            self._request(
                Timer(
                    self._create_metric_name_for_request(name),
                    milliseconds,
                    rate
                ).to_request()
            )

    def timing_since(self, name, start_time, rate=1):
        # type: (str, Union[float, datetime], float) -> None
        """Send a Timer metric calculating the duration from the start time"""
        duration = 0  # type: float
        if isinstance(start_time, datetime):
            duration = (datetime.now(start_time.tzinfo) - start_time).total_seconds() * 1000
        elif is_numeric(start_time):
            assert start_time > 0
            duration = (time() - start_time) * 1000
        else:
            raise ValueError("start time should be a timestamp or a datetime")
        self.timing(name, duration, rate)

    def gauge(self, name, value, rate=1):
        # type: (str, float, float) -> None
        """Send a Gauge metric with the specified value"""

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
        # type: (str, float, float) -> None
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
        # type: (str, str, float) -> None
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

    def chronometer(self):
        # type: () -> Chronometer
        return Chronometer(self)

    def stopwatch(self, name, rate=1, reference=None):
        # type: (str, float, float) -> Stopwatch
        return Stopwatch(self, name, rate, reference)

    def _create_metric_name_for_request(self, name):
        # type: (str) -> str
        return self.prefix + normalize_metric_name(name)

    def _should_send_metric(self, name, rate):
        # type: (str, float) -> bool
        return rate >= 1 or random() <= rate

    def _create_socket(self):
        # type: () -> AutoClosingSharedSocket
        sock = AutoClosingSharedSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        sock.add_client(self)
        return sock

    def _request(self, data):
        # type: (str) -> None
        self._socket.sendto(str(data).encode(), self.remote_address)

    def _configure_client(self, other):
        # type: (AbstractClient) -> None
        other._remote_address = self._remote_address
        other._socket = self._socket
        self._socket.add_client(other)

    def __del__(self):
        if self._socket:
            self._socket.remove_client(self)
            self._socket = None


class BatchClientMixIn(object):
    """MixIn class to clients that buffer metrics and send batch requests"""

    def __init__(self, batch_size=512):
        # type: (int) -> None
        batch_size = int(batch_size)
        assert batch_size > 0, "BatchClient batch size should be positive"
        self._batch_size = batch_size  # type: int
        self._batches = deque()  # type: deque

    @property
    def batch_size(self):
        # type: () -> int
        return self._batch_size

    def clear(self):
        # type: () -> BatchClientMixIn
        """Clear buffered metrics"""

        self._batches.clear()
        return self

    def flush(self):
        # type: () -> BatchClientMixIn
        """Send buffered metrics in batch requests"""
        raise NotImplementedError("flush should be implemented in the client class")

    def _request(self, data):
        # type: (str) -> None
        """Override parent by buffering the metric instead of sending now"""

        data = bytearray("{}\n".format(data).encode())
        self._prepare_batches_for_storage(len(data))
        self._batches[-1].extend(data)

    def _prepare_batches_for_storage(self, data_size=None):
        # type: (int) -> None
        batch_size = self._batch_size
        data_size = data_size or batch_size
        if data_size > batch_size:
            self._batches.append(bytearray())
        elif len(self._batches) < 1 or \
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
        # type: (int) -> BatchClient
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
        # type: (str, int, str, int) -> None
        AbstractClient.__init__(self, host, port, prefix)
        BatchClientMixIn.__init__(self, batch_size)

    def unit_client(self):
        # type: () -> Client
        """Return a client with same settings of the batch client"""

        client = Client(self.host, self.port, self.prefix)
        self._configure_client(client)
        return client

    def flush(self):
        # type: () -> BatchClient
        """Send buffered metrics in batch requests"""

        address = self.remote_address
        while len(self._batches) > 0:
            self._socket.sendto(self._batches[0], address)
            self._batches.popleft()
        return self


__all__ = ['Client', 'BatchClient']
