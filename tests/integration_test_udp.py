#!/usr/bin/env python

"""
tests.integration_test_udp
==========================

Integration tests for the UDP client.

Setup a UDP server to receive metrics from the
UDP clients and assert they are correct.

"""

from __future__ import print_function

import sys
import signal
from datetime import datetime
from time import time, sleep
from collections import deque
from os.path import dirname
from unittest import TestCase, main
from threading import Thread

import re

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver  # type: ignore

project_dir = dirname(dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from statsdmetrics.client import Client, BatchClient


class UDPRequestHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        for line in self.rfile:
            self.server.requests.append(line.decode().strip())


class DummyStatsdServer(socketserver.ThreadingUDPServer):
    allow_reuse_address = True

    def __init__(self, address, request_handler=UDPRequestHandler, bind_and_activate=True):
        self.requests = deque()
        socketserver.ThreadingUDPServer.__init__(self, address, request_handler, bind_and_activate)


class UDPClienstTest(TestCase):

    @classmethod
    def shutdown_server(cls, *args):
        cls.server.shutdown()
        cls.server_thread.join(3)

    @classmethod
    def setUpClass(cls):
        cls.server = DummyStatsdServer(("localhost", 0), UDPRequestHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        signal.signal(signal.SIGTERM, cls.shutdown_server)
        signal.signal(signal.SIGINT, cls.shutdown_server)

    @classmethod
    def tearDownClass(cls):
        cls.shutdown_server()

    def setUp(self):
        self.__class__.server.requests.clear()

    def test_sending_metrics(self):
        start = datetime.now()
        start_timestamp = time()
        client = Client("localhost", self.__class__.port)
        client.increment("1.test", 5)
        client.increment("2.login")
        client.timing("3.query", 3600)
        client.gauge("4.memory", 102400)
        client.gauge_delta("5.memory", 256)
        client.gauge_delta("6.memory", -128)
        client.set("7.ip", "127.0.0.1")

        expected = [
                "1.test:5|c",
                "2.login:1|c",
                "3.query:3600|ms",
                "4.memory:102400|g",
                "5.memory:+256|g",
                "6.memory:-128|g",
                "7.ip:127.0.0.1|s",
        ]

        self.assert_server_received_expected_requests(expected)

        self.__class__.server.requests.clear()
        client.timing_since("1.query", start_timestamp)
        client.timing_since("2.other_query", start)
        chronometer = client.chronometer()
        chronometer.time_callable("3.sleepy", sleep, 1, (0.02,))

        @chronometer.wrap("4.wait_a_sec")
        def wait_a_sec():
            sleep(0.01)

        wait_a_sec()

        with client.stopwatch("5.my_with_block"):
            sleep(0.02)

        expected_patterns = [
            "1.query:[1-9]\d{0,4}\|ms",
            "2.other_query:[1-9]\d{0,4}\|ms",
            "3.sleepy:[1-9]\d{0,4}\|ms",
            "4.wait_a_sec:[1-9]\d{0,4}\|ms",
            "5.my_with_block:[1-9]\d{0,4}\|ms",
        ]
        self.assert_server_received_expected_request_regex(expected_patterns)

    def test_sending_batch_metrics(self):
        start = datetime.now()
        start_timestamp = time()
        client = BatchClient("localhost", self.__class__.port)
        client.increment("1.test", 8)
        client.increment("2.login")
        client.timing("3.query", 9600)
        client.gauge("4.memory", 102600)
        client.gauge_delta("5.memory", 2560)
        client.gauge_delta("6.memory", -1280)
        client.set("7.ip", "127.0.0.2")
        client.flush()

        expected = [
                "1.test:8|c",
                "2.login:1|c",
                "3.query:9600|ms",
                "4.memory:102600|g",
                "5.memory:+2560|g",
                "6.memory:-1280|g",
                "7.ip:127.0.0.2|s",
        ]

        self.assert_server_received_expected_requests(expected)

        self.__class__.server.requests.clear()
        client.timing_since("1.query", start_timestamp)
        client.timing_since("2.other_query", start)
        client.flush()

        chronometer = client.chronometer()
        chronometer.time_callable("3.sleepy", sleep, 1, (0.02,))

        @chronometer.wrap("4.wait_a_sec")
        def wait_a_sec():
            sleep(0.01)

        wait_a_sec()

        with client.stopwatch("5.my_with_block"):
            sleep(0.02)

        client.flush()

        expected_patterns = [
            "1.query:[1-9]\d{0,4}\|ms",
            "2.other_query:[1-9]\d{0,4}\|ms",
            "3.sleepy:[1-9]\d{0,4}\|ms",
            "4.wait_a_sec:[1-9]\d{0,4}\|ms",
            "5.my_with_block:[1-9]\d{0,4}\|ms",
        ]
        self.assert_server_received_expected_request_regex(expected_patterns)

    def assert_server_received_expected_requests(self, expected, timeout=3):
        requests = self.wait_for_requests_in_server(expected, timeout)
        self.assertEqual(sorted(expected), sorted(requests))

    def assert_server_received_expected_request_regex(self, expected_patterns, timeout=3):
        requests = self.wait_for_requests_in_server(expected_patterns, timeout)
        for regex_pattern in expected_patterns:
            matched = False
            for request in requests:
                if re.match(regex_pattern, request):
                    matched = True
                    break
            self.assertTrue(matched, "No match found for request pattern '{}'".format(regex_pattern))

    def wait_for_requests_in_server(self, expected, timeout):
        start_time = time()
        server = self.__class__.server
        while len(server.requests) < len(expected) and time() - start_time < timeout:
            sleep(0.2)
        return server.requests


if __name__ == '__main__':
    main()
