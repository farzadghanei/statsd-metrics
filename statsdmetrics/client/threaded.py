"""
statsdmetrics.client.threaded
-----------------------------
Statsd clients to send metrics to server over TCP over different threads
"""

from threading import Thread, Event

try:
    import Queue as queue
except ImportError:
    import queue

from . import DEFAULT_PORT
from .tcp import TCPClient as DefaultTCPClient


class ThreadedTCPClientMixIn(object):

    def __init__(self):
        self._request_queue = queue.Queue()
        self._closed = Event()

        self._sending_thread  = Thread(target=self._send_queued_requests)
        self._sending_thread.daemon = True
        self._sending_thread.start()

    def _request(self, data):
        if self._closed.isSet():
            raise Exception("ThreadedTCPClient is closed and will not accept new metrics")
        self._request_queue.put("{}\n".format(data).encode())

    def _send_queued_requests(self):
        while True:
            if self._closed.isSet():
                return
            try:
                request = self._request_queue.get(timeout=1)
            except queue.Empty as e:
                continue
            if request is None: # None in the queue is a signal to quit
                self._request_queue.task_done()
                return
            self._get_open_socket().sendall(request)
            self._request_queue.task_done()

    def close(self):
        if self._closed.isSet():
            return
        # signal the thread to quit
        self._request_queue.put(None)
        self._request_queue.join()
        self._closed.set()

    def __del__(self):
        if self._request_queue:
            self.close()


class TCPClient(ThreadedTCPClientMixIn, DefaultTCPClient):
    """Statsd client using TCP in another thread to send metrics

    >>> client = TCPClient("stats.example.org")
    >>> client.increment("event")
    >>> client.increment("event", 3, 0.4) # specify count and sample rate
    >>> client.decrement("event", rate=0.2) # reconnects again automatically
    """

    def __init__(self, host, port=DEFAULT_PORT, prefix=''):
        DefaultTCPClient.__init__(self, host, port, prefix)
        ThreadedTCPClientMixIn.__init__(self)

    def _request(self, data):
        self._request_queue.put("{}\n".format(data).encode())

    def __del__(self):
        ThreadedTCPClientMixIn.__del__(self)
        DefaultTCPClient.__del__(self)

__all__ = (TCPClient,)
