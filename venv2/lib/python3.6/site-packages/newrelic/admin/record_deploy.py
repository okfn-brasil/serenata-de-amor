from __future__ import print_function

import pwd
import os

from newrelic.admin import command, usage

from newrelic.agent import initialize, global_settings
from newrelic.common import certs
from newrelic.network.addresses import proxy_details

from newrelic.packages import requests


@command('record-deploy', 'config_file description [revision changelog user]',
"""Records a deployment for the monitored application.""")
def local_config(args):
    import sys

    if len(args) < 2:
        usage('record-deploy')
        sys.exit(1)

    def _args(config_file, description, revision=None, changelog=None,
            user=None, *args):
        return config_file, description, revision, changelog, user

    config_file, description, revision, changelog, user = _args(*args)

    settings = global_settings()

    settings.monitor_mode = False

    initialize(config_file)

    app_name = settings.app_name

    api_key = settings.api_key or 'NO API KEY WAS SET IN AGENT CONFIGURATION'

    host = settings.host

    if host == 'collector.newrelic.com':
        host = 'api.newrelic.com'
    elif host == 'staging-collector.newrelic.com':
        host = 'staging-api.newrelic.com'

    port = settings.port
    ssl = settings.ssl

    url = '%s://%s/deployments.xml'

    scheme = ssl and 'https' or 'http'
    server = port and '%s:%d' % (host, port) or host

    url = url % (scheme, server)

    proxy_host = settings.proxy_host
    proxy_port = settings.proxy_port
    proxy_user = settings.proxy_user
    proxy_pass = settings.proxy_pass

    timeout = settings.agent_limits.data_collector_timeout

    proxies = proxy_details(None, proxy_host, proxy_port, proxy_user,
            proxy_pass)

    if user is None:
        user = pwd.getpwuid(os.getuid()).pw_gecos

    data = {}

    data['deployment[app_name]'] = app_name

    if description is not None:
        data['deployment[description]'] = description
    if revision is not None:
        data['deployment[revision]'] = revision
    if changelog is not None:
        data['deployment[changelog]'] = changelog
    if user is not None:
        data['deployment[user]'] = user

    headers = {}

    headers['X-API-Key'] = api_key

    cert_loc = certs.where()

    r = requests.post(url, proxies=proxies, headers=headers,
            timeout=timeout, data=data, verify=cert_loc)

    if r.status_code != 201:
        raise RuntimeError('An unexpected HTTP response of %r was received '
                'for request made to %r. The API key for the request was '
                '%r. The payload for the request was %r. If this issue '
                'persists then please report this problem to New Relic '
                'support for further investigation.' % (r.status_code,
                url, api_key, data))
