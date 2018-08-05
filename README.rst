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

    $ pip install statsdmetrics


The only dependencies are Python 2.7+ and setuptools.
CPython 2.7, 3.3, 3.4, 3.5, 3.6,, 3.7-dev, PyPy, and Jython 2.7 are tested)

However on development (and test) environment
`pytest <https://pypi.org/project/pytest/>`_, `mock <https://pypi.org/project/mock>`_ is required (for Python 2),
`typing <https://pypi.org/project/typing>`_ is recommended.

.. code-block:: bash

    # on dev/test env
    $ pip install -r requirements-dev.txt


Development
-----------

* Code is on `GitHub <https://github.com/farzadghanei/statsd-metrics>`_
* Documentations are on `Read The Docs <https://statsd-metrics.readthedocs.org>`_

Tests
^^^^^

`Tox <https://pypi.org/project/tox/>`_ is most convenient to run tests with since it handles creation of virtualenvs

.. code-block:: bash

    $ tox

When development dependencies are installed (preferably with a virtual environment),
tests can be run by calling `pytest`.

.. code-block:: bash

    $ pytest

Integration tests are available as part of the test suite, bringing up dummy servers (but actually listening on
network socket) to capture requests instead of processing them. Then send some metrics and
assert if the captured requests match the expected.

License
-------

Statsd metrics is released under the terms of the
`MIT license <http://opensource.org/licenses/MIT>`_.

The MIT License (MIT)

Copyright (c) 2015-2018 Farzad Ghanei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
