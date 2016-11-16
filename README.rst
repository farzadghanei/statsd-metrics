**************
Statsd Metrics
**************

.. image:: https://travis-ci.org/farzadghanei/statsd-metrics.svg?branch=master
    :target: https://travis-ci.org/farzadghanei/statsd-metrics

.. image:: https://codecov.io/gh/farzadghanei/statsd-metrics/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/farzadghanei/statsd-metrics

.. image:: https://ci.appveyor.com/api/projects/status/bekwcg8n1xe0w0n9/branch/master?svg=true
    :target: https://ci.appveyor.com/project/farzadghanei/statsd-metrics?branch=master

Metric classes for Statsd, and Statsd clients (each metric in a single request, or send batch requests).

Metric classes represent the data used in Statsd protocol excluding the IO, to create,
represent and parse Statsd requests. So any Statsd server and client regardless of the
IO implementation can use them to send/receive Statsd requests.

The library also comes with a rich set of Statsd clients using the same metric classes, and
Python standard library socket module.


Metric Classes
--------------

* Counter
* Timer
* Gauge
* Set
* GaugeDelta

.. code-block:: python

    from statsdmetrics import Counter, Timer

    counter = Counter('event.login', 1, 0.2)
    counter.to_request() # returns event.login:1|c|@0.2

    timer = Timer('db.search.username', 27.4)
    timer.to_request() # returns db.search.username:27.4|ms

Parse metrics from a Statsd request

.. code-block:: python

    from statsdmetrics import parse_metric_from_request

    event_login = parse_metric_from_request('event.login:1|c|@.2')
    # event_login is a Counter object with count = 1 and sample_rate = 0.2

    mem_usage = parse_metric_from_request('resource.memory:2048|g')
    # mem_usage is a Gauge object with value = 2028

Statsd Clients
--------------
* ``client.Client``: Default client, sends request on each call using UDP
* ``client.BatchClient``: Buffers metrics and flushes them in batch requests using UDP
* ``client.tcp.TCPClient``: Sends request on each call using TCP
* ``client.tcp.TCPBatchClient``: Buffers metrics and flushes them in batch requests using TCP

Send Statsd requests

.. code-block:: python

    from statsdmetrics.client import Client

    # default client, send metrics over UDP
    client = Client("stats.example.org")
    client.increment("login")
    client.decrement("connections", 2)
    client.timing("db.search.username", 3500)
    client.gauge("memory", 20480)
    client.gauge_delta("memory", -256)
    client.set("unique.ip_address", "10.10.10.1")

    # helpers for timing operations
    chronometer = client.chronometer()
    chronometer.time_callable("func1_duration", func1)

    # decorate functions to send timing metrics for the duration of their running time
    @chronometer.wrap("func2_duration")
    def func2():
        pass

    # send timing for duration of a with block
    with client.stopwatch("with_block_duration"):
        pass



Sending multiple metrics in batch requests by ``BatchClient``, either
by using an available client as the context manager:


.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org")
    with client.batch_client() as batch_client:
        batch_client.increment("login")
        batch_client.decrement("connections", 2)
        batch_client.timing("db.search.username", 3500)
    # now all metrics are flushed automatically in batch requests


or by creating a ``BatchClient`` object explicitly:


.. code-block:: python

    from statsdmetrics.client import BatchClient

    client = BatchClient("stats.example.org")
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    client.flush() # sends one UDP packet to remote server, carrying both metrics

    # timing helpers are available on all clients
    chronometer = client.chronometer()
    chronometer.time_callable("func1_duration", func1)

    @chronometer.wrap("func2_duration")
    def func2():
        pass

    with client.stopwatch("with_block_duration"):
        pass

    client.flush()


Installation
------------

.. code-block:: bash

    pip install statsdmetrics


The only dependencies are Python 2.7+ and setuptools.
CPython 2.7, 3.2, 3.3, 3.4, 3.5, 3.6-dev, PyPy 2.6 and PyPy3 2.4, and Jython 2.7 are tested)

However on development (and test) environment
`mock <https://pypi.python.org/pypi/mock>`_ is required,
`typing <https://pypi.python.org/pypi/typing>`_ and
`distutilazy <https://pypi.python.org/pypi/distutilazy>`_ are recommended.

.. code-block:: bash

    # on dev/test env
    pip install -r requirements-dev.txt


Development
-----------

* Code is on `GitHub <https://github.com/farzadghanei/statsd-metrics>`_
* Documentations are on `Read The Docs <https://statsd-metrics.readthedocs.org>`_

Tests
^^^^^

If you have make available

.. code-block:: bash

    make test

You can always use the setup.py file

.. code-block:: bash

    python setup.py test

Integration tests are available, bringing up dummy servers (but actually listening on
network socket) to capture requests instead of processing them. Then send some metrics and
assert if the captured requests match the expected.

.. code-block:: bash

    python tests/integration_test_udp.py
    python tests/integration_test_tcp.py


License
-------

Statsd metrics is released under the terms of the
`MIT license <http://opensource.org/licenses/MIT>`_.
