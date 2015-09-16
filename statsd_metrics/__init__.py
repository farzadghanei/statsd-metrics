"""
    statsd_metrics
    --------------

Data metrics for Statsd.

:license: relased under the terms of the MIT license.
See LICENSE file for more information.
"""

__version__ = '0.0.1'

from .metrics import Counter, Timer, normalize_metric_name

__all__ = (Counter, Timer, normalize_metric_name)
