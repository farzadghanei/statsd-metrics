"""
statsdmetrics.client.tcp
------------------------
Statsd clients to send metrics to server over TCP
"""

import socket

from . import (AutoClosingSharedSocket, AbstractClient,
        BatchClientMixIn, DEFAULT_PORT)


class TCPClientMixIn(object):
    """Mix-In class to send metrics over TCP"""

    def _get_open_socket(self):
        if self._socket is None:
            self._socket = AutoClosingSharedSocket(
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                )
            self._socket.add_client(self)
            self._socket.connect(self.remote_address)
        return self._socket

    def _request(self, data):
        self._get_open_socket().sendall("{}\n".format(data).encode())


class TCPClient(TCPClientMixIn, AbstractClient):
    """Statsd client using TCP to send metrics

    >>> client = TCPClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    """

    def batch_client(self, size=512):
        """Return a TCP batch client with same settings of the TCP client"""

        batch_client = TCPBatchClient(self.host, self.port, self.prefix, size)
        self._configure_client(batch_client)
        return batch_client


class TCPBatchClient(BatchClientMixIn, TCPClientMixIn, AbstractClient):
    """Statsd client that buffers metrics and sends batch requests over TCP

    >>> client = TCPBatchClient("stats.example.org")
    >>> client.increment("event")
    >>> client.decrement("event.second", 3, 0.5)
    >>> client.flush()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix="", batch_size=512):
        AbstractClient.__init__(self, host, port, prefix)
        BatchClientMixIn.__init__(self, batch_size)

    def flush(self):
        """Send buffered metrics in batch requests over TCP"""

        sock = self._get_open_socket()
        while len(self._batches) > 0:
            sock.sendall(self._batches[0])
            self._batches.pop(0)
        return self


__all__ = (TCPClient, TCPBatchClient)