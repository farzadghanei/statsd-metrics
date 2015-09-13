"""
tests.test_metrics_counter
--------------------------
"""

import unittest
from statsd_metrics import Counter

class MetricsCounterCase(unittest.TestCase):
    def test_counter_default_balance_is_zero(self):
        counter = Counter()
        self.assertEquals(counter.balance, 0)

    def test_counter_default_sample_rate_is_one(self):
        counter = Counter()
        self.assertEquals(counter.sample_rate, 1)

    def test_counter_constructor(self):
        counter = Counter(5, 0.2)
        self.assertEquals(counter.balance, 5)
        self.assertEquals(counter.sample_rate, 0.2)

        counter_negative = Counter(-10)
        self.assertEquals(counter_negative.balance, -10)

    def test_balance_should_be_integer(self):
        self.assertRaises(AssertionError, Counter, 1.2)

    def test_sample_rate_should_be_float(self):
        self.assertRaises(ValueError, Counter, 1, 's')

    def test_sample_rate_should_be_positive(self):
        self.assertRaises(AssertionError, Counter, 1, -4)

if __name__ == '__main__':
    unittest.main()
