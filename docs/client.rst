
Client
======

The client module provides clients for Statsd server to send metrics.

.. code-block:: python

    from statsdmetrics.client import Client
    client = Client("stats.example.org")
    client.increment("login")
    client.timing("db.search.username", 3500)

The client settings (remote host, port or prefix) can be changed later (if it's required).

.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org")
    client.increment("login")
    # settings can be updated later
    client.host = "localhost"
    client.port = 8126
    client.prefix = "other"
    client.gauge_delta("memory", -256)
    client.decrement(name="connections", 2)

Sending multiple metrics in batch requests is supported through `BatchClient` class, either
by using an available client as the context manager:


.. code-block:: python

    from statsdmetrics.client import Client

    client = Client("stats.example.org")
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

