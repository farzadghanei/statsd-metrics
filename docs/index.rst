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

    $ pip install statsdmetrics


Dependencies
------------
The only dependencies are Python 2.7+ and setuptools.
CPython 2.7, 3.4+, 3.7-dev, PyPy and Jython are tested)

However on development (and test) environment
`pytest <https://pypi.org/project/pytest/>`_, `mock <https://pypi.org/project/mock>`_ is required (for Python 2),
`typing <https://pypi.org/project/typing>`_ is recommended.

.. code-block:: bash

    # on dev/test env
    $ pip install -r requirements-dev.txt


License
=======
Statsd metrics is released under the terms of the `MIT license <http://opensource.org/licenses/MIT>`_.

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

Development
===========

* Code is on `GitHub <https://github.com/farzadghanei/statsd-metrics>`_
* Documentations are on `Read The Docs <https://statsd-metrics.readthedocs.org>`_
