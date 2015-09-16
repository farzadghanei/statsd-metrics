"""
tests.test_metrics
------------------
unit tests for module functions metric classes.
"""

import unittest
from statsd_metrics import (Counter, Timer,
                            Gauge, Set, GaugeDelta,
                            normalize_metric_name)


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


class TestCounter(unittest.TestCase):
    def test_counter_constructor(self):
        counter = Counter('test', 5, 0.2)
        self.assertEqual(counter.name, 'test')
        self.assertEqual(counter.count, 5)
        self.assertEqual(counter.sample_rate, 0.2)

        counter_negative = Counter('negative', -10)
        self.assertEqual(counter_negative.count, -10)

    def test_metric_requires_a_non_empty_string_name(self):
        self.assertRaises(AssertionError, Counter, 0)
        self.assertRaises(AssertionError, Counter, '')

    def test_counter_default_count_is_zero(self):
        counter = Counter('test')
        self.assertEqual(counter.count, 0)

    def test_counter_default_sample_rate_is_one(self):
        counter = Counter('test')
        self.assertEqual(counter.sample_rate, 1)

    def test_count_should_be_integer(self):
        self.assertRaises(AssertionError, Counter, 'test', 1.2)
        counter = Counter('ok')

        def set_string_as_count():
            counter.count = 'not integer'

        self.assertRaises(AssertionError, set_string_as_count)
        counter.count = 2
        self.assertEqual(counter.count, 2)

    def test_sample_rate_should_be_numeric(self):
        self.assertRaises(AssertionError, Counter, 'string_sample_rate', 1, 'what?')
        counter = Counter('ok')
        counter.sample_rate = 0.4
        self.assertEqual(counter.sample_rate, 0.4)
        counter.sample_rate = 2
        self.assertEqual(counter.sample_rate, 2)

    def test_sample_rate_should_be_positive(self):
        self.assertRaises(AssertionError, Counter, 'negative', 1, -2.3)
        self.assertRaises(AssertionError, Counter, 'zero', 1, 0)

    def test_to_request(self):
        counter = Counter('something')
        self.assertEqual(counter.to_request(), 'something:0|c')

        counter2 = Counter('another', 3)
        self.assertEqual(counter2.to_request(), 'another:3|c')

        counter3 = Counter('again', -2, 0.7)
        self.assertEqual(counter3.to_request(), 'again:-2|c|@0.7')


class TestTimer(unittest.TestCase):
    def test_constructor(self):
        timer = Timer('test', 5.1, 0.2)
        self.assertEqual(timer.name, 'test')
        self.assertEqual(timer.milliseconds, 5.1)
        self.assertEqual(timer.sample_rate, 0.2)

    def test_metric_requires_a_non_empty_string_name(self):
        self.assertRaises(AssertionError, Timer, 0, 0.1)
        self.assertRaises(AssertionError, Timer, '', 0.1)

    def test_default_sample_rate_is_one(self):
        timer = Timer('test', 0.1)
        self.assertEqual(timer.sample_rate, 1)

    def test_millisecond_should_be_numeric(self):
        self.assertRaises(AssertionError, Timer, 'test', '')
        timer = Timer('ok', 0.3)
        self.assertEqual(timer.milliseconds, 0.3)
        timer.milliseconds = 2
        self.assertEqual(timer.milliseconds, 2)

    def test_millisecond_should_not_be_negative(self):
        self.assertRaises(AssertionError, Timer, 'test', -4.2)
        timer = Timer('ok', 0.0)
        self.assertEqual(timer.milliseconds, 0.0)

    def test_sample_rate_should_be_numeric(self):
        self.assertRaises(AssertionError, Timer, 'string_sample_rate', 1.0, 's')
        timer = Timer('ok', 0.1)
        timer.sample_rate = 0.3
        self.assertEqual(timer.sample_rate, 0.3)
        timer.sample_rate = 2
        self.assertEqual(timer.sample_rate, 2)

    def test_sample_rate_should_be_positive(self):
        self.assertRaises(AssertionError, Timer, 'negative', 1.2, -4.0)
        self.assertRaises(AssertionError, Timer, 'zero', 1.2, 0)

    def test_to_request(self):
        timer = Timer('ok', 0.2)
        self.assertEqual(timer.to_request(), 'ok:0.2|ms')

        timer2 = Timer('another', 45.2)
        self.assertEqual(timer2.to_request(), 'another:45.2|ms')

        timer3 = Timer('again', 12.3, 0.8)
        self.assertEqual(timer3.to_request(), 'again:12.3|ms|@0.8')


class TestGauge(unittest.TestCase):
    def test_constructor(self):
        gauge = Gauge('test', 5, 0.2)
        self.assertEqual(gauge.name, 'test')
        self.assertEqual(gauge.value, 5)
        self.assertEqual(gauge.sample_rate, 0.2)

    def test_metric_requires_a_non_empty_string_name(self):
        self.assertRaises(AssertionError, Gauge, 0, 1)
        self.assertRaises(AssertionError, Gauge, '', 2)

    def test_default_sample_rate_is_one(self):
        gauge = Gauge('test', 3)
        self.assertEqual(gauge.sample_rate, 1)

    def test_value_should_be_numeric(self):
        self.assertRaises(AssertionError, Gauge, 'string_val', '')
        gauge = Gauge('ok', 0.3)

        def set_value_as_string():
            gauge.value = 'not float'

        self.assertRaises(AssertionError, set_value_as_string)
        gauge.value = 2.0
        self.assertEqual(gauge.value, 2.0)
        gauge.value = 63
        self.assertEqual(gauge.value, 63)

    def test_value_should_not_be_negative(self):
        self.assertRaises(AssertionError, Gauge, 'test', -2)
        gauge = Gauge('ok', 0)

        def set_negative_value():
            gauge.value = -4.5

        self.assertRaises(AssertionError, set_negative_value)

    def test_sample_rate_should_be_numeric(self):
        self.assertRaises(AssertionError, Gauge, 'string_sample_rate', 1.0, 's')
        gauge = Gauge('ok', 4)
        gauge.sample_rate = 0.3
        self.assertEqual(gauge.sample_rate, 0.3)
        gauge.sample_rate = 2
        self.assertEqual(gauge.sample_rate, 2)

    def test_sample_rate_should_be_positive(self):
        self.assertRaises(AssertionError, Gauge, 'negative', 10, -4.0)
        self.assertRaises(AssertionError, Gauge, 'zero', 10, 0)

    def test_to_request(self):
        gauge = Gauge('ok', 0.2)
        self.assertEqual(gauge.to_request(), 'ok:0.2|g')

        gauge2 = Gauge('another', 237)
        self.assertEqual(gauge2.to_request(), 'another:237|g')

        gauge3 = Gauge('again', 11.8, 0.4)
        self.assertEqual(gauge3.to_request(), 'again:11.8|g|@0.4')


class TestSet(unittest.TestCase):
    def test_constructor(self):
        set_ = Set('unique', 5)
        self.assertEqual(set_.name, 'unique')
        self.assertEqual(set_.value, 5)

    def test_metric_requires_a_non_empty_string_name(self):
        self.assertRaises(AssertionError, Set, 0, 1)
        self.assertRaises(AssertionError, Set, '', 2)

    def test_value_should_be_hashable(self):
        self.assertRaises(AssertionError, Set, 'not_hashable', [])
        set_ = Set('ok', 4)
        set_.value = 2.0
        self.assertEqual(set_.value, 2.0)
        set_.value = 'something hashable'
        self.assertEqual(set_.value, 'something hashable')


class TestGaugeDelta(unittest.TestCase):
    def test_constructor(self):
        gauge_delta = GaugeDelta('unique', 5)
        self.assertEqual(gauge_delta.name, 'unique')
        self.assertEqual(gauge_delta.delta, 5)

    def test_delta_should_be_numeric(self):
        self.assertRaises(AssertionError, GaugeDelta, 'string_val', '')
        gauge_delta = GaugeDelta('ok', 0.3)
        gauge_delta.delta = 2.0
        self.assertEqual(gauge_delta.delta, 2.0)
        gauge_delta.delta = 27
        self.assertEqual(gauge_delta.delta, 27)

    def test_to_request(self):
        gauge_delta = GaugeDelta('ok', 0.2)
        self.assertEqual(gauge_delta.to_request(), 'ok:+0.2|g')

        gauge_delta2 = GaugeDelta('another', -43)
        self.assertEqual(gauge_delta2.to_request(), 'another:-43|g')

        gauge_delta3 = GaugeDelta('again', 15, 0.4)
        self.assertEqual(gauge_delta3.to_request(), 'again:+15|g|@0.4')

if __name__ == '__main__':
    unittest.main()
