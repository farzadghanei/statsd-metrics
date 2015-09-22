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


class BaseTestCase(unittest.TestCase):
    """MixIn class to patch socket module for tests"""

    def setUp(self):
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


class TestClient(BaseTestCase):

    def test_init_and_properties(self):
        default_client = Client("127.0.0.1")
        self.assertEqual(default_client.host, "127.0.0.1")
        self.assertEqual(default_client.port, DEFAULT_PORT)
        self.assertEqual(default_client.prefix, "")

        client = Client("stats.example.org", 8111, "region")
        self.assertEqual(client.host, "stats.example.org")
        self.assertEqual(client.port, 8111)
        self.assertEqual(client.prefix, "region")
        client.host = "stats.example.com"
        self.assertEqual(client.host, "stats.example.com")
        client.port = 8126
        self.assertEqual(client.port, 8126)

    def test_port_number_should_be_valid(self):
        self.assertRaises(AssertionError, Client, "host", -1)
        self.assertRaises(AssertionError, Client, "host", 0)
        self.assertRaises(AssertionError, Client, "host", 65536)

    def test_remote_address_is_readonly(self):
        client = Client("localhost")
        with self.assertRaises(AttributeError) as context:
            client.remote_address = ("10.10.10.1", 8125)

    def test_remote_address_updates_when_host_is_updated(self):
        host1 = "localhost"
        host2 = "example.org"
        client = Client(host1)
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
        client = Client("localhost", port1)
        self.assertEqual(client.remote_address, ("127.0.0.2", port1))
        client.port = port2
        self.assertEqual(client.remote_address, ("127.0.0.2", port2))

    def test_increment(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.increment("event")
        mock_sendto.assert_called_with(
            "event:1|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.increment("event2", 5)
        mock_sendto.assert_called_with(
            "event2:5|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.increment("region.event name", 2, 0.5)
        mock_sendto.assert_called_with(
            "region.event_name:2|c|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.port = 8000
        client.prefix = "region.c_"
        client.increment("@login#", rate=0.6)
        mock_sendto.assert_called_with(
            "region.c_login:1|c|@0.6".encode(),
            ("127.0.0.2", 8000)
        )

        mock_sendto.reset_mock()
        client.increment("low.rate", rate=0.1)
        self.assertEqual(mock_sendto.call_count, 0)

    def test_decrement(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.decrement("event")
        mock_sendto.assert_called_with(
            "event:-1|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.decrement("event2", 5)
        mock_sendto.assert_called_with(
            "event2:-5|c".encode(),
            ("127.0.0.2", 8125)
        )
        client.decrement("region.event name", 2, 0.5)
        mock_sendto.assert_called_with(
            "region.event_name:-2|c|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.port = 8000
        client.decrement("active!users", rate=0.7)
        mock_sendto.assert_called_with(
            "region.c_activeusers:-1|c|@0.7".encode(),
            ("127.0.0.2", 8000)
        )

        mock_sendto.reset_mock()
        client.decrement("low.rate", rate=0.1)
        self.assertEqual(mock_sendto.call_count, 0)

    def test_timing(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.timing("event", 10)
        mock_sendto.assert_called_with(
            "event:10|ms".encode(),
            ("127.0.0.2", 8125)
        )
        client.timing("db.event name", 34.5, 0.5)
        mock_sendto.assert_called_with(
            "db.event_name:34.5|ms|@0.5".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region.c_"
        client.port = 8000
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        mock_sendto.assert_called_with(
            "region.c_db-query:22.22|ms|@0.7".encode(),
            ("127.0.0.2", 8000)
        )

        mock_sendto.reset_mock()
        client.timing("low.rate", 12, rate=0.1)
        self.assertEqual(mock_sendto.call_count, 0)

        self.assertRaises(AssertionError, client.timing, "negative", -0.5)

    def test_gauge(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.gauge("memory", 10240)
        mock_sendto.assert_called_with(
            "memory:10240|g".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.port = 9000
        client.gauge("cpu percentage%", rate=0.9, value=98.3)
        mock_sendto.assert_called_with(
            "region.cpu_percentage:98.3|g|@0.9".encode(),
            ("127.0.0.2", 9000)
        )

        mock_sendto.reset_mock()
        client.gauge("low.rate", 128, 0.1)
        self.assertEqual(mock_sendto.call_count, 0)

        self.assertRaises(AssertionError, client.gauge, "negative", -5)

    def test_gauge_delta(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.gauge_delta("memory!", 128)
        mock_sendto.assert_called_with(
            "memory:+128|g".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.port = 9000
        client.gauge_delta("cpu percentage%", rate=0.9, delta=-12)
        mock_sendto.assert_called_with(
            "region.cpu_percentage:-12|g|@0.9".encode(),
            ("127.0.0.2", 9000)
        )

        mock_sendto.reset_mock()
        client.gauge_delta("low.rate", 10, 0.1)
        self.assertEqual(mock_sendto.call_count, 0)

    def test_set(self):
        mock_sendto = mock.MagicMock()
        self.mock_socket.sendto = mock_sendto

        client = Client("localhost")
        client._socket = self.mock_socket
        client.set("ip address", "10.10.10.1")
        mock_sendto.assert_called_with(
            "ip_address:10.10.10.1|s".encode(),
            ("127.0.0.2", 8125)
        )

        client.prefix = "region."
        client.port = 9000
        client.set("~username*", rate=0.9, value='first')
        mock_sendto.assert_called_with(
            "region.username:first|s|@0.9".encode(),
            ("127.0.0.2", 9000)
        )

        mock_sendto.reset_mock()
        client.set("low.rate", 256, 0.1)
        self.assertEqual(mock_sendto.call_count, 0)

    def test_context_manager_creates_batch_client(self):
        client = Client("localhost")
        client._socket = self.mock_socket

        with client.batch_client() as batch_client:
            self.assertIsInstance(batch_client, BatchClient)
            self.assertGreater(batch_client.batch_size, 0)
            self.assertEqual(batch_client.size, 0)
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


class TestBatchClient(BaseTestCase):

    def test_init_and_properties(self):
        default_client = BatchClient("127.0.0.1")
        self.assertEqual(default_client.host, "127.0.0.1")
        self.assertEqual(default_client.port, DEFAULT_PORT)
        self.assertEqual(default_client.prefix, "")
        self.assertEqual(default_client.size, 0)
        self.assertGreater(default_client.batch_size, 0)

        client = BatchClient("stats.example.org", 8111, "region", 1024)
        self.assertEqual(client.host, "stats.example.org")
        self.assertEqual(client.port, 8111)
        self.assertEqual(client.prefix, "region")
        self.assertEqual(client.batch_size, 1024)
        self.assertEqual(client.size, 0)

        client.host = "stats.example.com"
        self.assertEqual(client.host, "stats.example.com")
        client.port = 8126
        self.assertEqual(client.port, 8126)

    def test_batch_size_should_be_int(self):
        self.assertRaises(
            ValueError, BatchClient, "localhost", batch_size="not number")
        self.assertRaises(
            AssertionError, BatchClient, "localhost", batch_size=-1)

    def test_batch_size_and_size_are_read_only(self):
        client = BatchClient("localhost")

        with self.assertRaises(AttributeError) as context:
            client.size = 100

        with self.assertRaises(AttributeError) as context:
            client.batch_size = 512


if __name__ == "__main__":
    unittest.main()
