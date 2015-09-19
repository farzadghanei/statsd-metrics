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

        client = Client("stats.example.org", 8111, "mystats")
        self.assertEqual(client.host, "stats.example.org")
        self.assertEqual(client.port, 8111)
        self.assertEqual(client.prefix, "mystats")
        client.host = "stats.example.com"
        self.assertEqual(client.host, "stats.example.com")
        client.port = 8126
        self.assertEqual(client.port, 8126)

    def test_port_number_should_be_valid(self):
        self.assertRaises(AssertionError, Client, "host", -1)
        self.assertRaises(AssertionError, Client, "host", 0)
        self.assertRaises(AssertionError, Client, "host", 65536)

    def test_remote_addr_is_readonly(self):
        client = Client("localhost")
        with self.assertRaises(AttributeError) as context:
            client.remote_addr = ("10.10.10.1", 8125)

    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_remote_addr_updates_when_host_is_updated(self, mock_gethost):
        host1 = "localhost"
        host2 = "example.org"
        client = Client(host1)
        mock_gethost.return_value = "127.0.0.2"
        addr1 = client.remote_addr
        mock_gethost.assert_called_with(host1)
        self.assertEqual(addr1, ("127.0.0.2", 8125))

        client.host = host2
        mock_gethost.return_value = "10.10.10.1"
        addr2 = client.remote_addr
        mock_gethost.assert_called_with(host2)
        self.assertEqual(addr2, ("10.10.10.1", 8125))

    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_remote_addr_updates_when_port_is_updated(self, mock_gethost):
        port1 = 8125
        port2 = 1024
        client = Client("localhost", port1)
        mock_gethost.return_value = "127.0.0.2"
        self.assertEqual(client.remote_addr, ("127.0.0.2", port1))
        client.port = port2
        self.assertEqual(client.remote_addr, ("127.0.0.2", port2))

    @mock.patch('statsdmetrics.client.socket.socket')
    @mock.patch('statsdmetrics.client.socket.gethostbyname')
    def test_increment_sends_metrics(self, mock_gethost, mock_socket):
        mock_gethost.return_value = "127.0.0.2"
        client = Client("localhost")
        client.socket = mock_socket
        mock_sendto = mock.MagicMock()
        mock_socket.sendto = mock_sendto
        client.increment("event")
        mock_sendto.assert_called_with(
            "event:1|c".encode(),
            ("127.0.0.2", 8125)
        )


if __name__ == "__main__":
    unittest.main()
