from __future__ import print_function

from newrelic.admin import command, usage

@command('data-source', 'config_file',
"""Loads the data sources specified in the agent configuration file and
reports data from those data sources using the platform API.
""", log_intercept=False, hidden=True, deprecated=True)
def data_source(args):
    import sys

    if len(args) == 0:
        usage('data-source')
        sys.exit(1)

    from newrelic.platform import run

    run(*args)
