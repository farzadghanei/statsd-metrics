"""
statsd_metrics.metrics
----------------------
Define metric classes
"""

from re import compile, sub

try:
    unicode('')
except NameError:
    unicode = str

try:
    long(1)
except NameError:
    long = int


def is_string(value):
    return isinstance(value, str) or\
           isinstance(value, unicode)


def is_numeric(value):
    return isinstance(value, int) or\
           isinstance(value, float) or\
           isinstance(value, long)

normalize_metric_name_regexes = (
    (compile("\s+"), "_"),
    (compile("[\/\\\\]"), "-"),
    (compile("[^\w.-]"), ""),
)


def normalize_metric_name(name):
    for regex, replacement in normalize_metric_name_regexes:
        name = sub(regex, replacement, name)
    return name


class AbstractMetric(object):
    def __init__(self, name):
        self._name = ''
        self._sample_rate = 1
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        assert is_string(name),\
            'Metric name should be string'
        assert name != '',\
            'Metric name should not be empty'
        self._name = name

    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        assert is_numeric(value),\
            'Metric sample rate should be numeric'
        assert value > 0,\
            'Metric sample rate should be positive'
        self._sample_rate = value


class Counter(AbstractMetric):
    def __init__(self, name, count=0, sample_rate=1):
        super(Counter, self).__init__(name)
        self._count = 0
        self.count = count
        self.sample_rate = sample_rate

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        assert isinstance(count, int),\
            'Counter count should be integer'
        self._count = count

    def to_request(self):
        result = "{0}:{1}|c".format(self._name, self._count)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result


class Timer(AbstractMetric):
    def __init__(self, name, milliseconds, sample_rate=1):
        super(Timer, self).__init__(name)
        self._milliseconds = 0
        self.milliseconds = milliseconds
        self.sample_rate = sample_rate

    @property
    def milliseconds(self):
        return self._milliseconds

    @milliseconds.setter
    def milliseconds(self, milliseconds):
        assert is_numeric(milliseconds),\
            'Timer milliseconds should be numeric'
        assert milliseconds >= 0,\
            'Timer milliseconds should not be negative'
        self._milliseconds = milliseconds

    def to_request(self):
        result = "{0}:{1}|ms".format(self._name, self._milliseconds)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result


class Gauge(AbstractMetric):
    def __init__(self, name, value, sample_rate=1):
        self._value = 0
        super(Gauge, self).__init__(name)
        self.value = value
        self.sample_rate = sample_rate

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        assert is_numeric(value),\
            'Gauge value should be numeric'
        assert value >= 0,\
            'Gauge value should not be negative'
        self._value = value

    def to_request(self):
        result = "{0}:{1}|g".format(self._name, self._value)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result


class Set(AbstractMetric):
    def __init__(self, name, value):
        self._value = 0
        super(Set, self).__init__(name)
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            str(value)
        except (TypeError, ValueError):
            raise AssertionError("Set value should be convertible to string")
        try:
            hash(value)
        except (TypeError, ValueError):
            raise AssertionError("Set value should be hashable")
        self._value = value

    def to_request(self):
        result = "{0}:{1}|s".format(self._name, self._value)
        if self._sample_rate != 1:
                result += "|@{:n}".format(self._sample_rate)
        return result


class GaugeDelta(AbstractMetric):
    def __init__(self, name, delta, sample_rate=1):
        self._delta = 0
        super(GaugeDelta, self).__init__(name)
        self.delta = delta
        self.sample_rate = sample_rate

    @property
    def delta(self):
        return self._delta

    @delta.setter
    def delta(self, delta):
        assert is_numeric(delta),\
            'Gauge delta should be numeric'
        self._delta = delta

    def to_request(self):
        result = "{}:{:+n}|g".format(self._name, self._delta)
        if self._sample_rate != 1:
                result += "|@{:n}".format(self._sample_rate)
        return result

__all__ = (Counter, Timer, Gauge,
           Set, GaugeDelta,
           normalize_metric_name)
