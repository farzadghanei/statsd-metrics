"""
statsdmetrics.client.timer
--------------------------
Easy to use classes to send timing metrics
"""

from time import time
from datetime import datetime
from statsdmetrics.client import AbstractClient

try:
    from typing import Union, Callable, Any
except ImportError:
    Union, Callable, Any = None, None, None  # type: ignore


class Timer(object):
    def __init__(self, client):
        # type (AbstractClient) -> None
        assert isinstance(client, AbstractClient)
        self.client = client

    def since(self, name, timestamp, rate=1):
        # type (str, Union[float, datetime], float) -> Timer
        self.client.timing_since(name, timestamp, rate)
        return self

    def time_callable(self, name, target, rate=1, *args, **kwargs):
        # type: (str, Callable, float, *Any, **Any) -> Timer
        """Send a Timer metric calculating duration of execution of the provided callable"""
        assert callable(target)
        start_time = time()  # type: float
        target(*args, **kwargs)
        return self.since(name, start_time, rate)

