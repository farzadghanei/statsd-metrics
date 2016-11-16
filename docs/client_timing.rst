**************
Timing Helpers
**************

Classes to help measure time and send :class:`metrics.Timer` metrics using any :mod:`client`.

:mod:`client.timing` -- Timing helpers
=======================================

.. module:: client.timing
    :synopsis: Provides easier ways to send timing metrics. Most of times there is no need to instantiate these classes,
               but they can be obtained directly from any client class in the :mod:`client` package.

.. moduleauthor:: Farzad Ghanei

.. class:: Chronometer(client, rate=1)

    Chronometer calculates duration (of function calls, etc.) and
    sends them with provided metric names.
    Normally these is no need to instantiate this class directly, but
    you can call :meth:`client.Client.chronometer` on any client, to
    get a configured Chronometer.

    .. data:: client

        The client used to send the timing metrics. This can be any client
        from :mod:`client` package.

    .. data:: rate

        the default sample rate for metrics to send. Should be a float between 0 and 1.
        This is the same as used in all clients.

    .. method:: since(name, timestamp, rate=None)

        Calculate the time passed since the given timestamp, and send
        a :class:`~metrics.Timer` metric with the provided name.
        The timestamp can be a float (seconds passed from epoch, as returned by :func:`time.time()`,
        or a :class:`datetime.datetime` instance.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.

    .. method:: time_callable(name, target, rate=None, args=(), kwargs={})

        Calculate the time it takes to run the callable `target` (with provided args and kwargs)
        and send the a :class:`~metrics.Timer` metric with the specific name.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.

    .. method:: wrap(name, rate=None)

        Used as a function decorator, to calculate the time it takes
        to run the decorated function, and send a :class:`~metrics.Timer` metric
        with the specified name.
        Rate is the sample rate to use, or None to use the default sample rate of the Chronometer.


Examples
--------

.. code-block:: python

    from time import time, sleep
    from statsdmetrics.client import Client
    from statsdmetrics.client.timing import Chronometer

    start_time = time()
    client = Client("stats.example.org")
    chronometer = Chronometer(client)
    chronometer.since("instantiate", start_time)

    def wait(secs):
        sleep(secs) # or any timed operation

    chronometer.time_callable("waited", wait, args=(0.56,))

    @chronometer.wrap("wait_decorated")
    def another_wait(secs):
        sleep(secs) # or any timed operation

    another_wait(0.23) # sends the "wait_decorated" Timer metric
    chronometer.since("overall", start_time)


If a batch client (like :class:`client.BatchClient` or :class:`client.tcp.TCPBatchClient`)
is used, then the behavior of the client requires an explicit `flush()` call.

.. code-block:: python

    from datetime import datetime
    from statsdmetrics.client.tcp import TCPBatchCPClient
    from statsdmetrics.client.timing import Chronometer

    start_time = datetime.now()
    client = TCPBatchClient("stats.example.org")
    chronometer = Chronometer(client)
    chronometer.since("instantiate", start_time)

    def wait_with_kwargs(name, key=val):
        sleep(1) # or any timed operation

    chronometer.time_callable("waited", wait_with_kwargs, kwargs=dict(name="foo", key="bar"))
    client.flush()


.. class:: Stopwatch(client, name, rate=1, reference=None)

    Stopwatch calculates duration passed from a given reference time (by default uses
    the instantiation time) for a specific metric name.
    So time passed since the reference time can be sent multiple times.
    Normally these is no need to instantiate this class directly, but
    you can call :meth:`client.Client.stopwatch` on any client, to
    get a configured Chronometer.

    .. data:: client

        The client used to send the timing metrics. This can be any client
        from :mod:`client` package.

    .. data:: name

        The name for the metric sent by the stopwatch.

    .. data:: rate

        The default sample rate for metrics to send. Should be a float between 0 and 1.
        This is the same as used in all clients.

    .. data:: reference

        The time reference that duration is calculated from. It's a float value
        of seconds passed since epoch, same as `time.time()`.

    .. method:: reset()

        Reset the stopwatch, updating the reference with current time.
        Returns a self reference for method chaining.

    .. method:: send(rate=None)

        Calculate time passed since :attr:`reference` and send the metric.
        A sampling rate can be specified, or `None` (default) uses the default
        sampling rate of the stopwatch.
        Returns a self reference for method chaining.

