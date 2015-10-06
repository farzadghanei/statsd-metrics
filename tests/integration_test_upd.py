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
from time import time, sleep
from collections import deque
from os.path import dirname
from unittest import TestCase, main
from threading import Thread

try:
    import SocketServer as socketserver
except ImportError:
    import socketserver


sys.path.insert(0, dirname(dirname(__file__)))

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
    def shutdown_server(cls):
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

        self.assertServerReceivedExpectedRequests(expected)

    def test_sending_batch_metrics(self):
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

        self.assertServerReceivedExpectedRequests(expected)

    def assertServerReceivedExpectedRequests(self, expected):
        timeout = 3
        starttime = time()
        server = self.__class__.server
        while len(server.requests) < len(expected) and time() - starttime < timeout:
            sleep(0.2)
        self.assertEqual(expected, sorted(server.requests))

if __name__ == '__main__':
    main()
