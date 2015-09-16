"""
tests.test_metrics
------------------
unit tests for module functions
"""

import unittest
from statsd_metrics import (Counter, normalize_metric_name)

class TestMetrics(unittest.TestCase):
    def test_normalize_metric_names_keeps_good_names(self):
        self.assertEqual(
            "metric.good.name",
            normalize_metric_name("metric.good.name")
        )

    def test_normalize_metric_names_replaces_spaces(self):
        self.assertEqual(
            "metric_name_with_spaces",
            normalize_metric_name("metric name with spaces")
        )

    def test_normalize_metric_names_replaces_slashes_and_backslashes(self):
        self.assertEqual(
            "metric-name-with-slashes",
            normalize_metric_name("metric/name\\with/slashes")
        )

    def test_normalize_metric_names_removes_none_alphanumeric_underscore_or_dashes(self):
        self.assertEqual(
            "namewithinvalidcharsandall",
            normalize_metric_name("#+name?with~invalid!chars(and)all*&")
        )

class CounterTestCase(unittest.TestCase):
    def test_metric_requires_a_non_empty_string_name(self):
        self.assertRaises(AssertionError, Counter, 0)
        self.assertRaises(AssertionError, Counter, '')

    def test_counter_default_count_is_zero(self):
        counter = Counter('test')
        self.assertEquals(counter.count, 0)

    def test_counter_default_sample_rate_is_one(self):
        counter = Counter('test')
        self.assertEquals(counter.sample_rate, 1.0)

    def test_counter_constructor(self):
        counter = Counter('test', 5, 0.2)
        self.assertEquals(counter.name, 'test')
        self.assertEquals(counter.count, 5)
        self.assertEquals(counter.sample_rate, 0.2)

        counter_negative = Counter('negative', -10)
        self.assertEquals(counter_negative.count, -10)

    def test_count_should_be_integer(self):
        self.assertRaises(AssertionError, Counter, 'test', 1.2)
        counter = Counter('ok')
        def set_string_as_count():
            counter.count = 'not integer'
        self.assertRaises(AssertionError, set_string_as_count)
        counter.count = 2
        self.assertEqual(counter.count, 2)

    def test_sample_rate_should_be_float(self):
        self.assertRaises(AssertionError, Counter, 'test', 1, 's')
        counter = Counter('ok')
        def set_int_as_sample_rate():
            counter.sample_rate = 7
        self.assertRaises(AssertionError, set_int_as_sample_rate)
        counter.sample_rate = 0.3
        self.assertEqual(counter.sample_rate, 0.3)

    def test_sample_rate_should_be_positive(self):
        self.assertRaises(AssertionError, Counter, 'test', 1, -4.0)

    def test_string_value(self):
        counter = Counter('something')
        self.assertEqual(counter.to_request(), 'something:0|c')

        counter2 = Counter('another', 3)
        self.assertEqual(counter2.to_request(), 'another:3|c')

        counter3 = Counter('again', -2, 0.7)
        self.assertEqual(counter3.to_request(), 'again:-2|c@0.7')

if __name__ == '__main__':
    unittest.main()
