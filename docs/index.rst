******************************************
Welcome to Statsd Metrics's documentation!
******************************************

Contents:

.. toctree::
   :maxdepth: 2

   metrics
   client
   client_timing

Introduction
============

Metric classes for Statsd, and Statsd clients (each metric in a single request, or send batch requests).
Provides APIs to create, parse or send metrics to a Statsd server.


The library also comes with a rich set of Statsd clients using the same metric classes, and
Python standard library socket module.

Metric Classes
--------------
Metric classes represent the data used in Statsd protocol excluding the IO, to create,
represent and parse Statsd requests. So any Statsd server and client regardless of the
IO implementation can use them to send/receive Statsd requests.

Available metrics:

* :class:`~metrics.Counter`
* :class:`~metrics.Timer`
* :class:`~metrics.Gauge`
* :class:`~metrics.Set`
* :class:`~metrics.GaugeDelta`

The :mod:`~metrics` module also provides helper functions to normalize metric names, and a parse a Statsd request
and return the corresponding metric object. This could be used on the server side to parse the received requests.

Clients
-------
A rich set of Statsd clients using the same metric classes, and Python standard library socket module.

* :class:`~client.Client`: Default client, sends request on each call using UDP
* :class:`~client.BatchClient`: Buffers metrics and flushes them in batch requests using UDP
* :class:`~client.tcp.TCPClient`: Sends request on each call using TCP
* :class:`~client.tcp.TCPBatchClient`: Buffers metrics and flushes them in batch requests using TCP

Timing Helpers
--------------
* :class:`~client.timing.Chronometer`: Measure duration and send multiple :class:`~metrics.Timer` metrics
* :class:`~client.timing.Stopwatch`: Measure time passed from a given reference and send :class:`~metrics.Timer` metrics with a specific name

Installation
============

.. code-block:: bash

  pip install statsdmetrics


Dependencies
------------
The only dependencies are Python 2.7+ and setuptools.
CPython 2.7, 3.2, 3.3, 3.4, 3.5, 3.6-dev, PyPy 2.6 and PyPy3 2.4, and Jython 2.7 are tested)

However on development (and test) environment
`mock <https://pypi.python.org/pypi/mock>`_ is required,
`typing <https://pypi.python.org/pypi/typing>`_ and
`distutilazy <https://pypi.python.org/pypi/distutilazy>`_ are recommended.

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
