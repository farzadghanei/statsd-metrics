"""
tests.test_client
-----------------
unittests for statsdmetrics.client module
"""

import platform
import gc
import unittest
from time import time, sleep
import threading
from datetime import datetime

try:
    import unittest.mock as mock
except ImportError:
    import mock

from statsdmetrics.client import (AutoClosingSharedSocket, Client, BatchClient)
from statsdmetrics.client.timing import Chronometer, Stopwatch
from . import BaseTestCase, MockMixIn, ClientTestCaseMixIn, BatchClientTestCaseMixIn


class TestSharedSocket(MockMixIn, BaseTestCase):

    def setUp(self):
        self.doMock()
        self.mock_close = mock.MagicMock();
        self.mock_socket.close = self.mock_close

    def test_call_underlying_socket_methods(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        sock.close()
        address = ("localhost", 8888)
        sock.sendall("sending all", address)
        sock.sendto("sending to", address)
        self.assertEqual(self.mock_close.call_count, 1)
        self.mock_sendall.assert_called_once_with("sending all", address)
        self.mock_sendto.assert_called_once_with("sending to", address)

    def test_close_on_no_more_client(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        self.assertFalse(sock.closed)
        client = Client("localhost")
        sock.add_client(client)
        self.assertFalse(sock.closed)
        sock.remove_client(client)
        self.assertTrue(sock.closed)
        self.assertEqual(self.mock_close.call_count, 1)

    def test_close_on_no_more_client_multithreaded(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        self.assertFalse(sock.closed)

        client1 = Client("localhost")
        sock.add_client(client1)

        client2 = Client("localhost")
        sock.add_client(client2)

        client3 = Client("localhost")
        sock.add_client(client3)

        self.assertFalse(sock.closed)

        start_remove = threading.Event()

        def _remove_client(client):
            start_remove.wait()
            self.assertFalse(sock.closed)
            sock.remove_client(client)

        th1 = threading.Thread(target=_remove_client, args=[client1])
        th2 = threading.Thread(target=_remove_client, args=[client2])
        th3 = threading.Thread(target=_remove_client, args=[client3])

        th1.start()
        th2.start()
        th3.start()

        start_remove.set()

        th1.join()
        th2.join()
        th3.join()

        self.assertTrue(sock.closed)
        self.assertEqual(self.mock_close.call_count, 1)

    @unittest.skipIf(
        platform.python_implementation().lower() == 'jython',
        "Jython is not calling __del__ even if gc is called explicitly"
    )
    def test_close_on_destruct(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        del sock
        gc.collect()
        self.assertEqual(self.mock_close.call_count, 1)


class TestClient(ClientTestCaseMixIn, BaseTestCase):

    def test_increment(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.increment("event")
        self.mock_sendto.assert_called_with(
            "event:1|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.increment("event2", 5)
        self.mock_sendto.assert_called_with(
            "event2:5|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.increment("region.event name", 2, 0.5)
        self.mock_sendto.assert_called_with(
            "region.event_name:2|c|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.increment("@login#", rate=0.6)
        self.mock_sendto.assert_called_with(
            "region.c_login:1|c|@0.6".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.increment("low.rate", rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_decrement(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.decrement("event")
        self.mock_sendto.assert_called_with(
            "event:-1|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.decrement("event2", 5)
        self.mock_sendto.assert_called_with(
            "event2:-5|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.decrement("region.event name", 2, 0.5)
        self.mock_sendto.assert_called_with(
            "region.event_name:-2|c|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.decrement("active!users", rate=0.7)
        self.mock_sendto.assert_called_with(
            "region.c_activeusers:-1|c|@0.7".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.decrement("low.rate", rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_timing(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10)
        self.mock_sendto.assert_called_with(
            "event:10|ms".encode(),
            ("127.0.0.2", 8125)
        )
        client.timing("db.event name", 34.5, 0.5)
        self.mock_sendto.assert_called_with(
            "db.event_name:34|ms|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        self.mock_sendto.assert_called_with(
            "region.c_db-query:22|ms|@0.7".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.timing("low.rate", 12, rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

        self.assertRaises(AssertionError, client.timing, "negative", -1)

    def test_timing_since_with_timestamp_as_number(self):
        start_time = time()
        client = Client("localhost")
        client._socket = self.mock_socket

        self.assertRaises(AssertionError, client.timing_since, "negative", -1)

        sleep(0.01)
        client.timing_since("event", start_time)
        self.assertEqual(self.mock_sendto.call_count, 1)
        socket_sendto_args = self.mock_sendto.call_args
        self.assertEqual(len(socket_sendto_args), 2)
        request, remote_address = socket_sendto_args[0]
        self.assertRegex(request.decode(), "event:[1-9]+\d{0,3}\|ms")
        self.assertEqual(remote_address, ("127.0.0.2", 8125))
        self.mock_sendto.reset_mock()

        client.timing_since("low.rate", start_time, rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_timing_since_with_datetime_timestamp(self):
        start_time = datetime.now()
        client = Client("localhost")
        client._socket = self.mock_socket

        sleep(0.01)
        client.timing_since("event", start_time)
        self.assertEqual(self.mock_sendto.call_count, 1)
        socket_sendto_args = self.mock_sendto.call_args
        self.assertEqual(len(socket_sendto_args), 2)
        request, remote_address = socket_sendto_args[0]
        self.assertRegex(request.decode(), "event:[1-9]\d{0,3}\|ms")
        self.assertEqual(remote_address, ("127.0.0.2", 8125))
        self.mock_sendto.reset_mock()

        client.timing_since("low.rate", start_time, rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_timing_since_with_none_float_datetimes_fails(self):
        client = Client("localhost")

        self.assertRaises(ValueError, client.timing_since, "event", "string")
        self.assertRaises(ValueError, client.timing_since, "event", None)
        self.assertRaises(ValueError, client.timing_since, "event", self)
        self.assertRaises(ValueError, client.timing_since, "event", client)

    def test_gauge(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        self.mock_sendto.assert_called_with(
            "memory:10240|g".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.gauge("cpu percentage%", rate=0.9, value=98.3)
        self.mock_sendto.assert_called_with(
            "region.cpu_percentage:98.3|g|@0.9".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.gauge("low.rate", 128, 0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

        self.assertRaises(AssertionError, client.gauge, "negative", -5)

    def test_gauge_delta(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory!", 128)
        self.mock_sendto.assert_called_with(
            "memory:+128|g".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.gauge_delta("cpu percentage%", rate=0.9, delta=-12)
        self.mock_sendto.assert_called_with(
            "region.cpu_percentage:-12|g|@0.9".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.gauge_delta("low.rate", 10, 0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_set(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.set("ip address", "10.10.10.1")
        self.mock_sendto.assert_called_with(
            "ip_address:10.10.10.1|s".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.set("~username*", rate=0.9, value='first')
        self.mock_sendto.assert_called_with(
            "region.username:first|s|@0.9".encode(),
            ("127.0.0.2", 8125)
        )

        self.mock_sendto.reset_mock()
        client.set("low.rate", 256, 0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_context_manager_creates_batch_client(self):
        client = Client("localhost")
        client._socket = self.mock_socket

        with client.batch_client() as batch_client:
            self.assertIsInstance(batch_client, BatchClient)
            self.assertGreater(batch_client.batch_size, 0)
            self.assertEqual(client.host, batch_client.host)
            self.assertEqual(client.port, batch_client.port)
            self.assertEqual(
                client._remote_address,
                batch_client._remote_address
            )
            self.assertEqual(
                client._socket,
                batch_client._socket
            )

        with client.batch_client(2048) as batch_client:
            self.assertEqual(batch_client.batch_size, 2048)

    def test_context_manager_flushes_metrics(self):
        client = Client("localhost", prefix="_.")
        client._socket = self.mock_socket

        with client.batch_client() as batch_client:
            batch_client.increment("event", rate=0.5)
            batch_client.timing("query", 1200)
            batch_client.decrement("event", rate=0.2)
            self.assertEqual(self.mock_sendto.call_count, 0)

        expected_calls = [
                mock.call(bytearray("_.event:1|c|@0.5\n_.query:1200|ms\n".encode()), ("127.0.0.2", 8125)),
        ]
        self.assertEqual(self.mock_sendto.mock_calls, expected_calls)

    def test_when_client_is_removed_the_socket_batch_client_socket_is_not_closed(self):
        client = Client("localhost")
        batch_client = client.batch_client()
        sock = batch_client._socket
        del client
        gc.collect()
        self.assertFalse(sock.closed)

    def test_client_creates_chronometer(self):
        client = Client("localhost")
        chronometer = client.chronometer()
        self.assertIsInstance(chronometer, Chronometer)
        self.assertEqual(chronometer.client, client)

    def test_client_creates_stopwatch(self):
        test_start_timestamp = time()
        one_minute_before_test = test_start_timestamp - 60
        client = Client("localhost")
        client._socket = self.mock_socket
        stopwatch = client.stopwatch("event")
        self.assertIsInstance(stopwatch, Stopwatch)
        self.assertEqual(stopwatch.client, client)
        self.assertEqual(stopwatch.rate, 1)
        self.assertGreaterEqual(stopwatch.reference, test_start_timestamp)

        stopwatch_low_rate = client.stopwatch("low_rate", rate=0.001)
        self.assertEqual(stopwatch_low_rate.rate, 0.001)
        self.assertGreaterEqual(stopwatch.reference, test_start_timestamp)

        stopwatch_1min_ref = client.stopwatch("low_rate", reference=one_minute_before_test)
        self.assertGreaterEqual(test_start_timestamp, stopwatch_1min_ref.reference)

        with client.stopwatch("something"):
            sleep(0.01)

        self.assertEqual(self.mock_sendto.call_count, 1)
        request_args = self.mock_sendto.call_args[0]
        self.assertEqual(len(request_args), 2)
        request = request_args[0]
        self.assertRegex(request.decode(), "something:[1-9]\d{0,3}\|ms")


class TestBatchClient(BatchClientTestCaseMixIn, BaseTestCase):

    def setUp(self):
        super(TestBatchClient, self).setUp()
        self.clientClass = BatchClient

    def test_increment(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.increment("event", 2, 0.5)
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("event:2|c|@0.5\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.increment("login")
        client.increment("login.fail", 5, 0.2)
        client.increment("login.ok", rate=0.8)
        client.flush()
        self.mock_sendto.assert_called_once_with(
            bytearray("pre.login:1|c\npre.login.ok:1|c|@0.8\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_decrement(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.decrement("event", 3, 0.7)
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("event:-3|c|@0.7\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.decrement("session")
        client.decrement("session.fail", 2, 0.2)
        client.decrement("session.ok", rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.session:-1|c\npre.session.ok:-1|c|@0.6\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_timing(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10, 0.4)
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("event:10|ms|@0.4\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.timing("query", 3)
        client.timing("process.request", 2, 0.2)
        client.timing("query.user", 350, rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.query:3|ms\npre.query.user:350|ms|@0.6\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_timing_since_with_timestamp_as_number(self):
        start_time = time()
        client = BatchClient("localhost")
        client._socket = self.mock_socket

        self.assertRaises(AssertionError, client.timing_since, "negative", -1)

        sleep(0.01)
        client.timing_since("event", start_time)
        client.timing_since("other_event", start_time)
        client.flush()
        self.assertEqual(self.mock_sendto.call_count, 1)
        socket_sendto_args = self.mock_sendto.call_args
        self.assertEqual(len(socket_sendto_args), 2)
        request, remote_address = socket_sendto_args[0]
        self.assertEqual(remote_address, ("127.0.0.2", 8125))
        self.assertRegex(request.decode(), "event:[1-9]+\d{0,3}\|ms\nother_event:[1-9]+\d{0,3}\|ms")

        self.mock_sendto.reset_mock()

        client.timing_since("low.rate", start_time, rate=0.1)
        client.flush()
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_timing_since_with_datetime_timestamp(self):
        start_time = datetime.now()
        client = BatchClient("localhost")
        client._socket = self.mock_socket

        sleep(0.01)
        client.timing_since("event", start_time)
        client.timing_since("other_event", start_time)
        client.flush()
        self.assertEqual(self.mock_sendto.call_count, 1)
        socket_sendto_args = self.mock_sendto.call_args
        self.assertEqual(len(socket_sendto_args), 2)
        request, remote_address = socket_sendto_args[0]
        self.assertRegex(request.decode(), "event:[1-9]\d{0,3}\|ms\nother_event:[1-9]\d{0,3}\|ms")
        self.assertEqual(remote_address, ("127.0.0.2", 8125))
        self.mock_sendto.reset_mock()

        client.timing_since("low.rate", start_time, rate=0.1)
        client.flush()
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_gauge(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("memory:10240|g\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.gauge("memory", 2048)
        client.gauge("memory", 8096, 0.2)
        client.gauge("storage", 512, rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.memory:2048|g\npre.storage:512|g|@0.6\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_gauge_delta(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory", -512)
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("memory:-512|g\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.gauge_delta("memory", 2048)
        client.gauge_delta("memory", 8096, 0.2)
        client.gauge_delta("storage", -128, rate=0.7)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.memory:+2048|g\npre.storage:-128|g|@0.7\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_set(self):
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        client.set("username", 'first')
        client.flush()
        self.mock_sendto.assert_called_with(
            bytearray("username:first|s\n".encode()),
            ("127.0.0.2", 8125)
        )
        self.mock_sendto.reset_mock()
        client.prefix = "pre."
        client.set("user", 'second')
        client.set("user", 'third', 0.2)
        client.set("user", 'last', rate=0.5)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.user:second|s\npre.user:last|s|@0.5\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_metrics_partitioned_into_batches(self):
        client = BatchClient("localhost", batch_size=20)
        client._socket = self.mock_socket
        client.increment("fit.a.batch.123")
        client.timing("_", 1)
        client.increment("larger.than.batch.becomes.a.batch", 5, 0.9)
        client.decrement("12")
        client.set("ab", 'z')
        client.timing("small", 9)
        client.gauge("overflow.previous", 10)
        client.gauge_delta("next", -10)
        client.increment("_")
        client.flush()
        expected_calls = [
                mock.call(bytearray("fit.a.batch.123:1|c\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("_:1|ms\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("larger.than.batch.becomes.a.batch:5|c|@0.9\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("12:-1|c\nab:z|s\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("small:9|ms\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("overflow.previous:10|g\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("next:-10|g\n_:1|c\n".encode()), ("127.0.0.2", 8125)),
        ]
        self.assertEqual(self.mock_sendto.mock_calls, expected_calls)

    def test_clear(self):
        client = BatchClient("localhost", batch_size=20)
        client._socket = self.mock_socket
        client.increment("first")
        client.decrement("second")
        client.timing("db.query", 1)
        client.clear()
        client.flush()
        self.assertEqual(self.mock_sendto.call_count, 0)

    def test_create_unit_client(self):
        batch_client = BatchClient("localhost")
        batch_client._socket = self.mock_socket
        client = batch_client.unit_client()
        self.assertIsInstance(client, Client)
        self.assertEqual(batch_client.host, client.host)
        self.assertEqual(batch_client.port, client.port)
        self.assertEqual(
            batch_client._remote_address,
            client._remote_address
        )
        self.assertEqual(
            batch_client._socket,
            client._socket
        )

    def test_when_client_is_removed_the_socket_batch_client_socket_is_not_closed(self):
        batch_client = BatchClient("localhost")
        unit_client = batch_client.unit_client()
        sock = batch_client._socket
        del batch_client
        gc.collect()
        self.assertFalse(sock.closed)

    def test_client_creates_chronometer(self):
        client = BatchClient("localhost")
        chronometer = client.chronometer()
        self.assertIsInstance(chronometer, Chronometer)
        self.assertEqual(chronometer.client, client)

    def test_client_creates_stopwatch(self):
        test_start_timestamp = time()
        one_minute_before_test = test_start_timestamp - 60
        client = BatchClient("localhost")
        client._socket = self.mock_socket
        stopwatch = client.stopwatch("event")
        self.assertIsInstance(stopwatch, Stopwatch)
        self.assertEqual(stopwatch.client, client)
        self.assertEqual(stopwatch.rate, 1)
        self.assertGreaterEqual(stopwatch.reference, test_start_timestamp)

        stopwatch_low_rate = client.stopwatch("low_rate", rate=0.001)
        self.assertEqual(stopwatch_low_rate.rate, 0.001)
        self.assertGreaterEqual(stopwatch.reference, test_start_timestamp)

        stopwatch_1min_ref = client.stopwatch("low_rate", reference=one_minute_before_test)
        self.assertGreaterEqual(test_start_timestamp, stopwatch_1min_ref.reference)

        with client.stopwatch("something"):
            sleep(0.01)

        self.assertEqual(self.mock_sendto.call_count, 0)
        client.flush()

        self.assertEqual(self.mock_sendto.call_count, 1)
        request_args = self.mock_sendto.call_args[0]
        self.assertEqual(len(request_args), 2)
        request = request_args[0]
        self.assertRegex(request.decode(), "something:[1-9]\d{0,3}\|ms")

if __name__ == "__main__":
    unittest.main()
