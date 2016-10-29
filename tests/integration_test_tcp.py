#!/usr/bin/env python

"""
tests.integration_test_tcp
==========================

Integration tests for the TCP clients.

Setup a TCP server to receive metrics from the
TCP clients and assert they are correct.

"""

from __future__ import print_function

import sys
import signal
from time import time, sleep
from collections import deque
from os.path import dirname
from unittest import TestCase, main
from threading import Thread
from multiprocessing import Process, Pipe

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver  # type: ignore

project_dir = dirname(dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from statsdmetrics.client.tcp import TCPClient, TCPBatchClient


PROC_CMD_SHUTDOWN = '<shutdown>'
PROC_CMD_FLUSH = '<flush>'
PROC_CMD_COUNT = '<count>'


class TCPRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        for line in self.rfile:
            self.server.requests.append(line.decode().strip())


class DummyTCPStatsdServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, address, request_handler=TCPRequestHandler, bind_and_activate=True):
        self.requests = deque()
        socketserver.ThreadingTCPServer.__init__(self, address, request_handler, bind_and_activate)


def start_dummy_tcp_server(pipe):
    server = DummyTCPStatsdServer(("localhost", 0))
    port = server.server_address[1]
    pipe.send(port)
    server_thread = Thread(target=server.serve_forever)
    server_thread.start()
    while True:
        command = pipe.recv()
        if command == PROC_CMD_SHUTDOWN:
            break
        elif command == PROC_CMD_COUNT:
            pipe.send(len(server.requests))
        elif command == PROC_CMD_FLUSH:
            pipe.send(server.requests)
            server.requests.clear()
    server.shutdown()
    server.server_close()
    server_thread.join()
    if server.socket:
        server.socket.close()



class TCPClienstTest(TestCase):

    @classmethod
    def shutdown_server(cls, *args):
        cls.control_pipe.send(PROC_CMD_SHUTDOWN)
        cls.server_proc.join()

    @classmethod
    def setUpClass(cls):
        control_pipe, server_pipe = Pipe()
        cls.server_proc = Process(target=start_dummy_tcp_server, args=(server_pipe,))
        cls.control_pipe = control_pipe
        signal.signal(signal.SIGINT, cls.shutdown_server)
        cls.server_proc.start()
        cls.port = cls.control_pipe.recv()

    @classmethod
    def tearDownClass(cls):
        cls.shutdown_server()

    def test_sending_metrics(self):
        client = TCPClient("localhost", self.__class__.port)
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
        client = TCPBatchClient("localhost", self.__class__.port)
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
        start_time = time()
        server_pipe = self.__class__.control_pipe
        requests = []
        while time() - start_time < timeout:
            sleep(0.5)
            server_pipe.send(PROC_CMD_COUNT)
            count = server_pipe.recv()
            if count:
                server_pipe.send(PROC_CMD_FLUSH)
                server_requests = server_pipe.recv()
                if server_requests:
                    requests.extend(server_requests)
            if len(requests) >= len(expected):
                break
        self.assertEqual(sorted(expected), sorted(requests))


if __name__ == '__main__':
    main()
