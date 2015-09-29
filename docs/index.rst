******************************************
Welcome to Statsd Metrics's documentation!
******************************************

Contents:

.. toctree::
   :maxdepth: 2

   metrics
   client

Introduction
============

Statsd metrics is an API to create, parse or send metrics to a Statsd server.

Metric Classes
--------------
Metric classes are used to define the data type and values for each metric,
and to create the contents of the request that will be setn to the Statsd server.

Available metrics:

* :class:`~metrics.Counter`
* :class:`~metrics.Timer`
* :class:`~metrics.Gauge`
* :class:`~metrics.Set`
* :class:`~metrics.GaugeDelta`

The :mod:`~metrics` module also provides helper functions to normalize metric names, and a parse a Statsd request
and return the correspodning metric object. This could be used on the server side to parse the received requests.

Clients
-------
- :class:`~client.Client`: Default client, sends request on each call direclty.
- :class:`~client.BatchClient`: Buffers metrics and flushes them in batch requests.

Installation
============

.. code-block:: bash

  pip install statsdmetrics


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

License
=======
Statsd metrics is released under the terms of the `MIT license <http://opensource.org/licenses/MIT>`_.

Development
===========

* Code is on `GitHub <https://github.com/farzadghanei/statsd-metrics>`_
* Documentations are on `Read The Docs <https://statsd-metrics.readthedocs.org>`_
