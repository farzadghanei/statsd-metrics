"""
statsdmetrics.metrics
----------------------
Define metric classes
"""

from abc import ABCMeta, abstractmethod
from re import compile, sub
try:
    from typing import Any, Dict, Tuple, Union
    TypeMetric = Union['AbstractMetric', 'Counter', 'Timer', 'Gauge', 'GaugeDelta', 'Set']
except ImportError:
    Any, Dict, Tuple, Union = None, None, None, None  # type: ignore
    TypeMetric = None


try:
    unicode('')  # type: ignore
except NameError:
    unicode = str

try:
    long(1)  # type: ignore
except NameError:
    long = int


def is_string(value):
    # type: (Any) -> bool
    return isinstance(value, str) or \
           isinstance(value, unicode)


def is_numeric(value):
    # type: (Any) -> bool
    return isinstance(value, int) or \
           isinstance(value, float) or \
           isinstance(value, long)


normalize_metric_name_regex_subs = (
    (compile("\s+"), "_"),
    (compile("[\/\\\\]"), "-"),
    (compile("[^\w.-]"), ""),
)  # type: Tuple[Tuple[Any, str], Tuple[Any, str], Tuple[Any, str]]


def normalize_metric_name(name):
    # type: (unicode) -> unicode
    for regex, replacement in normalize_metric_name_regex_subs:
        name = sub(regex, replacement, name)
    return name


def parse_metric_from_request(request):
    # type: (unicode) -> TypeMetric
    assert is_string(request), \
        "Request should be string to parse a metric from"

    metric_type_classes = {'c': Counter, 'ms': Timer, 'g': Gauge, 's': Set}
    metric_value_types = {'c': int, 'ms': float, 'g': float}

    name, data = request.split(':')  # type: unicode, unicode
    value, _, type_section = data.partition('|')  # type: unicode, unicode, unicode
    type_, __, sample_rate_section = type_section.partition('|@')  # type: unicode, unicode, unicode

    if type_ not in metric_type_classes:
        raise ValueError(
            "Invalid request. Metric type '{}' is not supported".format(type_)
        )

    if type_ == 'g' and len(value) > 1 and value[0] in ('+', '-'):
        metric_class = GaugeDelta
    else:
        metric_class = metric_type_classes[type_]  # type: ignore

    value = metric_value_types[type_](value) \
        if type_ in metric_value_types else value  # type: ignore

    sample_rate = AbstractMetric.default_sample_rate \
        if sample_rate_section == '' else float(sample_rate_section)  # type: float

    return metric_class(name.strip(), value, sample_rate)


class AbstractMetric(object):
    __metaclass__ = ABCMeta

    default_sample_rate = 1  # type: float

    def __init__(self, name):  # type: (str) -> None
        self._name = ''  # type: unicode
        self._sample_rate = self.__class__.default_sample_rate  # type: ignore
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        # type: (unicode) -> None
        assert is_string(name), \
            'Metric name should be string'
        assert name != '', \
            'Metric name should not be empty'
        self._name = unicode(name)

    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        # type: (float) -> None
        assert is_numeric(value), \
            'Metric sample rate should be numeric: {}:{}'.format(
                self.name, value)
        assert value > 0, \
            'Metric sample rate should be positive: {}:{}'.format(
                self.name, value)
        self._sample_rate = value

    @abstractmethod
    def to_request(self):  # type: () -> bytes
        raise NotImplementedError()  # pragma: no cover


class Counter(AbstractMetric):
    def __init__(self, name, count=0, sample_rate=1):
        super(Counter, self).__init__(name)
        self._count = 0   # type: int
        self.count = count
        self.sample_rate = sample_rate

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        # type: (int) -> None
        assert isinstance(count, int), \
            'Counter count should be integer'
        self._count = count

    def to_request(self):
        # type: () -> bytes
        result = "{0}:{1}|c".format(self._name, self._count)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result

    def __eq__(self, other):
        assert isinstance(other, Counter), \
            'Counter can be compared to Counter only'
        return self.name == other.name \
               and self.count == other.count \
               and self.sample_rate == other.sample_rate

    def __ne__(self, other):
        assert isinstance(other, Counter), \
            'Counter can be compared to Counter only'
        return self.name != other.name \
               or self.count != other.count \
               or self.sample_rate != other.sample_rate


class Timer(AbstractMetric):
    def __init__(self, name, milliseconds, sample_rate=1):
        super(Timer, self).__init__(name)
        self._milliseconds = 0  # type: int
        self.milliseconds = milliseconds
        self.sample_rate = sample_rate

    @property
    def milliseconds(self):
        return self._milliseconds

    @milliseconds.setter
    def milliseconds(self, milliseconds):
        # type: (int) -> None
        assert is_numeric(milliseconds), \
            'Timer milliseconds should be numeric'
        assert milliseconds >= 0, \
            'Timer milliseconds should not be negative'
        self._milliseconds = milliseconds

    def to_request(self):
        # type: () -> bytes
        result = "{0}:{1}|ms".format(self._name, self._milliseconds)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result

    def __eq__(self, other):
        assert isinstance(other, Timer), \
            'Timer can be compared to Timer only'
        return self.name == other.name \
               and self.milliseconds == other.milliseconds \
               and self.sample_rate == other.sample_rate

    def __ne__(self, other):
        assert isinstance(other, Timer), \
            'Timer can be compared to Timer only'
        return self.name != other.name \
               or self.milliseconds != other.milliseconds \
               or self.sample_rate != other.sample_rate


class Gauge(AbstractMetric):
    def __init__(self, name, value, sample_rate=1):
        self._value = 0  # type: float
        super(Gauge, self).__init__(name)
        self.value = value
        self.sample_rate = sample_rate

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # type: (float) -> None
        assert is_numeric(value), \
            'Gauge value should be numeric'
        assert value >= 0, \
            'Gauge value should not be negative'
        self._value = value

    def to_request(self):
        # type: () -> bytes
        result = "{0}:{1}|g".format(self._name, self._value)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result

    def __eq__(self, other):
        assert isinstance(other, Gauge), \
            'Gauge can be compared to Gauge only'
        return self.name == other.name \
               and self.value == other.value \
               and self.sample_rate == other.sample_rate

    def __ne__(self, other):
        assert isinstance(other, Gauge), \
            'Gauge can be compared to Gauge only'
        return self.name != other.name \
               or self.value != other.value \
               or self.sample_rate != other.sample_rate


class Set(AbstractMetric):
    def __init__(self, name, value, sample_rate=1):
        self._value = 0  # type: Any
        super(Set, self).__init__(name)
        self.value = value
        self.sample_rate = sample_rate

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # type: (Any) -> None
        try:
            str(value)
        except (TypeError, ValueError):
            raise AssertionError(
                "Set value should be convertible to string")
        try:
            hash(value)
        except (TypeError, ValueError):
            raise AssertionError(
                "Set value should be hashable")
        self._value = value

    def to_request(self):
        # type: () -> bytes
        result = "{0}:{1}|s".format(self._name, self._value)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result

    def __eq__(self, other):
        assert isinstance(other, Set), \
            "Set can be compared to Set only"
        return self.name == other.name \
               and self.value == other.value \
               and self.sample_rate == other.sample_rate

    def __ne__(self, other):
        assert isinstance(other, Set), \
            "Set can be compared to Set only"
        return self.name != other.name \
               or self.value != other.value \
               or self.sample_rate != other.sample_rate


class GaugeDelta(AbstractMetric):
    def __init__(self, name, delta, sample_rate=1):
        self._delta = 0  # type: float
        super(GaugeDelta, self).__init__(name)
        self.delta = delta
        self.sample_rate = sample_rate

    @property
    def delta(self):
        return self._delta

    @delta.setter
    def delta(self, delta):
        # type: (float) -> None
        assert is_numeric(delta), \
            "Gauge delta should be numeric"
        self._delta = delta

    def to_request(self):
        # type: () -> bytes
        result = "{}:{:+n}|g".format(self._name, self._delta)
        if self._sample_rate != 1:
            result += "|@{:n}".format(self._sample_rate)
        return result

    def __eq__(self, other):
        assert isinstance(other, GaugeDelta), \
            'GaugeDelta can be compared to GaugeDelta only'
        return self.name == other.name \
               and self.delta == other.delta \
               and self.sample_rate == other.sample_rate

    def __ne__(self, other):
        assert isinstance(other, GaugeDelta), \
            'GaugeDelta can be compared to GaugeDelta only'
        return self.name != other.name \
               or self.delta != other.delta \
               or self.sample_rate != other.sample_rate


__all__ = ['Counter', 'Timer', 'Gauge',
           'Set', 'GaugeDelta',
           'normalize_metric_name',
           'parse_metric_from_request'
           ]
