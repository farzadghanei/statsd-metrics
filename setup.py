#!/usr/bin/env python

"""
statsdmetrics
--------------

Statsd metrics and clients
"""
from __future__ import print_function

import os
from os.path import dirname
from setuptools import setup, find_packages

try:
    from typing import Dict, Any
except ImportError:
    Dict, Any = None, None  # type: ignore

try:
    import distutilazy.test  # type: ignore
    import distutilazy.clean  # type: ignore
except ImportError:
    distutilazy = None  # type: ignore

from statsdmetrics import __version__

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Programming Language :: Python :: Implementation :: Jython",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Networking :: Monitoring"
]

long_description = __doc__
with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fh:
    long_description = fh.read()

setup_params = dict(
    name="statsdmetrics",
    packages=find_packages(),
    version=__version__,
    description="Statsd metrics classes and clients",
    long_description=long_description,
    author="Farzad Ghanei",
    author_email="farzad.ghanei@gmail.com",
    url="https://github.com/farzadghanei/statsd-metrics",
    license="MIT",
    classifiers=classifiers,
    keywords="statsd metrics client",
    test_suite="tests",
    zip_safe=True
)  # type: Dict[str, Any]

setup_params["extras_require"] = {"dev": ["distutilazy>=0.4.2", "mock", "typing"]}

if distutilazy:
    setup_params["cmdclass"] = dict(
        test=distutilazy.test.run_tests,
        clean_pyc=distutilazy.clean.clean_pyc,
        clean=distutilazy.clean.clean_all
    )

if __name__ == "__main__":
    setup(**setup_params)

__all__ = ['setup_params', 'classifiers', 'long_description']
