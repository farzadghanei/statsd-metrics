"""
tests.test_client
-----------------
unittests for statsdmetrics.client module
"""

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from statsdmetrics.client import (AutoClosingSharedSocket, Client, BatchClient, DEFAULT_PORT)
from . import MockMixIn, ClientTestCaseMixIn, BatchClientTestCaseMixIn


class TestSharedSocket(MockMixIn, unittest.TestCase):

    def setUp(self):
        self.doMock()
        self.mock_close = mock.MagicMock();
        self.mock_socket.close = self.mock_close

    def test_call_underlying_socket_methods(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        sock.close()
        addr = ("localhost", 8888)
        sock.sendall("sending all", addr)
        sock.sendto("sending to", addr)
        self.assertEqual(self.mock_close.call_count, 1)
        self.mock_sendall.assert_called_once_with("sending all", addr)
        self.mock_sendto.assert_called_once_with("sending to", addr)

    def test_close_on_no_more_client(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        self.assertFalse(sock.closed)
        client = Client("localhost")
        sock.add_client(client)
        self.assertFalse(sock.closed)
        sock.remove_client(client)
        self.assertTrue(sock.closed)
        self.assertEqual(self.mock_close.call_count, 1)

    def test_close_on_destruct(self):
        sock = AutoClosingSharedSocket(self.mock_socket)
        del sock
        self.assertEqual(self.mock_close.call_count, 1)


class TestClient(ClientTestCaseMixIn, unittest.TestCase):

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

        client.port = 8000
        client.prefix = "region.c_"
        client.increment("@login#", rate=0.6)
        self.mock_sendto.assert_called_with(
            "region.c_login:1|c|@0.6".encode(),
            ("127.0.0.2", 8000)
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
        client.port = 8000
        client.decrement("active!users", rate=0.7)
        self.mock_sendto.assert_called_with(
            "region.c_activeusers:-1|c|@0.7".encode(),
            ("127.0.0.2", 8000)
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
            "db.event_name:34.5|ms|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.port = 8000
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        self.mock_sendto.assert_called_with(
            "region.c_db-query:22.22|ms|@0.7".encode(),
            ("127.0.0.2", 8000)
        )

        self.mock_sendto.reset_mock()
        client.timing("low.rate", 12, rate=0.1)
        self.assertEqual(self.mock_sendto.call_count, 0)

        self.assertRaises(AssertionError, client.timing, "negative", -0.5)

    def test_gauge(self):
        client = Client("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        self.mock_sendto.assert_called_with(
            "memory:10240|g".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.port = 9000
        client.gauge("cpu percentage%", rate=0.9, value=98.3)
        self.mock_sendto.assert_called_with(
            "region.cpu_percentage:98.3|g|@0.9".encode(),
            ("127.0.0.2", 9000)
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
        client.port = 9000
        client.gauge_delta("cpu percentage%", rate=0.9, delta=-12)
        self.mock_sendto.assert_called_with(
            "region.cpu_percentage:-12|g|@0.9".encode(),
            ("127.0.0.2", 9000)
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
        client.port = 9000
        client.set("~username*", rate=0.9, value='first')
        self.mock_sendto.assert_called_with(
            "region.username:first|s|@0.9".encode(),
            ("127.0.0.2", 9000)
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

    def test_context_manager_flushs_metrics(self):
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

    def test_changing_remote_addr_in_context_does_not_affect_batch_client(self):
        client = Client("localhost")
        client._socket = self.mock_socket

        with client.batch_client() as batch_client:
            batch_client.increment("event", rate=0.5)
            client.port = 8888
            batch_client.timing("query", 1200)
            self.assertEqual(client.remote_address, ("127.0.0.2", 8888))
            self.assertEqual(batch_client.remote_address, ("127.0.0.2", 8125))

        expected_calls = [
                mock.call(bytearray("event:1|c|@0.5\nquery:1200|ms\n".encode()), ("127.0.0.2", 8125)),
        ]
        self.assertEqual(self.mock_sendto.mock_calls, expected_calls)

    def test_when_client_is_removed_the_socket_batch_client_socket_is_not_closed(self):
        client = Client("localhost")
        batch_client = client.batch_client()
        sock = batch_client._socket
        del client
        self.assertFalse(sock.closed)
        del batch_client
        self.assertTrue(sock.closed)


class TestBatchClient(BatchClientTestCaseMixIn, unittest.TestCase):

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
        client.port = 8000
        client.prefix = "pre."
        client.increment("login")
        client.increment("login.fail", 5, 0.2)
        client.increment("login.ok", rate=0.8)
        client.flush()
        self.mock_sendto.assert_called_once_with(
            bytearray("pre.login:1|c\npre.login.ok:1|c|@0.8\n".encode()),
            ("127.0.0.2", 8000)
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
        client.port = 8000
        client.decrement("session")
        client.decrement("session.fail", 2, 0.2)
        client.decrement("session.ok", rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.session:-1|c\npre.session.ok:-1|c|@0.6\n".encode()),
            ("127.0.0.2", 8000)
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
        client.port = 8000
        client.timing("query", 3)
        client.timing("process.request", 2, 0.2)
        client.timing("query.user", 350, rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.query:3|ms\npre.query.user:350|ms|@0.6\n".encode()),
            ("127.0.0.2", 8000)
        )

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
        client.port = 8000
        client.gauge("memory", 2048)
        client.gauge("memory", 8096, 0.2)
        client.gauge("storage", 512, rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.memory:2048|g\npre.storage:512|g|@0.6\n".encode()),
            ("127.0.0.2", 8000)
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
        client.port = 8000
        client.gauge_delta("memory", 2048)
        client.gauge_delta("memory", 8096, 0.2)
        client.gauge_delta("storage", -128, rate=0.7)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.memory:+2048|g\npre.storage:-128|g|@0.7\n".encode()),
            ("127.0.0.2", 8000)
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
        client.port = 8000
        client.set("user", 'second')
        client.set("user", 'third', 0.2)
        client.set("user", 'last', rate=0.5)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("pre.user:second|s\npre.user:last|s|@0.5\n".encode()),
            ("127.0.0.2", 8000)
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


if __name__ == "__main__":
    unittest.main()
