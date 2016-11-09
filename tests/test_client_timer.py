"""
tests.test_client_timer
-----------------------
unit tests for timer module
"""
from time import time, sleep
from statsdmetrics.client import Client
from statsdmetrics.client.timer import Timer, StopWatch

try:
    import unittest.mock as mock
except ImportError:
    import mock

from . import BaseTestCase


class TestTimer(BaseTestCase):
    def setUp(self):
        self.client = Client('127.0.0.1')
        self.request_mock = mock.MagicMock()
        self.client._request = self.request_mock
        self.timer = Timer(self.client)

    def test_sample_rate_configuration(self):
        self.assertEqual(self.timer.rate, 1)
        timer = Timer(self.client, 0.3)
        self.assertEqual(timer.rate, 0.3)
        with self.assertRaises(AssertionError):
            timer.rate = "not a number"
        with self.assertRaises(AssertionError):
            timer.rate = 2
        with self.assertRaises(AssertionError):
            timer.rate = -0.3

    def test_get_set_client(self):
        self.assertEqual(self.timer.client, self.client)
        client = Client('127.0.0.2')
        timer = Timer(client)
        self.assertEqual(timer.client, client)
        timer.client = self.client
        self.assertEqual(timer.client, self.client)

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

        with self.assertRaises(AssertionError):
            self.timer.since("event", start_time, rate=-0.2)
        with self.assertRaises(AssertionError):
            self.timer.since("event", start_time, rate=1.01)

    def test_time_callable(self):
        self.assertRaises(AssertionError, self.timer.time_callable, "event", "I'm not callable")
    
        self.assertEqual(
            self.timer.time_callable("event", self.wait_a_while),
            "waited"
        )
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "event:[1-9]\d{0,3}\|ms")
    
        self.request_mock.reset_mock()
        self.timer.time_callable("low.rate", self.wait_a_while, rate=0.0001)
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

        with self.assertRaises(AssertionError):
            self.timer.time_callable("event", self.wait_a_while, rate=-0.2)
        with self.assertRaises(AssertionError):
            self.timer.time_callable("event", self.wait_a_while, rate=1.01)

    def test_timer_function_decorator(self):
        nap_calls = []

        @self.timer.wrap(name="event")
        def take_a_nap():
            nap_calls.append("nap called")
            sleep(0.1)

        take_a_nap()
        self.assertEqual(nap_calls, ["nap called"])
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "event:[1-9]\d{0,3}\|ms")

        self.request_mock.reset_mock()
        nap_low_rate_calls = []

        @self.timer.wrap("event", 0.001)
        def nap_low_rate():
            nap_low_rate_calls.append("low rate called")
            sleep(0.01)

        nap_low_rate()
        self.assertEqual(nap_low_rate_calls, ["low rate called"])
        self.assertEqual(self.request_mock.call_count, 0)

        with self.assertRaises(AssertionError):
            @self.timer.wrap("invalid_rate", -0.1)
            def wont_be_called():
                pass

    def wait_a_while(self):
        sleep(0.01)
        return "waited"


class TestStopWatch(BaseTestCase):
    def setUp(self):
        self.client = Client('127.0.0.1')
        self.request_mock = mock.MagicMock()
        self.client._request = self.request_mock
        self.metric_name = "timed_event"
        self.stop_watch = StopWatch(self.client, self.metric_name)

    def test_name(self):
        stop_watch = StopWatch(self.client, "new_watch")
        self.assertEqual(stop_watch.name, "new_watch")
        stop_watch.name = self.metric_name
        self.assertEqual(stop_watch.name, self.metric_name)

    def test_sample_rate_configuration(self):
        self.assertEqual(self.stop_watch.rate, 1)
        stop_watch = StopWatch(self.client, "new_watch", rate=0.3)
        self.assertEqual(stop_watch.rate, 0.3)
        with self.assertRaises(AssertionError):
            stop_watch.rate = "not a number"
        with self.assertRaises(AssertionError):
            stop_watch.rate = 2
        with self.assertRaises(AssertionError):
            stop_watch.rate = -0.3

    def test_get_set_client(self):
        self.assertEqual(self.stop_watch.client, self.client)
        client = Client('127.0.0.2')
        stop_watch = StopWatch(client, "new_watch")
        self.assertEqual(stop_watch.client, client)
        stop_watch.client = self.client
        self.assertEqual(stop_watch.client, self.client)

    def test_reset(self):
        original_reference = self.stop_watch.reference
        sleep(0.01)
        self.assertEqual(self.stop_watch.reset(), self.stop_watch)
        self.assertGreater(self.stop_watch.reference, original_reference)

    def test_send(self):
        sleep(0.01)
        self.stop_watch.send()
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "timed_event:[1-9]\d{0,3}\|ms")

        self.request_mock.reset_mock()
        self.stop_watch.send(rate=0)
        self.assertEqual(self.request_mock.call_count, 0)

    def test_stop_watch_as_context_manager(self):
        original_reference = self.stop_watch.reference
        with self.stop_watch:
            sleep(0.01)
        self.assertGreater(self.stop_watch.reference, original_reference, "stop watch as context manager resets")
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "timed_event:[1-9]\d{0,3}\|ms")

        self.request_mock.reset_mock()
        stop_watch = StopWatch(self.client, "low_rate", rate=0)
        with stop_watch:
            sleep(0.01)
        self.assertEqual(self.request_mock.call_count, 0)
