"""
statsd_metrics.metrics
----------------------
Define metrics classes
"""

from re import compile, sub
from types import StringTypes, IntType, FloatType

normalize_metric_names_regexes = (
    (compile("\s+"), "_"),
    (compile("[\/\\\\]"), "-"),
    (compile("[^\w.-]"), ""),
)

def normalize_metric_name(name):
    for regex, replacement in normalize_metric_names_regexes:
        name = sub(regex, replacement, name)
    return name

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

    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        assert type(value) is FloatType, 'Metric sample rate should be float'
        assert value > 0, 'Metric sample rate should be positive'
        self._sample_rate = value

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

    def to_request(self):
        result = "{0}:{1}|c".format(self._name, self._count)
        if self._sample_rate != 1.0:
            result += "@{:.1}".format(self._sample_rate)
        return result

class Timer(AbstractMetric):
    def __init__(self, name, milliseconds, sample_rate=1.0):
        super(Timer, self).__init__(name)
        self.milliseconds = milliseconds
        self.sample_rate = sample_rate

    @property
    def milliseconds(self):
        return self._milliseconds

    @milliseconds.setter
    def milliseconds(self, milliseconds):
        assert type(milliseconds) is FloatType, 'Timer milliseconds should be float'
        assert milliseconds >= 0, 'Timer milliseconds should not be negative'
        self._milliseconds = milliseconds

__all__ = (normalize_metric_name, Counter,)