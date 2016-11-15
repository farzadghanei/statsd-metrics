"""
tests.test_client_timer
-----------------------
unit tests for timer module
"""
from time import time, sleep
from statsdmetrics.client import Client
from statsdmetrics.client.timing import Chronometer, Stopwatch

try:
    import unittest.mock as mock
except ImportError:
    import mock

from . import BaseTestCase


class TestChronometer(BaseTestCase):
    def setUp(self):
        self.client = Client('127.0.0.1')
        self.request_mock = mock.MagicMock()
        self.client._request = self.request_mock
        self.chronometer = Chronometer(self.client)

    def test_sample_rate_configuration(self):
        self.assertEqual(self.chronometer.rate, 1)
        chronometer = Chronometer(self.client, 0.3)
        self.assertEqual(chronometer.rate, 0.3)
        with self.assertRaises(AssertionError):
            chronometer.rate = "not a number"
        with self.assertRaises(AssertionError):
            chronometer.rate = 2
        with self.assertRaises(AssertionError):
            chronometer.rate = -0.3

    def test_get_set_client(self):
        self.assertEqual(self.chronometer.client, self.client)
        client = Client('127.0.0.2')
        chronometer = Chronometer(client)
        self.assertEqual(chronometer.client, client)
        chronometer.client = self.client
        self.assertEqual(chronometer.client, self.client)

    def test_since(self):
        start_time = time()
        sleep(0.01)
        self.assertEqual(self.chronometer.since("event", start_time), self.chronometer)
        self.assertEqual(self.request_mock.call_count, 1)
        (request,) = self.request_mock.call_args[0]
        self.assertRegex('event:[1-9]\d{0,3}\|ms', request)

        self.request_mock.reset_mock()
        self.assertEqual(self.chronometer.since("event", start_time, rate=0), self.chronometer)
        self.assertEqual(self.request_mock.call_count, 0)

        with self.assertRaises(AssertionError):
            self.chronometer.since("event", start_time, rate=-0.2)
        with self.assertRaises(AssertionError):
            self.chronometer.since("event", start_time, rate=1.01)

    def test_time_callable(self):
        self.assertRaises(AssertionError, self.chronometer.time_callable, "event", "I'm not callable")
    
        self.assertEqual(
            self.chronometer.time_callable("event", self.wait_a_while),
            "waited"
        )
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "event:[1-9]\d{0,3}\|ms")
    
        self.request_mock.reset_mock()
        self.chronometer.time_callable("low.rate", self.wait_a_while, rate=0.0001)
        self.assertEqual(self.request_mock.call_count, 0)

        args_passed = []
    
        def store_args(*args, **kwargs):
            args_passed.append(args)
            args_passed.append(kwargs)
            sleep(0.01)
    
        self.request_mock.reset_mock()
        self.chronometer.time_callable("with_args", store_args, 1, ("arg1", "arg2"), dict(named_arg="named_value"))
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        (request,) = request_args
        self.assertRegex(request, "with_args:[1-9]\d{0,3}\|ms")
        self.assertEqual(args_passed, [("arg1", "arg2"), dict(named_arg="named_value")])

        with self.assertRaises(AssertionError):
            self.chronometer.time_callable("event", self.wait_a_while, rate=-0.2)
        with self.assertRaises(AssertionError):
            self.chronometer.time_callable("event", self.wait_a_while, rate=1.01)

    def test_timer_function_decorator(self):
        nap_calls = []

        @self.chronometer.wrap(name="event")
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

        @self.chronometer.wrap("event", 0.001)
        def nap_low_rate():
            nap_low_rate_calls.append("low rate called")
            sleep(0.01)

        nap_low_rate()
        self.assertEqual(nap_low_rate_calls, ["low rate called"])
        self.assertEqual(self.request_mock.call_count, 0)

        with self.assertRaises(AssertionError):
            @self.chronometer.wrap("invalid_rate", -0.1)
            def wont_be_called():
                pass

    def wait_a_while(self):
        sleep(0.01)
        return "waited"


class TestStopwatch(BaseTestCase):
    def setUp(self):
        self.client = Client('127.0.0.1')
        self.request_mock = mock.MagicMock()
        self.client._request = self.request_mock
        self.metric_name = "timed_event"
        self.stopwatch = Stopwatch(self.client, self.metric_name)

    def test_name(self):
        stopwatch = Stopwatch(self.client, "new_watch")
        self.assertEqual(stopwatch.name, "new_watch")
        stopwatch.name = self.metric_name
        self.assertEqual(stopwatch.name, self.metric_name)

    def test_sample_rate_configuration(self):
        self.assertEqual(self.stopwatch.rate, 1)
        stopwatch = Stopwatch(self.client, "new_watch", rate=0.3)
        self.assertEqual(stopwatch.rate, 0.3)
        with self.assertRaises(AssertionError):
            stopwatch.rate = "not a number"
        with self.assertRaises(AssertionError):
            stopwatch.rate = 2
        with self.assertRaises(AssertionError):
            stopwatch.rate = -0.3

    def test_get_set_client(self):
        self.assertEqual(self.stopwatch.client, self.client)
        client = Client('127.0.0.2')
        stopwatch = Stopwatch(client, "new_watch")
        self.assertEqual(stopwatch.client, client)
        stopwatch.client = self.client
        self.assertEqual(stopwatch.client, self.client)

    def test_reset(self):
        original_reference = self.stopwatch.reference
        sleep(0.01)
        self.assertEqual(self.stopwatch.reset(), self.stopwatch)
        self.assertGreater(self.stopwatch.reference, original_reference)

    def test_send(self):
        sleep(0.01)
        self.stopwatch.send()
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "timed_event:[1-9]\d{0,3}\|ms")

        self.request_mock.reset_mock()
        self.stopwatch.send(rate=0)
        self.assertEqual(self.request_mock.call_count, 0)

    def test_stopwatch_as_context_manager(self):
        original_reference = self.stopwatch.reference
        with self.stopwatch:
            sleep(0.01)
        self.assertGreater(self.stopwatch.reference, original_reference, "stop watch as context manager resets")
        self.assertEqual(self.request_mock.call_count, 1)
        request_args = self.request_mock.call_args[0]
        self.assertEqual(len(request_args), 1)
        request = request_args[0]
        self.assertRegex(request, "timed_event:[1-9]\d{0,3}\|ms")

        self.request_mock.reset_mock()
        stopwatch = Stopwatch(self.client, "low_rate", rate=0)
        with stopwatch:
            sleep(0.01)
        self.assertEqual(self.request_mock.call_count, 0)
