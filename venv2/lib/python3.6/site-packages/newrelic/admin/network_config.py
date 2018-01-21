from __future__ import print_function

from newrelic.admin import command, usage


@command('network-config', 'config_file [log_file]',
"""Prints out the network configuration after having loaded the settings
from <config_file>.""")
def network_config(args):
    import os
    import sys
    import logging

    if len(args) == 0:
        usage('network-config')
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

    print('host = %r' % _settings.host)
    print('port = %r' % _settings.port)
    print('proxy_scheme = %r' % _settings.proxy_scheme)
    print('proxy_host = %r' % _settings.proxy_host)
    print('proxy_port = %r' % _settings.proxy_port)
    print('proxy_user = %r' % _settings.proxy_user)
    print('proxy_pass = %r' % _settings.proxy_pass)
    print('ssl = %r' % _settings.ssl)
