******
Client
******

To send the metrics to Statsd server, client classes are available
in the :mod:`client` package and :mod:`client.tcp` module.


:mod:`client` -- Statsd client
==============================

.. module:: client
    :synopsis: Define Statsd client classes
.. moduleauthor:: Farzad Ghanei

.. class:: Client(host, [port=8125], [prefix=''])

    Default Statsd client that sends each metric in a separate UDP request

    .. data:: host

        the host name (or IP address) of Statsd server. This property is **readonly**.

    .. data:: port

        the port number of Statsd server. This property is **readonly**.

    .. data:: prefix

        the default prefix for all metric names sent from the client

    .. data:: remote_address

        tuple of resolved server address (host, port). This property is **readonly**.

    .. method:: increment(name, [count=1], [rate=1])

        Increase a :class:`~metrics.Counter` metric by ``count`` with an integer value.
        An optional sample rate can be specified.

    .. method:: decrement(name, [count=1], [rate=1])

        Decrease a :class:`~metrics.Counter` metric by ``count`` with an integer value.
        An optional sample rate can be specified.

    .. method:: timing(name, milliseconds, [rate=1])

        Send a :class:`~metrics.Timer` metric for the duration of a task in milliseconds. The ``milliseconds``
        should be a none-negative numeric value.
        An optional sample rate can be specified.

    .. method:: gauge(name, value, [rate=1])

        Send a :class:`~metrics.Gauge` metric with the specified value. The ``value`` should be a none-negative
        numeric value.
        An optional sample rate can be specified.

    .. method:: set(name, value, [rate=1])

        Send a :class:`~metrics.Set` metric with the specified value. The server will count the number of unique
        values during each sampling period. The ``value`` could be any value that can be converted
        to a string.
        An optional sample rate can be specified.

    .. method:: gauge_delta(name, delta, [rate=1])

        Send a :class:`~metrics.GaugeDelta` metric with the specified delta. The ``delta`` should be
        a numeric value. An optional sample rate can be specified.

    .. method:: batch_client([size=512])

        Create a :class:`~BatchClient` object, using the same configurations of current client.
        This batch client could be used as a context manager in a ``with`` statement. After the ``with``
        block when the context manager exits, all the metrics are flushed to the server in batch requests.


.. note::

        Most Statsd servers do not apply the sample rate
        on timing metrics calculated results (mean, percentile, max, min), gauge or
        set metrics, but they take the rate into account for the number of received samples.
        Some statsd servers totally ignore the sample rate for metrics other than counters.


Examples
--------

.. code-block:: python

    from statsdmetrics.client import Client
    client = Client("stats.example.org")
    client.increment("login")
    client.timing("db.search.username", 3500)
    client.prefix = "other"
    client.gauge_delta("memory", -256)
    client.decrement(name="connections", count=2)

.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org")
    with client.batch_client() as batch_client:
        batch_client.increment("login")
        batch_client.decrement(name="connections", count=2)
        batch_client.timing("db.search.username", 3500)
    # now all metrics are flushed automatically in batch requests


.. class:: BatchClient(host, [port=8125], [prefix=''], [batch_size=512])

    Statsd client that buffers all metrics and sends them in batch requests
    over UDP when instructed to flush the metrics explicitly.

    Each UDP request might contain multiple metrics, but limited to a certain batch size
    to avoid UDP fragmentation.

    The size of batch requests is not the fixed size of the requests, since metrics can not be broken
    into multiple requests. So if adding a new metric overflows this size, then that metric will be sent in
    a new batch request.


    .. data:: batch_size

        Size of each batch request. This property is **readonly**.

    .. method:: clear()

        Clear buffered metrics

    .. method:: flush()

        Send the buffered metrics in batch requests.

    .. method:: unit_client()

        Create a :class:`~Client` object, using the same configurations of current batch client
        to send the metrics on each request. The client uses the same resources as the batch client.


.. code-block:: python

    from statsdmetrics.client import BatchClient

    client = BatchClient("stats.example.org")
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    client.flush() # sends one UDP packet to remote server, carrying both metrics


:mod:`client.tcp` -- Statsd client sending metrics over TCP
===========================================================

.. module:: client.tcp
    :synopsis: Define Statsd client classes that send metrics over TCP
.. moduleauthor:: Farzad Ghanei

.. class:: TCPClient(host, [port=8125], [prefix=''])

    Statsd client that sends each metric in separate requests over TCP.

    Provides the same interface as :class:`~client.Client`.

Examples
--------

.. code-block:: python

    from statsdmetrics.client.tcp import TCPClient
    client = TCPClient("stats.example.org")
    client.increment("login")
    client.timing("db.search.username", 3500)
    client.prefix = "other"
    client.gauge_delta("memory", -256)
    client.decrement(name="connections", count=2)

.. code-block:: python

    from statsdmetrics.client.tcp import TCPClient

    client = TCPClient("stats.example.org")
    with client.batch_client() as batch_client:
        batch_client.increment("login")
        batch_client.decrement(name="connections", count=2)
        batch_client.timing("db.search.username", 3500)
    # now all metrics are flushed automatically in batch requests


.. class:: TCPBatchClient(host, [port=8125], [prefix=''], [batch_size=512])

    Statsd client that buffers all metrics and sends them in batch requests
    over TCP when instructed to flush the metrics explicitly.

    Provides the same interface as :class:`~client.BatchClient`.


.. code-block:: python

    from statsdmetrics.client.tcp import TCPBatchClient

    client = TCPBatchClient("stats.example.org")
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    client.flush() # sends one TCP packet to remote server, carrying both metrics


:mod:`client.timing`. -- Timing helpers
=======================================

.. module:: client.timing
    :synopsis: Provides easier ways to send timing metrics. Most of times there is no need to instantiate these classes,
               but they can be obtained directly from any client class in the :mod:`client` package.

.. moduleauthor:: Farzad Ghanei

.. class:: Chronometer(client, [rate=1])

    Chronometer calculates duration (of function calls, etc.) and
    sends them with provided metric names.

    .. data:: client

        The client used to send the timing metrics. This can be any client
        from :mod:`client` package.

    .. data:: rate

        the default sample rate for metrics to send. Should be a float between 0 and 1.
        This is the same as used in all clients.

    .. method:: since(name, timestamp, [rate=None])

        Calculate the time passed since the given timestamp, and send
        a :class:`~metrics.Timer` metric with the provided name.
        The timestamp can be a float (seconds passed from epoch, as returned by :func:`time.time()`,
        or a :class:`datetime.datetime` instance.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.

    .. method:: time_calllable(name, target, [rate=None], [\*args], [\*\*kwargs])

        Calculate the time it takes to run the callable `target` (with provided \*args and \*\*kwargs)
        and send the a :class:`~metrics.Timer` metric with the specific name.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.

    .. method:: wrap(name, , [rate=None])

        Used as a function decorator, to calculae the time it takes
        to run the decorated function, and send a :class:`~metrics.Timer` metric
        with the specified name.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.


Examples
--------

.. code-block:: python

    from time import time, sleep
    from statsdmetrics.cllient import Client
    from statsdmetrics.client.timing import Chronometer

    start_time = time()
    client = Client("stats.example.org")
    chronometer = Chronometer(client)
    chronometer.since("instantiate", start_time)

    def wait(secs):
        sleep(secs) # or any timed operation

    chronometer.time_calllable("waited", wait, 1, 0.56)

    @chronometer.wrap("wait_decorated")
    def another_wait(secs):
        sleep(secs) # or any timed operation

    another_wait(0.23) # sends the "wait_decorated" Timer metric
    chronometer.since("overall", start_time)


If a batch client (like :class:`client.BatchClient` or :class:`client.tcp.TCPBatchClient`)
is used, then the behavior of the client requires an explicit `flush()` call.

.. code-block:: python

    from datetime import datetime
    from statsdmetrics.cllient.tcp import TCPBatchCPClient
    from statsdmetrics.client.timing import Chronometer

    start_time = datetime.now()
    client = TCPBatchClient("stats.example.org")
    chronometer = Chronometer(client)
    chronometer.since("instantiate", start_time)

    def wait_with_kwargs(name, key=val):
        sleep(1) # or any timed operation

    chronometer.time_calllable("waited", wait_with_kwargs, 1, name="foo", key="bar")
    client.flush()

