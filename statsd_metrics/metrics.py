"""
statsd_metrics.metrics
----------------------
Define metrics classes
"""

from types import StringTypes, IntType, FloatType

class AbstractMetric(object):
    def __init__(self, name):
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        assert type(name) in StringTypes, 'Metric name should be string'
        assert name != '', 'Metric name should not be empty'
        self._name = name

class Counter(AbstractMetric):
    def __init__(self, name, count=0, sample_rate=1.0):
        super(Counter, self).__init__(name)
        self.count = count
        self.sample_rate = sample_rate

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        assert type(count) is IntType, 'Counter count should be integer'
        self._count = count

    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        assert type(value) is FloatType, 'Counter sample rate should be float'
        assert value > 0, 'Counter sample rate should be positive'
        self._sample_rate = value

    def to_request(self):
        result = "{0}:{1}|c".format(self._name, self._count)
        if self._sample_rate != 1.0:
            result += "@{:.1}".format(self._sample_rate)
        return result

__all__ = (Counter,)