from __future__ import print_function

from newrelic.admin import command, usage


@command('license-key', 'config_file [log_file]',
"""Prints out the account license key after having loaded the settings
from <config_file>.""")
def license_key(args):
    import os
    import sys
    import logging

    if len(args) == 0:
        usage('license-key')
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

    _settings = global_settings()

    print('license_key = %r' % _settings.license_key)
