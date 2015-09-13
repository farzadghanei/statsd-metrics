"""
statsd_metrics.metrics
----------------------
Define metrics classes
"""

class Counter(object):
    def __init__(self, balance=0, sample_rate=1):
        self._set_balance(balance)
        self._set_sample_rate(sample_rate)

    @property
    def balance(self):
        return self.__balance

    @balance.setter
    def balance(self, balance):
        self._set_balance(balance)

    @property
    def sample_rate(self):
        return self.__sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        self._set_sample_rate(value)

    def _set_balance(self, balance):
        assert balance == int(balance)
        self.__balance = balance

    def _set_sample_rate(self, rate):
        rate_float = float(rate)
        assert rate_float > 0
        self.__sample_rate = float(rate_float)

__all__ = (Counter,)