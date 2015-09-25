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

from statsdmetrics.client import Client, BatchClient, DEFAULT_PORT


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

        with client.batch_client(2048) as batch_client:
            self.assertEqual(batch_client.batch_size, 2048)


class TestBatchClient(ClientTestCaseMixIn, unittest.TestCase):
    def setUp(self):
        super(TestBatchClient, self).setUp()
        self.clientClass = BatchClient

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

    def test_batch_size_should_be_int(self):
        self.assertRaises(
            ValueError, BatchClient, "localhost", batch_size="not number")
        self.assertRaises(
            AssertionError, BatchClient, "localhost", batch_size=-1)

    def test_batch_size_is_read_only(self):
        client = BatchClient("localhost")
        with self.assertRaises(AttributeError):
            client.batch_size = 512

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
        client.increment("login")
        client.increment("login.fail", 5, 0.2)
        client.increment("login.ok", rate=0.8)
        client.flush()
        self.mock_sendto.assert_called_once_with(
            bytearray("login:1|c\nlogin.ok:1|c|@0.8\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_increment_multi_batch(self):
        client = BatchClient("localhost", batch_size=10)
        client._socket = self.mock_socket
        client.increment("12345")
        client.increment("larger.than.batch.becomes.a.batch")
        client.increment("123")
        client.flush()
        expected_calls = [
                mock.call(bytearray("12345:1|c\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("larger.than.batch.becomes.a.batch:1|c\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("123:1|c\n".encode()), ("127.0.0.2", 8125)),
        ]
        self.assertEqual(self.mock_sendto.mock_calls, expected_calls)

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

        client.decrement("session")
        client.decrement("session.fail", 2, 0.2)
        client.decrement("session.ok", rate=0.6)
        client.flush()

        self.mock_sendto.assert_called_once_with(
            bytearray("session:-1|c\nsession.ok:-1|c|@0.6\n".encode()),
            ("127.0.0.2", 8125)
        )

    def test_decrement_multi_batch(self):
        client = BatchClient("localhost", batch_size=10)
        client._socket = self.mock_socket
        client.decrement("1234")
        client.decrement("larger.than.batch.becomes.a.batch")
        client.decrement("123")
        client.flush()
        expected_calls = [
                mock.call(bytearray("1234:-1|c\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("larger.than.batch.becomes.a.batch:-1|c\n".encode()), ("127.0.0.2", 8125)),
                mock.call(bytearray("123:-1|c\n".encode()), ("127.0.0.2", 8125)),
        ]
        self.assertEqual(self.mock_sendto.mock_calls, expected_calls)

if __name__ == "__main__":
    unittest.main()
