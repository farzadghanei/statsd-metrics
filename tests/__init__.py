"""
tests
-----
statsdmetrics unit tests
"""

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from statsdmetrics.client import Client, DEFAULT_PORT


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
