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

from statsdmetrics.client import (Client, BatchClient, TCPClient,
                                    TCPBatchClient, DEFAULT_PORT)


class MockMixIn():
    """Base test case to patch socket module for tests"""

    def doMock(self):
        patcher = mock.patch('statsdmetrics.client.socket.gethostbyname')
        self.mock_gethost = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_gethost.return_value = "127.0.0.2"

        patcher = mock.patch('statsdmetrics.client.random')
        self.mock_random = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_random.return_value = 0.3

        patcher = mock.patch('statsdmetrics.client.socket.socket')
        self.mock_socket = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = self.mock_sendto

        self.mock_sendall = mock.MagicMock()
        self.mock_socket.sendall = self.mock_sendall


class ClientTestCaseMixIn(MockMixIn):

    def setUp(self):
        self.doMock()
        self.clientClass = Client

    def test_init_and_properties(self):
        default_client = self.clientClass("127.0.0.1")
        self.assertEqual(default_client.host, "127.0.0.1")
        self.assertEqual(default_client.port, DEFAULT_PORT)
        self.assertEqual(default_client.prefix, "")

        client = self.clientClass("stats.example.org", 8111, "region")
        self.assertEqual(client.host, "stats.example.org")
        self.assertEqual(client.port, 8111)
        self.assertEqual(client.prefix, "region")
        client.host = "stats.example.com"
        self.assertEqual(client.host, "stats.example.com")
        client.port = 8126
        self.assertEqual(client.port, 8126)

    def test_port_number_should_be_valid(self):
        self.assertRaises(AssertionError, self.clientClass, "host", -1)
        self.assertRaises(AssertionError, self.clientClass, "host", 0)
        self.assertRaises(AssertionError, self.clientClass, "host", 65536)

    def test_remote_address_is_readonly(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.remote_address = ("10.10.10.1", 8125)

    def test_remote_address_updates_when_host_is_updated(self):
        host1 = "localhost"
        host2 = "example.org"
        client = self.clientClass(host1)
        address1 = client.remote_address
        self.mock_gethost.assert_called_with(host1)
        self.assertEqual(address1, ("127.0.0.2", 8125))

        client.host = host2
        self.mock_gethost.return_value = "10.10.10.1"
        address2 = client.remote_address
        self.mock_gethost.assert_called_with(host2)
        self.assertEqual(address2, ("10.10.10.1", 8125))

    def test_remote_address_updates_when_port_is_updated(self):
        port1 = 8125
        port2 = 1024
        client = self.clientClass("localhost", port1)
        self.assertEqual(client.remote_address, ("127.0.0.2", port1))
        client.port = port2
        self.assertEqual(client.remote_address, ("127.0.0.2", port2))

    def test_remote_address_is_not_affected_if_updated_address_is_same(self):
        host = "example.org"
        client = self.clientClass(host)
        address1 = client.remote_address
        self.mock_gethost.assert_called_with(host)
        self.assertEqual(address1, ("127.0.0.2", 8125))

        client.host = host
        address2 = client.remote_address
        self.assertEqual(address2, address1)
        self.assertEqual(self.mock_gethost.call_count, 1)

        client.port = 8125
        address3 = client.remote_address
        self.assertEqual(address3, address1)
        self.assertEqual(self.mock_gethost.call_count, 1)


class BatchClientTestCaseMixIn(ClientTestCaseMixIn):

    def test_init_and_properties(self):
        default_client = self.clientClass("127.0.0.1")
        self.assertEqual(default_client.host, "127.0.0.1")
        self.assertEqual(default_client.port, DEFAULT_PORT)
        self.assertEqual(default_client.prefix, "")
        self.assertGreater(default_client.batch_size, 0)

        client = self.clientClass("stats.example.org", 8111, "region", 1024)
        self.assertEqual(client.host, "stats.example.org")
        self.assertEqual(client.port, 8111)
        self.assertEqual(client.prefix, "region")
        self.assertEqual(client.batch_size, 1024)

        client.host = "stats.example.com"
        self.assertEqual(client.host, "stats.example.com")
        client.port = 8126
        self.assertEqual(client.port, 8126)

    def test_batch_size_should_be_positive_int(self):
        self.assertRaises(
            ValueError, self.clientClass, "localhost", batch_size="not number")
        self.assertRaises(
            AssertionError, self.clientClass, "localhost", batch_size=-1)

    def test_batch_size_is_read_only(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.batch_size = 512


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


class TestTCPClient(ClientTestCaseMixIn, unittest.TestCase):

    def setUp(self):
        super(TestTCPClient, self).setUp()
        self.clientClass = TCPClient

    def test_increment(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.increment("event")
        self.mock_sendall.assert_called_with("event:1|c".encode())
        client.increment("region.event name", 2, 0.5)
        self.mock_sendall.assert_called_with("region.event_name:2|c|@0.5".encode())

    def test_decrement(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.decrement("event")
        self.mock_sendall.assert_called_with(
            "event:-1|c".encode()
        )
        client.decrement("event2", 5)
        self.mock_sendall.assert_called_with(
            "event2:-5|c".encode()
        )
        client.decrement("region.event name", 2, 0.5)
        self.mock_sendall.assert_called_with(
            "region.event_name:-2|c|@0.5".encode()
        )

    def test_timing(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10)
        self.mock_sendall.assert_called_with(
            "event:10|ms".encode()
        )
        client.timing("db.event name", 34.5, 0.5)
        self.mock_sendall.assert_called_with(
            "db.event_name:34.5|ms|@0.5".encode(),
        )

        client.prefix = "region.c_"
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        self.mock_sendall.assert_called_with(
            "region.c_db-query:22.22|ms|@0.7".encode(),
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
            "memory:10240|g".encode()
        )

        client.prefix = "region."
        client.gauge("cpu percentage%", rate=0.9, value=98.3)
        self.mock_sendall.assert_called_with(
            "region.cpu_percentage:98.3|g|@0.9".encode()
        )

        self.mock_sendall.reset_mock()
        client.gauge("low.rate", 128, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

        self.assertRaises(AssertionError, client.gauge, "negative", -5)

    def test_gauge_delta(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory!", 128)
        self.mock_sendall.assert_called_with("memory:+128|g".encode())

        client.prefix = "region."
        client.gauge_delta("cpu percentage%", rate=0.9, delta=-12)
        self.mock_sendall.assert_called_with(
            "region.cpu_percentage:-12|g|@0.9".encode()
        )

        self.mock_sendall.reset_mock()
        client.gauge_delta("low.rate", 10, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)

    def test_set(self):
        client = self.clientClass("localhost")
        client._socket = self.mock_socket
        client.set("ip address", "10.10.10.1")
        self.mock_sendall.assert_called_with(
            "ip_address:10.10.10.1|s".encode()
        )

        client.prefix = "region."
        client.set("~username*", rate=0.9, value='first')
        self.mock_sendall.assert_called_with(
            "region.username:first|s|@0.9".encode()
        )

        self.mock_sendall.reset_mock()
        client.set("low.rate", 256, 0.1)
        self.assertEqual(self.mock_sendall.call_count, 0)


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
