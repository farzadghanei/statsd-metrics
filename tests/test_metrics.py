"""
tests.test_metrics
------------------
unit tests for module functions metric classes.
"""

import unittest

from statsdmetrics import (Counter, Timer,
                           Gauge, Set, GaugeDelta,
                           normalize_metric_name,
                           parse_metric_from_request
                           )


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

    def test_normalize_names_removes_none_alphanumeric_dashes(self):
        self.assertEqual(
            "namewithinvalidcharsandall",
            normalize_metric_name("#+name?with~invalid!chars(and)all*&")
        )

    def test_parse_metric_from_request_requires_string(self):
        self.assertRaises(AssertionError, parse_metric_from_request, 10)
        self.assertRaises(AssertionError, parse_metric_from_request, 2.2)

    def test_parse_counter_metric_from_request(self):
        self.assertEqual(
            Counter("sales", 10),
            parse_metric_from_request("sales:10|c")
        )
        self.assertEqual(
            Counter("with rate?", 0, 1),
            parse_metric_from_request("with rate?:0|c|@1")
        )
        self.assertEqual(
            Counter("accounts.active.disable", 4567, 1.0),
            parse_metric_from_request("accounts.active.disable:4567|c|@1.0")
        )
        self.assertEqual(
            Counter("float_rate", 345, 0.2),
            parse_metric_from_request("float_rate:345|c|@0.2")
        )

    def test_parse_counter_metric_from_invalid_request_raises_error(self):
        self.assertRaises(ValueError, parse_metric_from_request, "")
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "invalid_request"
        )
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "invalid request"
        )
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "bad_value_separator|2|c"
        )
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "missing_value:"
        )
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "no type:2"
        )
        self.assertRaises(
            ValueError, parse_metric_from_request, "missing_type:2|")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_type:2|X")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_rate:2|c@hello")
        self.assertRaises(
            ValueError, parse_metric_from_request, "float_counter:2.2|c@1")

    def test_parse_timer_metric_from_request(self):
        self.assertEqual(
            Timer("exact", 1),
            parse_metric_from_request("exact:1|ms")
        )
        self.assertEqual(
            Timer("db query?", 2.4),
            parse_metric_from_request("db query?:2.4|ms")
        )
        self.assertEqual(
            Timer("db.query.with.rate", 10, 1),
            parse_metric_from_request("db.query.with.rate:10|ms|@1")
        )
        self.assertEqual(
            Timer("db_query_float_rate", 23.5, 0.5),
            parse_metric_from_request("db_query_float_rate:23.5|ms|@0.5")
        )

    def test_parse_timer_metric_from_invalid_request_raises_value_error(self):
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_value:hello|ms")
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "invalid_value:hello|ms|@0.5"
        )
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_type:4|ms_")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_rate:4.2|ms@_")

    def test_parse_gauge_metric_from_request(self):
        self.assertEqual(
            Gauge("cpu_usage", 45.3),
            parse_metric_from_request("cpu_usage:45.3|g")
        )
        self.assertEqual(
            Gauge("mem usage?", 10240, 1),
            parse_metric_from_request("mem usage?:10240|g|@1")
        )
        self.assertEqual(
            Gauge("weird.gauge.with.rate", 23.3, 0.5),
            parse_metric_from_request("weird.gauge.with.rate:23.3|g|@0.5")
        )

    def test_parse_gauge_metric_from_invalid_request_raises_value_error(self):
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_value:hello|g")
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "invalid_value:hello|g|@0.5"
        )
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_type:4|g_")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_rate:2.8|g@_")

    def test_parse_set_metric_from_request(self):
        self.assertEqual(
            Set("host", '127.0.0.1'),
            parse_metric_from_request("host:127.0.0.1|s")
        )
        self.assertEqual(
            Set("user id?", '12345', 1),
            parse_metric_from_request("user id?:12345|s|@1")
        )
        self.assertEqual(
            Set("weird.set.with.rate", '25.7', 0.5),
            parse_metric_from_request("weird.set.with.rate:25.7|s|@0.5")
        )

    def test_parse_set_metric_from_invalid_request_raises_value_error(self):
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_type:4|s_")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_rate:name|s@_")

    def test_parse_gauge_delta_metric_from_request(self):
        self.assertEqual(
            GaugeDelta("cpu_usage", 6),
            parse_metric_from_request("cpu_usage:+6|g")
        )
        self.assertEqual(
            GaugeDelta("mem usage?", -2048, 1),
            parse_metric_from_request("mem usage?:-2048|g|@1")
        )
        self.assertEqual(
            GaugeDelta("weird.gauge.delta.with.rate", 23.3, 0.5),
            parse_metric_from_request(
                "weird.gauge.delta.with.rate:+23.3|g|@0.5")
        )

    def test_parse_gauge_delta_metric_from_invalid_request_raises_error(self):
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_value:+hello|g")
        self.assertRaises(
            ValueError,
            parse_metric_from_request,
            "invalid_value:-hello|g|@0.5"
        )
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_type:+4|g_")
        self.assertRaises(
            ValueError, parse_metric_from_request, "invalid_rate:-2.8|g@_")


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
        self.assertRaises(
            AssertionError, Counter, 'string_sample_rate', 1, 'what?')
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

    def test_equality_check(self):
        counter = Counter('counter1')
        with self.assertRaises(AssertionError):
            counter != 'I am not a Counter'

        different_name = Counter('counter2')
        self.assertTrue(counter != different_name)

        different_count = Counter('counter1', 10)
        self.assertTrue(counter != different_count)

        different_rate = Counter('counter1', 1, 0.5)
        self.assertTrue(counter != different_rate)

        same = Counter('counter1')
        self.assertTrue(same == counter)


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
        self.assertRaises(
            AssertionError, Timer, 'string_sample_rate', 1.0, 's')
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

    def test_equality_check(self):
        timer = Timer('timer1', 10)
        with self.assertRaises(AssertionError):
            timer != 'I am not a Timer'

        different_name = Timer('timer2', 10)
        self.assertTrue(timer != different_name)

        different_time = Timer('timer1', 25)
        self.assertTrue(timer != different_time)

        different_rate = Timer('timer1', 10, 0.5)
        self.assertTrue(timer != different_rate)

        same = Timer('timer1', 10)
        self.assertTrue(same == timer)


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
        self.assertRaises(
            AssertionError, Gauge, 'string_sample_rate', 1.0, 's')
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

    def test_equality_check(self):
        gauge = Gauge('cpu', 10)
        with self.assertRaises(AssertionError):
            gauge != 'I am not a Gauge'

        different_name = Gauge('memory', 10)
        self.assertTrue(gauge != different_name)

        different_value = Gauge('cpu', 25)
        self.assertTrue(gauge != different_value)

        different_rate = Gauge('cpu', 10, 0.5)
        self.assertTrue(gauge != different_rate)

        same = Gauge('cpu', 10)
        self.assertTrue(same == gauge)


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

    def test_equality_check(self):
        metric = Set('uid', 5)
        with self.assertRaises(AssertionError):
            metric != 'I am not a Set'

        different_name = Set('userid', 5)
        self.assertTrue(metric != different_name)

        different_value = Set('uid', 25)
        self.assertTrue(metric != different_value)

        different_rate = Set('uid', 10, 0.5)
        self.assertTrue(metric != different_rate)

        same = Set('uid', 5)
        self.assertTrue(same == metric)


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

    def test_equality_check(self):
        metric = GaugeDelta('cpu', 5)
        with self.assertRaises(AssertionError):
            metric != 'I am not a GaugeDelta'

        different_name = GaugeDelta('memory', 5)
        self.assertTrue(metric != different_name)

        different_value = GaugeDelta('cpu', 25)
        self.assertTrue(metric != different_value)

        different_rate = GaugeDelta('cpu', 5, 0.5)
        self.assertTrue(metric != different_rate)

        same = GaugeDelta('cpu', 5)
        self.assertTrue(same == metric)

if __name__ == '__main__':
    unittest.main()