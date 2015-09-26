Statsd Metrics
==============

.. image:: https://travis-ci.org/farzadghanei/statsd-metrics.svg?branch=master
    :target: https://travis-ci.org/farzadghanei/statsd-metrics

Metric classes for Statsd and and functionality to create, parse and send
Statsd requests (each metric in a single request, or send batch requests).

Metric Classes
--------------
Available metrics:

- Counter
- Timer
- Gauge
- Set
- GaugeDelta

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

Statsd Client
-------------
Send Statsd requests

.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org")
    client.increment("login")
    client.timing("db.search.username", 3500)
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    # settings can be updated later
    client.host = "localhost"
    client.port = 8126
    client.gauge_delta("memory", -256)
    client.decrement(name="connections", 2)


Sending multiple metrics in batch requests is supported through `BatchClient` class, either
by using an available client as the context manager:


.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org", prefix="region")
    with client.batch_client() as batch_client:
        batch_client.increment("login")
        batch_client.decrement(name="connections", 2)
        batch_client.timing("db.search.username", 3500)
    # now all metrics are flushed automatically in batch requests


or by creating a `BatchClient` object explicitly:


.. code-block:: python

    from statsdmetrics.client import BatchClient

    client = BatchClient("stats.example.org")
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    client.flush() # sends one UDP packet to remote server, carrying both metrics


Dependencies
------------
There are no specific dependencies, it runs on Python 2.7+ (CPython 2.7, 3.2, 3.3
3.4 and 3.5, PyPy 2.6 and PyPy3 2.4, and Jython 2.7 are tested)

However on development (and test) environment
`mock <https://pypi.python.org/pypi/mock>`__ is required, and
`distutilazy <https://pypi.python.org/pypi/distutilazy>`_
(or setuptools as a fallback) is used to run the tests.

.. code-block:: bash

    # on dev/test env
    pip install -r requirements-dev.txt


Tests
-----

If you have make available

.. code-block:: bash

    make test

You can always use the setup.py file

.. code-block:: bash

    python setup.py test

License
-------
Statsd metrics is released under the terms of the
`MIT license <http://opensource.org/licenses/MIT>`_.
