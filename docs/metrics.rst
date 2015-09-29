*******
Metrics
*******

Define the data types used in Statsd. Each data type is defined as a class, supported data types are:

* :class:`~metrics.Counter`
* :class:`~metrics.Timer`
* :class:`~metrics.Gauge`
* :class:`~metrics.Set`
* :class:`~metrics.GaugeDelta`

.. note::

    The metric classes and helper functions are available from the package
    directly, but internally they are defined in :mod:`metrics` module.
    So there is no need to import the :mod:`metrics` module direcly,
    unless you're trying to access those objects that are not used reguraly and hence
    are not exported, like the :class:`~metrics.AbstractMetric` class.

Each metric requires a name and a value.

.. code-block:: python

    from statsdmetrics import Counter, Timer
    counter = Counter('event.login', 1)
    timer = Timer('db.query.user', 10)

An optional sample rate can be specified for the metrics. Sample rate is used by the client and the server to
help to reduce network traffic, or reduce the load on the server.

.. code-block:: python

    >>> from statsdmetrics import Counter
    >>> counter = Counter('event.login', 1, 0.2)
    >>> counter.name
    'event.login'
    >>> counter.count
    1
    >>> counter.sample_rate
    0.2

All metrics have :attr:`~metrics.AbstractMetric.name` and :attr:`~metrics.AbstractMetric.sample_rate` properties,
but they store their value in different properties.

Metrics provide :meth:`~metrics.AbstractMetric.to_request` method to create the proper value used to send the metric to the server.

.. code-block:: python

    >>> from statsdmetrics import Counter, Timer, Gauge, Set, GaugeDelta
    >>> counter = Counter('event.login', 1, 0.2)
    >>> counter.to_request()
    'event.login:1|c|@0.2'
    >>> timer = Timer('db.query.user', 10, 0.5)
    >>> timer.to_request()
    'db.query.user:10|ms|@0.5'
    >>> gauge = Gauge('memory', 20480)
    >>> gauge.to_request()
    'memory:20480|g'
    >>> set_ = Set('unique.users', 'first')
    >>> set_.to_request()
    'unique.users:first|s'
    >>> delta = GaugeDelta('memory', 128)
    >>> delta.to_request()
    'memory:+128|g'
    >>> delta.delta = -256
    >>> delta.to_request()
    'memory:-256|g'

:mod:`metrics` -- Metric classes and helper functions
=====================================================

.. module:: metrics
    :synopsis: Define metrics classes and helper functions
.. moduleauthor:: Farzad Ghanei


Metric Classes
--------------

.. class:: AbstractMetric

    Abstract class that all metric classes would extend from

    .. data:: name

        the name of the metric

    .. data:: sample_rate

        the rate of sampling that the client considers when sending metrics

    .. method:: to_request() -> str

        return the string that is used in the Statsd request to send the metric


.. class:: Counter(name, count, [sample_rate])

    A metric to count events

    .. data:: count

        current count of events being reporeted via the metric

.. class:: Timer(name, milliseconds, [sample_rate])

    A metric for timing durations, in milliseconds.

    .. data:: milliseconds

        number of milliseconds for the duration

.. class:: Gauge(name, value, [sample_rate])

    Any arbitrary value, like the memory usage in bytes.

    .. data:: value

        the value of the metric

.. class:: Set(name, value, [sample_rate])

    A set of unique values counted on the server side for each sampling period.
    Techincally the value could be anything that can be serialized to a string (to be sent
    on the request).

    .. data:: value

        the value of the metric

.. class:: GaugeDelta(name, delta, [sample_rate])

    A value change in a gauge, could be a positive or negative numeric value.

    .. data:: delta

        the difference in the value of the gauge


Module functions
----------------

.. function:: normalize_metric_name(name) -> str

    normalize a metric name, removing characters that might not be welcome by common backends.

    .. code-block:: python

        >>> from statsdmetrics import normalize_metric_name
        >>> normalize_metric_name("will replace some, and $remove! others*")
        'will_replace_some_and_remove_others'

    If passed argument is not a string, an ``TypeError`` is raised.

.. function:: parse_metric_from_request(request) -> str

    parse a metric object from a request string.

    .. code-block:: python

        >>> from statsdmetrics import parse_metric_from_request
        >>> metric = parse_metric_from_request("memory:2048|g")
        >>> type(metric)
        <class 'statsdmetrics.metrics.Gauge'>
        >>> metric.name, metric.value, metric.sample_rate
        ('memory', 2048.0, 1)
        >>> metric = parse_metric_from_request('event.connections:-2|c|@0.6')
        >>> type(metric)
        <class 'statsdmetrics.metrics.Counter'>
        >>> metric.name, metric.count, metric.sample_rate
        ('event.connections', -2, 0.6)

    If the request is invalid, a ``ValueError`` is raised.
