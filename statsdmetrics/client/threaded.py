"""
statsdmetrics.client.threaded
-----------------------------
Statsd clients to send metrics to server in a separate thread
"""

from threading import Thread, Event

try:
    import Queue as queue
except ImportError:
    import queue

from . import DEFAULT_PORT
from .tcp import TCPClient, TCPBatchClient


class ThreadedTCPClientError(Exception):
    pass


class ThreadedTCPClientMixIn(object):

    def __init__(self):
        self._stop_sending_metrics_sentinel = "__STOP__"
        self._request_queue = queue.Queue()
        self._closed = Event()
        self._sending_thread = Thread(target=self._send_queued_requests)
        self._sending_thread.daemon = False
        self._sending_thread.start()

    def _request(self, data):
        if self._closed.isSet():
            raise ThreadedTCPClientError(
                    "ThreadedTCPClient is closed and can not send requests anymore")
        self._request_queue.put("{}\n".format(data).encode())

    def _send_queued_requests(self):
        while not self._closed.isSet():
            request = self._request_queue.get()
            if request == self._stop_sending_metrics_sentinel:
                self._request_queue.task_done()
                break
            self._socket.sendall(request)
            self._request_queue.task_done()

    def close(self, wait=True, timeout=None):
        if self._closed.isSet():
            return
        self._request_queue.put(self._stop_sending_metrics_sentinel)
        self._closed.set()
        if wait:
            self._sending_thread.join(None)


class ThreadedTCPClient(ThreadedTCPClientMixIn, TCPClient):
    """Statsd client using TCP in another thread to send metrics

    >>> client = ThreadedTCPClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    >>> client.close()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        TCPClient.__init__(self, host, port, prefix)
        ThreadedTCPClientMixIn.__init__(self)

    def batch_client(self, size=512):
        """Return a threadd TCP batch client with same settings of the threaded TCP client"""

        batch_client = ThreadedTCPBatchClient(self.host, self.port, self.prefix, size)
        self._configure_client(batch_client)
        return batch_client

    def __del__(self):
        self.close(False)
        TCPClient.__del__(self)


class ThreadedTCPBatchClient(ThreadedTCPClientMixIn, TCPBatchClient):
    """Statsd client using TCP in another thread to send multiple metrics
    in batch requests.

    >>> client = ThreadedTCPBatchClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    >>> client.flush()
    >>> client.decrement("event")
    >>> client.close()
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix='', batch_size=512):
        TCPBatchClient.__init__(self, host, port, prefix, batch_size)
        ThreadedTCPClientMixIn.__init__(self)

    def close(self, wait=True, timeout=None):
        self.flush()
        ThreadedTCPClientMixIn.close(self, wait, timeout)

    def __del__(self):
        self.close(False)
        TCPBatchClient.__del__(self)


__all__ = (ThreadedTCPClient, ThreadedTCPBatchClient)
