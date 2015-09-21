Statsd Metrics
==============

.. image:: https://travis-ci.org/farzadghanei/statsd-metrics.svg?branch=master
    :target: https://travis-ci.org/farzadghanei/statsd-metrics

Metric classes for Statsd and and functionality to create, parse and send
Statsd requests.

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

    client = Client("stats.example.org", prefix="region")

    client.increment("login")
    client.timing("db.search.username", 3500)
    client.set("unique.ip_address", "10.10.10.1")
    client.gauge("memory", 20480)
    client.gauge_delta("memory", -256)

    # change settings
    client.host = "localhost"
    client.port = 8126

    client.decrement(name="connections", 2, rate=0.9)

Dependencies
------------
There are no specific dependencies, it runs on Python 2.7+ (CPython 3.2, 3.3
3.4 and 3.5, PyPy and PyPy3 are tested)

however on development (and test) environment
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
