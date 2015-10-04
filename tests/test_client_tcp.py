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

from statsdmetrics.client.tcp import TCPClient, TCPBatchClient
from . import ClientTestCaseMixIn, BatchClientTestCaseMixIn


class TestTCPClient(ClientTestCaseMixIn, unittest.TestCase):

    def setUp(self):
        super(TestTCPClient, self).setUp()
        self.clientClass = TCPClient

    def test_increment(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.increment("event")
        self.mock_sendall.assert_called_with("event:1|c\n".encode())
        client.increment("region.event name", 2, 0.5)
        self.mock_sendall.assert_called_with("region.event_name:2|c|@0.5\n".encode())

    def test_decrement(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.decrement("event")
        self.mock_sendall.assert_called_with(
            "event:-1|c\n".encode()
        )
        client.decrement("event2", 5)
        self.mock_sendall.assert_called_with(
            "event2:-5|c\n".encode()
        )
        client.decrement("region.event name", 2, 0.5)
        self.mock_sendall.assert_called_with(
            "region.event_name:-2|c|@0.5\n".encode()
        )

    def test_timing(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10)
        self.mock_sendall.assert_called_with(
            "event:10|ms\n".encode()
        )
        client.timing("db.event name", 34.5, 0.5)
        self.mock_sendall.assert_called_with(
            "db.event_name:34.5|ms|@0.5\n".encode(),
        )

        client.prefix = "region.c_"
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        self.mock_sendall.assert_called_with(
            "region.c_db-query:22.22|ms|@0.7\n".encode(),
        )

        self.mock_sendall.reset_mock()
        client.timing("low.rate", 12, rate=0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

        self.assertRaises(AssertionError, client.timing, "negative", -0.5)

    def test_gauge(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        self.mock_sendall.assert_called_with(
            "memory:10240|g\n".encode()
        )

        client.prefix = "region."
        client.gauge("cpu percentage%", rate=0.9, value=98.3)
        self.mock_sendall.assert_called_with(
            "region.cpu_percentage:98.3|g|@0.9\n".encode()
        )

        self.mock_sendall.reset_mock()
        client.gauge("low.rate", 128, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

        self.assertRaises(AssertionError, client.gauge, "negative", -5)

    def test_gauge_delta(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory!", 128)
        self.mock_sendall.assert_called_with("memory:+128|g\n".encode())

        client.prefix = "region."
        client.gauge_delta("cpu percentage%", rate=0.9, delta=-12)
        self.mock_sendall.assert_called_with(
            "region.cpu_percentage:-12|g|@0.9\n".encode()
        )

        self.mock_sendall.reset_mock()
        client.gauge_delta("low.rate", 10, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

    def test_set(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.set("ip address", "10.10.10.1")
        self.mock_sendall.assert_called_with(
            "ip_address:10.10.10.1|s\n".encode()
        )

        client.prefix = "region."
        client.set("~username*", rate=0.9, value='first')
        self.mock_sendall.assert_called_with(
            "region.username:first|s|@0.9\n".encode()
        )

        self.mock_sendall.reset_mock()
        client.set("low.rate", 256, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

    def test_when_client_is_removed_the_socket_batch_client_socket_is_not_closed(self):
        client = self.clientClass("localhost")
        batch_client = client.batch_client()
        sock = batch_client._socket
        del client
        self.assertFalse(sock.closed)
        del batch_client
        self.assertTrue(sock.closed)


class TestTCPBatchClient(BatchClientTestCaseMixIn, unittest.TestCase):

    def setUp(self):
        super(TestTCPBatchClient, self).setUp()
        self.clientClass = TCPBatchClient

    def test_increment(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.increment("event", 2, 0.5)
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("event:2|c|@0.5\n".encode()),
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.increment("login")
        client.increment("login.fail", 5, 0.2)
        client.increment("login.ok", rate=0.8)
        client.flush()
        self.mock_sendall.assert_called_once_with(
            bytearray("pre.login:1|c\npre.login.ok:1|c|@0.8\n".encode())
        )

    def test_decrement(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.decrement("event", 3, 0.7)
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("event:-3|c|@0.7\n".encode())
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.decrement("session")
        client.decrement("session.fail", 2, 0.2)
        client.decrement("session.ok", rate=0.6)
        client.flush()

        self.mock_sendall.assert_called_once_with(
            bytearray("pre.session:-1|c\npre.session.ok:-1|c|@0.6\n".encode())
        )

    def test_timing(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10, 0.4)
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("event:10|ms|@0.4\n".encode())
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.timing("query", 3)
        client.timing("process.request", 2, 0.2)
        client.timing("query.user", 350, rate=0.6)
        client.flush()

        self.mock_sendall.assert_called_once_with(
            bytearray("pre.query:3|ms\npre.query.user:350|ms|@0.6\n".encode())
        )

    def test_gauge(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("memory:10240|g\n".encode())
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.gauge("memory", 2048)
        client.gauge("memory", 8096, 0.2)
        client.gauge("storage", 512, rate=0.6)
        client.flush()

        self.mock_sendall.assert_called_once_with(
            bytearray("pre.memory:2048|g\npre.storage:512|g|@0.6\n".encode())
        )

    def test_gauge_delta(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory", -512)
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("memory:-512|g\n".encode())
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.gauge_delta("memory", 2048)
        client.gauge_delta("memory", 8096, 0.2)
        client.gauge_delta("storage", -128, rate=0.7)
        client.flush()

        self.mock_sendall.assert_called_once_with(
            bytearray("pre.memory:+2048|g\npre.storage:-128|g|@0.7\n".encode())
        )

    def test_set(self):
        client = TCPBatchClient("localhost")
        client._socket = self.mock_socket
        client.set("username", 'first')
        client.flush()
        self.mock_sendall.assert_called_with(
            bytearray("username:first|s\n".encode())
        )
        self.mock_sendall.reset_mock()
        client.prefix = "pre."
        client.set("user", 'second')
        client.set("user", 'third', 0.2)
        client.set("user", 'last', rate=0.5)
        client.flush()

        self.mock_sendall.assert_called_once_with(
            bytearray("pre.user:second|s\npre.user:last|s|@0.5\n".encode())
        )

    def test_metrics_partitioned_into_batches(self):
        client = TCPBatchClient("localhost", batch_size=20)
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
                mock.call(bytearray("fit.a.batch.123:1|c\n".encode())),
                mock.call(bytearray("_:1|ms\n".encode())),
                mock.call(bytearray("larger.than.batch.becomes.a.batch:5|c|@0.9\n".encode())),
                mock.call(bytearray("12:-1|c\nab:z|s\n".encode())),
                mock.call(bytearray("small:9|ms\n".encode())),
                mock.call(bytearray("overflow.previous:10|g\n".encode())),
                mock.call(bytearray("next:-10|g\n_:1|c\n".encode()))
        ]
        self.assertEqual(self.mock_sendall.mock_calls, expected_calls)

    def test_clear(self):
        client = TCPBatchClient("localhost", batch_size=20)
        client._socket = self.mock_socket
        client.increment("first")
        client.decrement("second")
        client.timing("db.query", 1)
        client.clear()
        client.flush()
        self.assertEqual(self.mock_sendall.call_count, 0)

if __name__ == "__main__":
    unittest.main()