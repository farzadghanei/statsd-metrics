"""
statsdmetrics.app.statsdclient
------------------------------
Statsd client utility app
"""
from __future__ import print_function

import sys
import os
from os.path import dirname
from getopt import getopt, GetoptError

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from statsdmetrics import __version__
from statsdmetrics.client import Client, DEFAULT_PORT


class StatsdClient(object):
    version = __version__

    @classmethod
    def get_usage(cls):
        usage = """Statsd client version {}

Usage: [options] [host][:port]

Sends metrics to Statsd server on host (default=localhost),
and port (default={}).

Metrics are read from standard input, one metric per line:

    method metric_name [value] [sample_rate]

Supported methods are: {}

Example:

    timing db.search.username 3500
    increment login
    decrement connections 2 0.6
    gauge_delta memory -256

Options:
    -h, --help          show this help
    -v, --version       show app version
    --prefix            prefix for all metric names
""".format(cls.version, DEFAULT_PORT, ', '.join(cls.get_client_methods()))
        return usage

    @staticmethod
    def get_cli_options():
        short_opts = ["h", "v"]
        long_opts = ["help", "version", "prefix="]
        return short_opts, long_opts

    @staticmethod
    def _get_short_options_mapping():
        return dict(h="help", v="version")

    @staticmethod
    def get_client_methods():
        return ('increment', 'decrement', 'timing',
                'gauge', 'gauge_delta', 'set')

    def __init__(self, opts=(), args=()):
        opts = self.normalize_options(opts)
        self.options = opts
        self.args = args

    def normalize_options(self, opts):
        short_opts_mapping = self._get_short_options_mapping()
        opts = dict(opts)

        for key in opts:
            if key.startswith('--'):
                opts[key[2:]] = opts[key]
                del opts[key]
            elif key.startswith('-'):
                opts[key[1:]] = opts[key]
                del opts[key]

        for key in opts.keys():
            long_opt = short_opts_mapping.get(key, None)
            if long_opt:
                if long_opt not in opts:
                    opts[long_opt] = opts[key]
                del opts[key]

        return opts

    def _get_server_address(self):
        address = len(self.args) and self.args[0] or "localhost"
        host, _, port = address.partition(":")
        port = port and int(port) or DEFAULT_PORT
        return host, port

    def run(self):
        if "help" in self.options:
            print(self.get_usage())
            return getattr(os,"EX_OK", 0)

        if "version" in self.options:
            print(__version__)
            return getattr(os, "EX_OK", 0)

        host, port = self._get_server_address()
        prefix = self.options.get("prefix", "")

        client = Client(host, port, prefix)
        methods = self.get_client_methods()
        for line in sys.stdin:
            tokens = line.strip().split()
            if len(tokens) < 2:
                print(
                    "ignoring invalid input: '{}'".format(line),
                    file=sys.stderr
                )
                continue
            method_name = tokens.pop(0)
            if method_name not in methods:
                print(
                    "ignoring invalid method '{}'".format(method_name),
                    file=sys.stderr
                )
                continue
            if len(tokens) > 2: # sample rate
                tokens[2] = float(tokens[2])
            method = getattr(client, method_name)
            print(".", end="")
            method(*tokens)
            sys.stderr.flush()
            sys.stdout.flush()


def main():
    short_opts, long_opts = StatsdClient.get_cli_options()
    try:
        opts, args = getopt(
                        sys.argv[1:],
                        "".join(short_opts),
                        long_opts
                    )
    except GetoptError as exp:
        print(
            "invalid options. {}. see help by -h or --help".format(exp),
            file=sys.stderr
        )
        sys.exit(getattr(os, "EX_CONFIG", 78))
    app = StatsdClient(opts, args)
    try:
        sys.exit(app.run())
    except KeyboardInterrupt as e:
        sys.exit(getattr(os, "EX_OK", 0))

if __name__ == "__main__":
    main()
