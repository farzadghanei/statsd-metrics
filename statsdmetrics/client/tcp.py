"""
statsdmetrics.client.tcp
------------------------
Statsd clients to send metrics to server over TCP
"""

import socket

from . import (AutoClosingSharedSocket, AbstractClient,
        BatchClientMixIn, DEFAULT_PORT)


def _create_auto_closing_shared_tcp_socket(client):
    # type: (AbstractClient) -> AutoClosingSharedSocket
    sock = AutoClosingSharedSocket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    sock.add_client(client)
    sock.connect(client.remote_address)
    return sock


class TCPClient(AbstractClient):
    """Statsd client using TCP to send metrics

    >>> client = TCPClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    """

    def batch_client(self, size=512):
        # type: (int) -> TCPBatchClient
        """Return a TCP batch client with same settings of the TCP client"""

        batch_client = TCPBatchClient(self.host, self.port, self.prefix, size)
        self._configure_client(batch_client)
        return batch_client

    def _create_socket(self):
        # type: () -> AutoClosingSharedSocket
        return _create_auto_closing_shared_tcp_socket(self)

    def _request(self, data):
        # type: (str) -> None
        self._socket.sendall("{}\n".format(data).encode())


class TCPBatchClient(BatchClientMixIn, AbstractClient):
    """Statsd client that buffers metrics and sends batch requests over TCP

    >>> client = TCPBatchClient("stats.example.org")
    >>> client.increment("event")
    >>> client.decrement("event.second", 3, 0.5)
    >>> client.flush()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix="", batch_size=512):
        # type: (str, int, str, int) -> None
        AbstractClient.__init__(self, host, port, prefix)
        BatchClientMixIn.__init__(self, batch_size)

    def flush(self):
        """Send buffered metrics in batch requests over TCP"""
        # type: () -> TCPBatchClient
        while len(self._batches) > 0:
            self._socket.sendall(self._batches[0])
            self._batches.popleft()
        return self

    def unit_client(self):
        # type: () -> TCPClient
        """Return a TCPClient with same settings of the batch TCP client"""

        client = TCPClient(self.host, self.port, self.prefix)
        self._configure_client(client)
        return client

    def _create_socket(self):
        # type: () -> AutoClosingSharedSocket
        return _create_auto_closing_shared_tcp_socket(self)


__all__ = ['TCPClient', 'TCPBatchClient']
