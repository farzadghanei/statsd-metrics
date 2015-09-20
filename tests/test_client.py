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

from statsdmetrics.client import Client, DEFAULT_PORT


class TestClient(unittest.TestCase):
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

    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_remote_address_updates_when_host_is_updated(self, mock_gethost):
        host1 = "localhost"
        host2 = "example.org"
        client = Client(host1)
        mock_gethost.return_value = "127.0.0.2"
        address1 = client.remote_address
        mock_gethost.assert_called_with(host1)
        self.assertEqual(address1, ("127.0.0.2", 8125))

        client.host = host2
        mock_gethost.return_value = "10.10.10.1"
        address2 = client.remote_address
        mock_gethost.assert_called_with(host2)
        self.assertEqual(address2, ("10.10.10.1", 8125))

    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_remote_address_updates_when_port_is_updated(self, mock_gethost):
        port1 = 8125
        port2 = 1024
        client = Client("localhost", port1)
        mock_gethost.return_value = "127.0.0.2"
        self.assertEqual(client.remote_address, ("127.0.0.2", port1))
        client.port = port2
        self.assertEqual(client.remote_address, ("127.0.0.2", port2))

    @mock.patch('statsdmetrics.client.random')
    @mock.patch('statsdmetrics.client.socket.socket')
    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_increment(self, mock_gethost, mock_socket, mock_random):
        mock_gethost.return_value = "127.0.0.2"
        mock_sendto = mock.MagicMock()
        mock_socket.sendto = mock_sendto
        mock_random.return_value = 0.3

        client = Client("localhost")
        client.socket = mock_socket
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

    @mock.patch('statsdmetrics.client.random')
    @mock.patch('statsdmetrics.client.socket.socket')
    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_decrement(self, mock_gethost, mock_socket, mock_random):
        mock_gethost.return_value = "10.10.10.1"
        mock_sendto = mock.MagicMock()
        mock_socket.sendto = mock_sendto
        mock_random.return_value = 0.3

        client = Client("localhost")
        client.socket = mock_socket
        client.decrement("event")
        mock_sendto.assert_called_with(
            "event:-1|c".encode(),
            ("10.10.10.1", 8125)
        )
        client.decrement("event2", 5)
        mock_sendto.assert_called_with(
            "event2:-5|c".encode(),
            ("10.10.10.1", 8125)
        )
        client.decrement("region.event name", 2, 0.5)
        mock_sendto.assert_called_with(
            "region.event_name:-2|c|@0.5".encode(),
            ("10.10.10.1", 8125)
        )

        client.prefix = "region.c_"
        client.port = 8000
        client.decrement("active!users", rate=0.7)
        mock_sendto.assert_called_with(
            "region.c_activeusers:-1|c|@0.7".encode(),
            ("10.10.10.1", 8000)
        )

        mock_sendto.reset_mock()
        client.decrement("low.rate", rate=0.1)
        self.assertEqual(mock_sendto.call_count, 0)

    @mock.patch('statsdmetrics.client.random')
    @mock.patch('statsdmetrics.client.socket.socket')
    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_timing(self, mock_gethost, mock_socket, mock_random):
        mock_gethost.return_value = "10.10.10.1"
        mock_sendto = mock.MagicMock()
        mock_socket.sendto = mock_sendto
        mock_random.return_value = 0.3

        client = Client("localhost")
        client.socket = mock_socket
        client.timing("event", 10)
        mock_sendto.assert_called_with(
            "event:10|ms".encode(),
            ("10.10.10.1", 8125)
        )
        client.timing("db.event name", 34.5, 0.5)
        mock_sendto.assert_called_with(
            "db.event_name:34.5|ms|@0.5".encode(),
            ("10.10.10.1", 8125)
        )

        client.prefix = "region.c_"
        client.port = 8000
        client.timing("db/query", rate=0.7, milliseconds=22.22)
        mock_sendto.assert_called_with(
            "region.c_db-query:22.22|ms|@0.7".encode(),
            ("10.10.10.1", 8000)
        )

        mock_sendto.reset_mock()
        client.timing("low.rate", 12, rate=0.1)
        self.assertEqual(mock_sendto.call_count, 0)


if __name__ == "__main__":
    unittest.main()
