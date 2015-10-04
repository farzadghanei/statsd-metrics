"""
statsdmetrics.client.threaded
-----------------------------
Statsd clients to send metrics to server in a separate thread
"""

from threading import Thread

try:
    import Queue as queue
except ImportError:
    import queue

from . import DEFAULT_PORT
from .tcp import TCPClient as DefaultTCPClient


class ThreadedTCPClientMixIn(object):

    def __init__(self):
        self._stop_sending_metrics_sentinel = "__STOP__"
        self._request_queue = queue.Queue()
        self._sending_thread = Thread(target=self._send_queued_requests)
        self._sending_thread.daemon = True
        self._sending_thread.start()

    def _request(self, data):
        self._request_queue.put("{}\n".format(data).encode())

    def _send_queued_requests(self):
        while True:
            request = self._request_queue.get()
            if request == self._stop_sending_metrics_sentinel:
                self._request_queue.task_done()
                return
            self._get_open_socket().sendall(request)
            self._request_queue.task_done()

    def __del__(self):
        # signal the thread to quit
        self._request_queue.put(self._stop_sending_metrics_sentinel)


class TCPClient(ThreadedTCPClientMixIn, DefaultTCPClient):
    """Statsd client using TCP in another thread to send metrics

    >>> client = TCPClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4)
    >>> client.decrement("event", rate=0.2)
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        DefaultTCPClient.__init__(self, host, port, prefix)
        ThreadedTCPClientMixIn.__init__(self)

    def __del__(self):
        ThreadedTCPClientMixIn.__del__(self)
        DefaultTCPClient.__del__(self)


__all__ = (TCPClient,)
