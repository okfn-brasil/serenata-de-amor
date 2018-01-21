from __future__ import print_function

from newrelic.admin import command, usage


@command('local-config', 'config_file [log_file]',
"""Dumps out the local agent configuration after having loaded the settings
from <config_file>.""")
def local_config(args):
    import os
    import sys
    import logging

    if len(args) == 0:
        usage('local-config')
        sys.exit(1)

    from newrelic.config import initialize
    from newrelic.core.config import global_settings

    if len(args) >= 2:
        log_file = args[1]
    else:
        log_file = '/tmp/python-agent-test.log'

    log_level = logging.DEBUG

    try:
        os.unlink(log_file)
    except Exception:
        pass

    config_file = args[0]
    environment = os.environ.get('NEW_RELIC_ENVIRONMENT')

    if config_file == '-':
        config_file = os.environ.get('NEW_RELIC_CONFIG_FILE')

    initialize(config_file, environment, ignore_errors=False,
            log_file=log_file, log_level=log_level)

    for key, value in sorted(global_settings()):
        print('%s = %r' % (key, value))
