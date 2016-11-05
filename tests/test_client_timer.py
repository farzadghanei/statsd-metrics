"""
tests.test_client_timer
-----------------------
unit tests for timer module
"""
from time import time, sleep
from statsdmetrics.client import Client
from statsdmetrics.client.timer import Timer

try:
    import unittest.mock as mock
except ImportError:
    import mock

from . import BaseTestCase


class BaseTestTimer(BaseTestCase):
    def setUp(self):
        self.client = Client('127.0.0.1')
        self.request_mock = mock.MagicMock()
        self.client._request = self.request_mock
        self.timer = Timer(self.client)

    def test_since(self):
        start_time = time()
        sleep(0.01)
        self.assertEqual(self.timer.since("event", start_time), self.timer)
        self.assertEqual(self.request_mock.call_count, 1)
        (request,) = self.request_mock.call_args[0]
        self.assertRegex('event:[1-9]\d{0,3}\|ms', request)

        self.request_mock.reset_mock()
        self.assertEqual(self.timer.since("event", start_time, rate=0), self.timer)
        self.assertEqual(self.request_mock.call_count, 0)

    def test_time_callable(self):
        self.assertRaises(AssertionError, self.timer.time_callable, "event", "I'm not callable")
    
        self.assertEqual(
            self.timer.time_callable("event", self.wait_a_while),
            self.timer
        )
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "event:[1-9]\d{0,3}\|ms")
    
        self.request_mock.reset_mock()
        self.timer.time_callable("low.rate", self.wait_a_while, rate=0.1)
        self.assertEqual(self.request_mock.call_count, 0)

        args_passed = []
    
        def store_args(*args, **kwargs):
            args_passed.append(args)
            args_passed.append(kwargs)
            sleep(0.01)
    
        self.request_mock.reset_mock()
        self.timer.time_callable("with_args", store_args, 1, "arg1", "arg2", named_arg="named_value")
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        (request,) = request_args
        self.assertRegex(request, "with_args:[1-9]\d{0,3}\|ms")
        self.assertEqual(args_passed, [("arg1", "arg2"), dict(named_arg="named_value")])
    
    def wait_a_while(self):
        sleep(0.01)

