#!/usr/bin/env python

"""
statsdmetrics
--------------

Data metrics for Statsd.

"""
from __future__ import print_function

import os

try:
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup

try:
    import distutilazy.test
    import distutilazy.clean
except ImportError:
    distutilazy = None

from statsdmetrics import __version__

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking :: Monitoring",
    "Topic :: Internet :: Log Analysis"
]

long_description = __doc__
with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fh:
    long_description = fh.read()

setup_params = dict(
    name = 'statsdmetrics',
    packages = ['statsdmetrics'],
    version = __version__,
    description = 'Metric classes for Statsd',
    long_description = long_description,
    author = 'Farzad Ghanei',
    author_email = 'farzad.ghanei@gmail.com',
    license = 'MIT',
    classifiers = classifiers,
)

if distutilazy:
    setup_params['cmdclass'] = dict(
        test=distutilazy.test.run_tests,
        clean_pyc=distutilazy.clean.clean_pyc,
        clean=distutilazy.clean.clean_all
    )
elif setuptools:
    setup_params['test_suite'] = 'tests'
    setup_params['zip_safe'] = True

if __name__ == '__main__':
    setup(**setup_params)

__all__ = (setup_params, classifiers, long_description)