"""
tests
-----
statsdmetrics unit tests
"""
import sys
from os.path import dirname
import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

project_dir = dirname(dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from statsdmetrics.client import Client, DEFAULT_PORT


class MockMixIn(object):
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

    def test_port_number_should_be_valid(self):
        self.assertRaises(AssertionError, self.clientClass, "host", -1)
        self.assertRaises(AssertionError, self.clientClass, "host", 0)
        self.assertRaises(AssertionError, self.clientClass, "host", 65536)

    def test_host_is_readonly(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.host = "example.org"

    def test_port_is_readonly(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.port = 8888

    def test_remote_address_is_readonly(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.remote_address = ("10.10.10.1", 8125)


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

    def test_batch_size_should_be_positive_int(self):
        self.assertRaises(
            ValueError, self.clientClass, "localhost", batch_size="not number")
        self.assertRaises(
            AssertionError, self.clientClass, "localhost", batch_size=-1)

    def test_batch_size_is_read_only(self):
        client = self.clientClass("localhost")
        with self.assertRaises(AttributeError):
            client.batch_size = 512


class BaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        if not hasattr(self, 'assertRegex'):
            self.assertRegex = self.assertRegexpMatches
