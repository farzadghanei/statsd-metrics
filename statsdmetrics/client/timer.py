"""
statsdmetrics.client.timer
--------------------------
Easy to use classes to send timing metrics
"""
import functools
from time import time

from statsdmetrics.client import AbstractClient

try:
    from typing import Union, Callable, Any
except ImportError:
    Union, Callable, Any = None, None, None  # type: ignore


class ClientWrapper(object):
    def __init__(self, client):
        # type (AbstractClient) -> None
        assert isinstance(client, AbstractClient)
        self._client = client

    @property
    def client(self):
        # type: () -> AbstractClient
        return self._client

    @client.setter
    def client(self, client):
        # type: (AbstractClient) -> None
        assert isinstance(client, AbstractClient)
        self._client = client


class Timer(ClientWrapper):
    def since(self, name, timestamp, rate=1):
        # type (str, Union[float, datetime], float) -> Timer
        self._client.timing_since(name, timestamp, rate)
        return self

    def time_callable(self, name, target, rate=1, *args, **kwargs):
        # type: (str, Callable, float, *Any, **Any) -> Timer
        """Send a Timer metric calculating duration of execution of the provided callable"""
        assert callable(target)
        start_time = time()  # type: float
        result = target(*args, **kwargs)
        self.since(name, start_time, rate)
        return result

    def wrap(self, name, rate=1):
        # type: (str, float) -> Callable
        def create_decorator(func):
            # type: (Callable) -> Callable
            @functools.wraps(func)
            def decorator(*args, **kwargs):
                return self.time_callable(name, func, rate, *args, **kwargs)
            return decorator
        return create_decorator

