"""
statsdmetrics.client.timing
---------------------------
Easy to use classes to send timing metrics
"""
import functools
from datetime import datetime
from time import time

try:
    from typing import Union, Callable, Any, Tuple, Dict
except ImportError:
    Union, Callable, Any, Tuple, Dict = None, None, None, None, None  # type: ignore


def assert_timestamp(timestamp):
    # type: (Any) -> None
    assert isinstance(timestamp, int) or isinstance(timestamp, float)


def assert_sample_rate(rate):
    # type: (Any) -> None
    assert isinstance(rate, int) or isinstance(rate, float)
    assert 0 <= rate <= 1


class ClientWrapper(object):
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client


class SampleRateMixIn(object):
    def __init__(self, rate=1):
        # type: (float) -> None
        assert_sample_rate(rate)
        self._rate = rate

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        # type: (float) -> None
        assert_sample_rate(rate)
        self._rate = rate


class Chronometer(ClientWrapper, SampleRateMixIn):
    def __init__(self, client, rate=1):
        # type: (Any, float) -> None
        SampleRateMixIn.__init__(self, rate)
        ClientWrapper.__init__(self, client)

    def since(self, name, timestamp, rate=None):
        # type (str, Union[float, datetime], float) -> Chronometer
        if rate is None:
            rate = self._rate
        else:
            assert_sample_rate(rate)

        self._client.timing_since(name, timestamp, rate)
        return self

    def time_callable(self, name, target, rate=None, args=(), kwargs={}):
        # type: (str, Callable, float, Tuple, Dict) -> Chronometer
        """Send a Timer metric calculating duration of execution of the provided callable"""
        assert callable(target)
        if rate is None:
            rate = self._rate
        else:
            assert_sample_rate(rate)
        start_time = time()  # type: float
        result = target(*args, **kwargs)
        self.since(name, start_time, rate)
        return result

    def wrap(self, name, rate=None):
        # type: (str, float) -> Callable
        if rate is None:
            rate = self._rate
        else:
            assert_sample_rate(rate)

        def create_decorator(func):
            # type: (Callable) -> Callable
            @functools.wraps(func)
            def decorator(*args, **kwargs):
                return self.time_callable(name, func, rate, args, kwargs)
            return decorator
        return create_decorator


class Stopwatch(ClientWrapper, SampleRateMixIn):
    def __init__(self, client, name, rate=1, reference=None):
        # type: (Any, str, float, float) -> None
        if reference is None:
            reference = time()
        else:
            assert_timestamp(reference)
        SampleRateMixIn.__init__(self, rate)
        ClientWrapper.__init__(self, client)
        self._name = str(name)
        self._paused_duration = 0
        self._reference = reference

    @property
    def reference(self):
        return self._reference

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        # type: (str) -> None
        self._name = str(name)

    def reset(self):
        # type: () -> Stopwatch
        """Reset stop watch by setting now as reference"""
        self._reference = time()
        return self

    def send(self, rate=None):
        # type: (float) -> Stopwatch
        if rate is None:
            rate = self._rate
        else:
            assert_sample_rate(rate)
        self.client.timing_since(self._name, self._reference, rate)
        return self

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.send()

__all__= ['Chronometer', 'Stopwatch']
