"""This module implements the communications layer with the data collector.

"""

from __future__ import print_function

import logging
import os
import sys
import time
import zlib
import warnings

from pprint import pprint

import newrelic.packages.six as six

import newrelic.packages.requests as requests

from newrelic.common import certs, system_info

from newrelic import version
from newrelic.core.config import (global_settings, global_settings_dump,
        finalize_application_settings)
from newrelic.core.internal_metrics import internal_metric

from newrelic.network.exceptions import (NetworkInterfaceException,
        ForceAgentRestart, ForceAgentDisconnect, DiscardDataForRequest,
        RetryDataForRequest, ServerIsUnavailable)

from newrelic.network.addresses import proxy_details
from newrelic.common.object_wrapper import patch_function_wrapper
from newrelic.common.object_names import callable_name
from newrelic.common.encoding_utils import (json_encode, json_decode,
        unpack_field)
from newrelic.common.system_info import (logical_processor_count,
        total_physical_memory, BootIdUtilization)
from newrelic.common.utilization import (AWSUtilization, AzureUtilization,
        DockerUtilization, GCPUtilization, PCFUtilization)

_logger = logging.getLogger(__name__)

# User agent string that must be used in all requests. The data collector
# does not rely on this, but is used to target specific agents if there
# is a problem with data collector handling requests.

USER_AGENT = 'NewRelic-PythonAgent/%s (Python %s %s)' % (
         version, sys.version.split()[0], sys.platform)

# Data collector URL and proxy settings.


def collector_url(server=None):
    """Returns the URL for talking to the data collector. When no server
    'host:port' is specified then the main data collector host and port is
    taken from the agent configuration. When a server is explicitly passed
    it would be the secondary data collector which subsequent requests
    in an agent session should be sent to.

    """

    settings = global_settings()

    url = '%s://%s/agent_listener/invoke_raw_method'

    scheme = settings.ssl and 'https' or 'http'

    if not server or settings.port:
        # When pulling the port from agent configuration it should only be
        # set when testing against a local data collector. For staging
        # and production should not be set and would default to port 80
        # or 443 based on scheme name in URL and we don't explicitly
        # add the ports.

        if settings.port:
            server = '%s:%d' % (settings.host, settings.port)
        else:
            server = '%s' % settings.host

    return url % (scheme, server)


def proxy_server():
    """Returns the dictionary of proxy server settings to be supplied to
    the 'requests' library when making requests.

    """

    # For backward compatibility from when using requests prior to 2.0.0,
    # we take the proxy_scheme as not being set to mean that we should
    # derive it from whether SSL is being used. This will still be overridden
    # if the proxy scheme was defined as part of proxy URL in proxy_host.

    settings = global_settings()

    ssl = settings.ssl
    proxy_scheme = settings.proxy_scheme

    if proxy_scheme is None:
        proxy_scheme = ssl and 'https' or 'http'

    return proxy_details(proxy_scheme, settings.proxy_host,
            settings.proxy_port, settings.proxy_user, settings.proxy_pass)


def connection_type(proxies):
    """Returns a string describing the connection type for use in metrics.

    """

    settings = global_settings()

    ssl = settings.ssl

    request_scheme = ssl and 'https' or 'http'

    if proxies is None:
        return 'direct/%s' % request_scheme

    proxy_scheme = proxies['http'].split('://')[0]

    return '%s-proxy/%s' % (proxy_scheme, request_scheme)

# This is a monkey patch for urllib3 contained within our bundled requests
# library. This is to override the urllib3 behaviour for how the proxy
# is communicated with so as to allow us to restore the old broken
# behaviour from before requests 2.0.0 so that we can transition
# customers over without outright breaking their existing configurations.


@patch_function_wrapper(
        'newrelic.packages.requests.packages.urllib3.connectionpool',
        'HTTPSConnectionPool._prepare_conn')
def _requests_proxy_scheme_workaround(wrapped, instance, args, kwargs):
    def _params(connection, *args, **kwargs):
        return connection

    pool, connection = instance, _params(*args, **kwargs)

    settings = global_settings()

    if pool.proxy and pool.proxy.scheme == 'https':
        if settings.proxy_scheme in (None, 'https'):
            return connection

    return wrapped(*args, **kwargs)

# This is a monkey patch for requests contained within our bundled requests.
# Have no idea why they made the change, but the change they made in the
# commit:
#
#   https://github.com/kennethreitz/requests/commit/8b7fcfb49a38cd6ee1cbb4a52e0a4af57969abb3
#
# breaks proxying an HTTPS requests over an HTTPS proxy. The original seems to
# be more correct than the changed version and works in testing. Return the
# functionality back to how it worked previously.


@patch_function_wrapper(
        'newrelic.packages.requests.adapters',
        'HTTPAdapter.request_url')
def _requests_request_url_workaround(wrapped, instance, args, kwargs):
    from newrelic.packages.requests.adapters import urldefragauth

    def _bind_params(request, proxies):
        return request, proxies

    request, proxies = _bind_params(*args, **kwargs)

    if not proxies:
        return wrapped(*args, **kwargs)

    return urldefragauth(request.url)


# This is a monkey patch for urllib3 + python3.6 + gevent/eventlet.
# Gevent/Eventlet patches the ssl library resulting in a re-binding that causes
# infinite recursion in a super call. In order to prevent this error, the
# SSLContext object should be accessed through the ssl library attribute.
#
#   https://github.com/python/cpython/commit/328067c468f82e4ec1b5c510a4e84509e010f296#diff-c49248c7181161e24048bec5e35ba953R457
#   https://github.com/gevent/gevent/blob/f3acb176d0f0f1ac797b50e44a5e03726f687c53/src/gevent/_ssl3.py#L67
#   https://github.com/shazow/urllib3/pull/1177
#   https://bugs.python.org/issue29149
#
@patch_function_wrapper(
        'newrelic.packages.requests.packages.urllib3.util.ssl_',
        'SSLContext')
def _urllib3_ssl_recursion_workaround(wrapped, instance, args, kwargs):
    try:
        import ssl
        return ssl.SSLContext(*args, **kwargs)
    except:
        return wrapped(*args, **kwargs)

# Low level network functions and session management. When connecting to
# the data collector it is initially done through the main data collector.
# It is then necessary to ask the data collector for the per-session data
# collector to use. Subsequent calls are then made to it.


_audit_log_fp = None
_audit_log_id = 0


def _log_request(url, params, headers, data):
    settings = global_settings()

    if not settings.audit_log_file:
        return

    global _audit_log_fp

    if not _audit_log_fp:
        log_file = settings.audit_log_file
        try:
            _audit_log_fp = open(log_file, 'a')
        except Exception:
            _logger.exception('Unable to open audit log file %r.', log_file)
            settings.audit_log_file = None
            return

    global _audit_log_id

    _audit_log_id += 1

    print('TIME: %r' % time.strftime('%Y-%m-%d %H:%M:%S',
            time.localtime()), file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('ID: %r' % _audit_log_id, file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('PID: %r' % os.getpid(), file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('URL: %r' % url, file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('PARAMS: %r' % params, file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('HEADERS: %r' % headers, file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('DATA:', end=' ', file=_audit_log_fp)

    if headers.get('Content-Encoding') == 'deflate':
        data = zlib.decompress(data)

        if isinstance(data, bytes):
            data = data.decode('Latin-1')

    object_from_json = json_decode(data)

    pprint(object_from_json, stream=_audit_log_fp)

    if params.get('method') == 'transaction_sample_data':
        for i, sample in enumerate(object_from_json[1]):
            field_as_json = unpack_field(sample[4])
            print(file=_audit_log_fp)
            print('DATA[1][%d][4]:' % i, end=' ', file=_audit_log_fp)
            pprint(field_as_json, stream=_audit_log_fp)

    elif params.get('method') == 'profile_data':
        for i, sample in enumerate(object_from_json[1]):
            field_as_json = unpack_field(sample[4])
            print(file=_audit_log_fp)
            print('DATA[1][%d][4]:' % i, end=' ', file=_audit_log_fp)
            pprint(field_as_json, stream=_audit_log_fp)

    elif params.get('method') == 'sql_trace_data':
        for i, sample in enumerate(object_from_json[0]):
            field_as_json = unpack_field(sample[9])
            print(file=_audit_log_fp)
            print('DATA[0][%d][9]:' % i, end=' ', file=_audit_log_fp)
            pprint(field_as_json, stream=_audit_log_fp)

    print(file=_audit_log_fp)
    print(78 * '=', file=_audit_log_fp)
    print(file=_audit_log_fp)

    _audit_log_fp.flush()

    return _audit_log_id


def _log_response(log_id, result):

    print('TIME: %r' % time.strftime('%Y-%m-%d %H:%M:%S',
            time.localtime()), file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('ID: %r' % _audit_log_id, file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('PID: %r' % os.getpid(), file=_audit_log_fp)
    print(file=_audit_log_fp)
    print('RESULT:', end=' ', file=_audit_log_fp)

    pprint(result, stream=_audit_log_fp)

    print(file=_audit_log_fp)
    print(78 * '=', file=_audit_log_fp)
    print(file=_audit_log_fp)

    _audit_log_fp.flush()


_deflate_exclude_list = set(['transaction_sample_data', 'sql_trace_data',
    'profile_data'])


def send_request(session, url, method, license_key, agent_run_id=None,
            payload=()):
    """Constructs and sends a request to the data collector."""

    params = {}
    headers = {}

    settings = global_settings()

    start = time.time()

    # Validate that the license key was actually set and if not replace
    # it with a string which makes it more obvious it was not set.

    if not license_key:
        license_key = 'NO LICENSE KEY WAS SET IN AGENT CONFIGURATION'

    # The agent formats requests and is able to handle responses for
    # protocol version 14.

    params['method'] = method
    params['license_key'] = license_key
    params['protocol_version'] = '14'
    params['marshal_format'] = 'json'

    if agent_run_id:
        params['run_id'] = str(agent_run_id)

    headers['User-Agent'] = USER_AGENT
    headers['Content-Encoding'] = 'identity'

    # Set up definitions for proxy server in case that has been set.

    proxies = proxy_server()

    # At this time we use JSON content encoding for the data being sent.
    # If an error does occur when encoding the JSON, then it isn't
    # likely going to work later on in a subsequent request with same
    # data, even if aggregated with other data, so we need to log the
    # details and then flag that data should be thrown away. Don't mind
    # being noisy in the the log in this situation as it would indicate
    # a problem with the implementation of the agent.

    try:
        data = json_encode(payload)

    except Exception:
        _logger.exception('Error encoding data for JSON payload for '
                'method %r with payload of %r. Please report this problem '
                'to New Relic support.', method, payload)

        raise DiscardDataForRequest(str(sys.exc_info()[1]))

    # Log details of call and/or payload for debugging. Use the JSON
    # encoded value to know that what is encoded is correct.

    if settings.debug.log_data_collector_payloads:
        _logger.debug('Calling data collector with url=%r, method=%r and '
                'payload=%r.', url, method, data)
    elif settings.debug.log_data_collector_calls:
        _logger.debug('Calling data collector with url=%r and method=%r.',
                url, method)

    # Compress the serialized JSON being sent as content if over 64KiB
    # in size and not in message types that further compression is
    # excluded.

    threshold = settings.agent_limits.data_compression_threshold

    if method not in _deflate_exclude_list and len(data) > threshold:
        headers['Content-Encoding'] = 'deflate'

        internal_metric('Supportability/Python/Collector/ZLIB/Bytes/'
                '%s' % method, len(data))

        level = settings.agent_limits.data_compression_level
        level = level or zlib.Z_DEFAULT_COMPRESSION
        data = zlib.compress(six.b(data), level)

    # If there is no requests session object provided for making
    # requests create one now. We want to close this as soon as we
    # are done with it.

    auto_close_session = False

    if not session:
        session = requests.session()
        auto_close_session = True

    # The 'requests' library can raise a number of exceptions derived
    # from 'RequestException' before we even manage to get a connection
    # to the data collector.
    #
    # The data collector can then generate a number of different types of
    # HTTP errors for requests. These are:
    #
    # 400 Bad Request - For incorrect method type or incorrectly
    # constructed parameters. We should not get this and if we do it would
    # likely indicate a problem with the implementation of the agent.
    #
    # 413 Request Entity Too Large - Where the request content was too
    # large. The limits on number of nodes in slow transaction traces
    # should in general prevent this, but not everything has size limits
    # and so rogue data could still blow things out. The same data are not
    # going to work later on in a subsequent request, even if aggregated
    # with other data, so we need to log the details and then flag that
    # data should be thrown away.
    #
    # 415 Unsupported Media Type - This occurs when the JSON which was
    # sent can't be decoded by the data collector. If this is a true
    # problem with the JSON formatting, then sending again, even if
    # aggregated with other data, may not work, so we need to log the
    # details and then flag that data should be thrown away.
    #
    # 503 Service Unavailable - This occurs when the data collector, or core
    # application is being restarted and not in state to be able to
    # accept requests. It should be a transient issue so should be able
    # to retain data and try again.

    internal_metric('Supportability/Python/Collector/Output/Bytes/'
            '%s' % method, len(data))

    # If audit logging is enabled, log the requests details.

    log_id = _log_request(url, params, headers, data)

    connection = connection_type(proxies)

    try:
        # The timeout value in the requests module is only on
        # the initial connection and doesn't apply to how long
        # it takes to get back a response.

        cert_loc = certs.where()

        if settings.debug.disable_certificate_validation:
            cert_loc = False

        timeout = settings.agent_limits.data_collector_timeout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            r = session.post(url, params=params, headers=headers,
                    proxies=proxies, timeout=timeout, data=data,
                    verify=cert_loc)

        # Read the content now so we can force close the socket
        # connection if this is a transient session as quickly
        # as possible.

        content = r.content

    except requests.RequestException:
        exc_type, message = sys.exc_info()[:2]

        internal_metric('Supportability/Python/Collector/Failures', 1)
        internal_metric('Supportability/Python/Collector/Failures/'
                '%s' % connection, 1)

        internal_metric('Supportability/Python/Collector/Exception/'
                '%s' % callable_name(exc_type), 1)

        if not settings.proxy_host or not settings.proxy_port:
            _logger.warning('Data collector is not contactable. This can be '
                    'because of a network issue or because of the data '
                    'collector being restarted. In the event that contact '
                    'cannot be made after a period of time then please '
                    'report this problem to New Relic support for further '
                    'investigation. The exception raised was %r.', message)

        else:
            _logger.warning('Data collector is not contactable via the proxy '
                    'host %r on port %r with proxy user of %r. This can be '
                    'because of a network issue or because of the data '
                    'collector being restarted. In the event that contact '
                    'cannot be made after a period of time then please '
                    'report this problem to New Relic support for further '
                    'investigation. The exception raised was %r.',
                    settings.proxy_host, settings.proxy_port,
                    settings.proxy_user, message)

        raise RetryDataForRequest(str(message))

    except Exception:
        # Any unexpected exception will be caught by higher layer, but
        # still attempt to log a metric here just in case agent run
        # doesn't get shutdown as a result of the exception.

        exc_type = sys.exc_info()[0]

        internal_metric('Supportability/Python/Collector/Failures', 1)
        internal_metric('Supportability/Python/Collector/Failures/'
                '%s' % connection, 1)

        internal_metric('Supportability/Python/Collector/Exception/'
                '%s' % callable_name(exc_type), 1)

        raise

    finally:
        if auto_close_session:
            session.close()
            session = None

    if r.status_code != 200:
        _logger.warning('Received a non 200 HTTP response from the data '
                'collector where url=%r, method=%r, license_key=%r, '
                'agent_run_id=%r, params=%r, headers=%r, status_code=%r '
                'and content=%r.', url, method, license_key, agent_run_id,
                params, headers, r.status_code, content)

        internal_metric('Supportability/Python/Collector/Failures', 1)
        internal_metric('Supportability/Python/Collector/Failures/'
                '%s' % connection, 1)

        internal_metric('Supportability/Python/Collector/HTTPError/%d'
                % r.status_code, 1)

    if r.status_code == 400:
        _logger.error('Data collector is indicating that a bad '
                'request has been submitted for url %r, headers of %r, '
                'params of %r and payload of %r. Please report this '
                'problem to New Relic support.', url, headers, params,
                payload)

        raise DiscardDataForRequest()

    elif r.status_code == 408:
        _logger.warning('Data collector is indicating that a timeout '
                'has occurred for url %r, headers of %r, '
                'params of %r and payload of %r. If this keeps occurring on a '
                'regular basis, Please report this problem to New Relic '
                'support.', url, headers, params,
                payload)

        raise RetryDataForRequest()

    elif r.status_code == 413:
        _logger.warning('Data collector is indicating that a request for '
                'method %r was received where the request content size '
                'was over the maximum allowed size limit. The length of '
                'the request content was %d. If this keeps occurring on a '
                'regular basis, please report this problem to New Relic '
                'support for further investigation.', method, len(data))

        raise DiscardDataForRequest()

    elif r.status_code == 415:
        _logger.warning('Data collector is indicating that it was sent '
                'malformed JSON data for method %r. If this keeps occurring '
                'on a regular basis, please report this problem to New '
                'Relic support for further investigation.', method)

        if settings.debug.log_malformed_json_data:
            if headers['Content-Encoding'] == 'deflate':
                data = zlib.decompress(data)

            _logger.info('JSON data which was rejected by the data '
                    'collector was %r.', data)

        raise DiscardDataForRequest(content)

    elif r.status_code == 503:
        _logger.warning('Data collector is unavailable. This can be a '
                'transient issue because of the data collector or our '
                'core application being restarted. If the issue persists '
                'it can also be indicative of a problem with our servers. '
                'In the event that availability of our servers is not '
                'restored after a period of time then please report this '
                'problem to New Relic support for further investigation.')

        raise ServerIsUnavailable()

    elif r.status_code != 200:
        if not settings.proxy_host or not settings.proxy_port:
            _logger.warning('An unexpected HTTP response was received from '
                    'the data collector of %r for method %r. The payload for '
                    'the request was %r. If this issue persists then please '
                    'report this problem to New Relic support for further '
                    'investigation.', r.status_code, method, payload)

        else:
            _logger.warning('An unexpected HTTP response was received from '
                    'the data collector of %r for method %r while connecting '
                    'via proxy host %r on port %r with proxy user of %r. '
                    'The payload for the request was %r. If this issue '
                    'persists then please report this problem to New Relic '
                    'support for further investigation.', r.status_code,
                    method, settings.proxy_host, settings.proxy_port,
                    settings.proxy_user, payload)

        raise DiscardDataForRequest()

    # Log details of response payload for debugging. Use the JSON
    # encoded value so we know what was the original encoded value.

    duration = time.time() - start

    if settings.debug.log_data_collector_payloads:
        _logger.debug('Valid response from data collector after %.2f '
                'seconds with content=%r.', duration, content)
    elif settings.debug.log_data_collector_calls:
        _logger.debug('Valid response from data collector after %.2f '
                'seconds.', duration)

    # If we got this far we should have a legitimate response from the
    # data collector. The response is JSON so need to decode it.

    try:
        if six.PY3:
            content = content.decode('UTF-8')

        result = json_decode(content)

    except Exception:
        _logger.exception('Error decoding data for JSON payload for '
                'method %r with payload of %r. Please report this problem '
                'to New Relic support.', method, content)

        if settings.debug.log_malformed_json_data:
            _logger.info('JSON data received from data collector which '
                    'could not be decoded was %r.', content)

        raise DiscardDataForRequest(str(sys.exc_info()[1]))

    # The decoded JSON can be either for a successful response or an
    # error. A successful response has a 'return_value' element and on
    # error an 'exception' element.

    if log_id is not None:
        _log_response(log_id, result)

    if 'return_value' in result:
        return result['return_value']

    error_type = result['exception']['error_type']
    message = result['exception']['message']

    # Now need to check for server side exceptions. The following
    # exceptions can occur for abnormal events.

    _logger.warning('Received an exception from the data collector where '
            'url=%r, method=%r, license_key=%r, agent_run_id=%r, params=%r, '
            'headers=%r, error_type=%r and message=%r', url, method,
            license_key, agent_run_id, params, headers, error_type,
            message)

    # Technically most server side errors will result in the active
    # agent run being abandoned and so there is no point trying to
    # create a metric for when they occur. Leave this here though to at
    # least log a metric for the case where a completely unexpected
    # server error response is received and the agent run does manage to
    # continue and further requests don't just keep failing. Since we do
    # not even expect the metric to be retained, use the original error
    # type as sent.

    internal_metric('Supportability/Python/Collector/ServerError/'
            '%s' % error_type, 1)

    if error_type == 'NewRelic::Agent::LicenseException':
        _logger.error('Data collector is indicating that an incorrect '
                'license key has been supplied by the agent. The value '
                'which was used by the agent is %r. Please correct any '
                'problem with the license key or report this problem to '
                'New Relic support.', license_key)

        raise DiscardDataForRequest(message)

    elif error_type == 'NewRelic::Agent::PostTooBigException':
        # As far as we know we should never see this type of server side
        # error as the JSON API should always send back an HTTP 413
        # error response instead.

        internal_metric('Supportability/Python/Collector/Failures', 1)
        internal_metric('Supportability/Python/Collector/Failures/'
                '%s' % connection, 1)

        _logger.warning('Core application is indicating that a request for '
                'method %r was received where the request content size '
                'was over the maximum allowed size limit. The length of '
                'the request content was %d. If this keeps occurring on a '
                'regular basis, please report this problem to New Relic '
                'support for further investigation.', method, len(data))

        raise DiscardDataForRequest(message)

    # Server side exceptions are also used to inform the agent to
    # perform certain actions such as restart when server side
    # configuration has changed for this application or when agent is
    # being disabled remotely for some reason.

    if error_type == 'NewRelic::Agent::ForceRestartException':
        _logger.info('An automatic internal agent restart has been '
                'requested by the data collector for the application '
                'where the agent run was %r. The reason given for the '
                'forced restart is %r.', agent_run_id, message)

        raise ForceAgentRestart(message)

    elif error_type == 'NewRelic::Agent::ForceDisconnectException':
        _logger.critical('Disconnection of the agent has been requested by '
                'the data collector for the application where the '
                'agent run was %r. The reason given for the forced '
                'disconnection is %r. Please contact New Relic support '
                'for further information.', agent_run_id, message)

        raise ForceAgentDisconnect(message)

    # We received an unexpected server side error and we don't know what
    # to do with it. Ignoring PostTooBigException which we expect that we
    # should never receive, unexpected server side errors are the only
    # ones we record a failure metric for as other server side errors
    # are really commands to have the agent do something.

    internal_metric('Supportability/Python/Collector/Failures', 1)
    internal_metric('Supportability/Python/Collector/Failures/'
            '%s' % connection, 1)

    _logger.warning('An unexpected server error was received from the '
            'data collector for method %r with payload of %r. The error '
            'was of type %r with message %r. If this issue persists '
            'then please report this problem to New Relic support for '
            'further investigation.', method, payload, error_type, message)

    raise DiscardDataForRequest(message)


def apply_high_security_mode_fixups(local_settings, server_settings):
    # When High Security Mode is True in local_settings, then all
    # security related settings should be removed from server_settings.
    # That way, when the local and server side configuration settings
    # are merged, the local security settings will not get overwritten
    # by the server side configuration settings.
    #
    # Note that security settings we may want to remove can appear at
    # both the top level of the server settings, but also nested within
    # the 'agent_config' sub dictionary. Those settings at the top level
    # represent how the settings were previously overridden for high
    # security mode. Those in 'agent_config' correspond to server side
    # configuration as set by the user.

    if not local_settings['high_security']:
        return server_settings

    # Remove top-level 'high_security' setting. This will only exist
    # if it had been enabled server side.

    if 'high_security' in server_settings:
        del server_settings['high_security']

    # Remove individual security settings from top level of configuration
    # settings.

    security_settings = ('capture_params', 'transaction_tracer.record_sql',
            'strip_exception_messages.enabled',
            'custom_insights_events.enabled')

    for setting in security_settings:
        if setting in server_settings:
            del server_settings[setting]

    # When server side configuration is disabled, there will be no
    # agent_config value in server_settings, so no more fix-ups
    # are required.

    if 'agent_config' not in server_settings:
        return server_settings

    # Remove individual security settings from agent server side
    # configuration settings.

    agent_config = server_settings['agent_config']

    for setting in security_settings:
        if setting in agent_config:
            del server_settings['agent_config'][setting]

            _logger.info('Ignoring server side configuration setting for '
                    '%r, because High Security Mode has been activated. '
                    'Using local setting %s=%r.', setting, setting,
                    local_settings[setting])

    return server_settings


class ApplicationSession(object):

    """ Class which encapsulates communication with the data collector
    once the initial registration has been done.

    """

    def __init__(self, collector_url, license_key, configuration):
        self.collector_url = collector_url
        self.license_key = license_key
        self.configuration = configuration
        self.agent_run_id = configuration.agent_run_id

        self._requests_session = None

    @property
    def requests_session(self):
        if self._requests_session is None:
            self._requests_session = requests.session()
        return self._requests_session

    def close_connection(self):
        if self._requests_session:
            self._requests_session.close()
        self._requests_session = None

    @classmethod
    def send_request(cls, session, url, method, license_key,
            agent_run_id=None, payload=()):
        return send_request(session, url, method, license_key,
            agent_run_id, payload)

    def agent_settings(self, settings):
        """Called to report up agent settings after registration.

        """

        payload = (settings,)

        return self.send_request(self.requests_session, self.collector_url,
                'agent_settings', self.license_key, self.agent_run_id,
                payload)

    def shutdown_session(self):
        """Called to perform orderly deregistration of agent run against
        the data collector, rather than simply dropping the connection and
        relying on data collector to surmise that agent run is finished
        due to no more data being reported.

        """

        _logger.debug('Connecting to data collector to terminate session '
                'for agent run %r.', self.agent_run_id)

        result = self.send_request(self.requests_session, self.collector_url,
                'shutdown', self.license_key, self.agent_run_id)

        _logger.info('Successfully shutdown New Relic Python agent '
                'where app_name=%r, pid=%r, and agent_run_id=%r',
                self.configuration.app_name, os.getpid(),
                self.agent_run_id)

        return result

    def send_metric_data(self, start_time, end_time, metric_data):
        """Called to submit metric data for specified period of time.
        Time values are seconds since UNIX epoch as returned by the
        time.time() function. The metric data should be iterable of
        specific metrics.

        """

        payload = (self.agent_run_id, start_time, end_time, metric_data)

        return self.send_request(self.requests_session, self.collector_url,
                'metric_data', self.license_key, self.agent_run_id, payload)

    def send_errors(self, errors):
        """Called to submit errors. The errors should be an iterable
        of individual error details.

        NOTE Although the details for each error carries a timestamp,
        the data collector appears to ignore it and overrides it with
        the timestamp that the data is received by the data collector.

        """

        if not errors:
            return

        payload = (self.agent_run_id, errors)

        return self.send_request(self.requests_session, self.collector_url,
                'error_data', self.license_key, self.agent_run_id, payload)

    def send_transaction_traces(self, transaction_traces):
        """Called to submit transaction traces. The transaction traces
        should be an iterable of individual traces.

        NOTE Although multiple traces could be supplied, the agent is
        currently only reporting on the slowest transaction in the most
        recent period being reported on.

        """

        if not transaction_traces:
            return

        payload = (self.agent_run_id, transaction_traces)

        return self.send_request(self.requests_session, self.collector_url,
                'transaction_sample_data', self.license_key,
                self.agent_run_id, payload)

    def send_profile_data(self, profile_data):
        """Called to submit Profile Data.
        """

        if not profile_data:
            return

        payload = (self.agent_run_id, profile_data)

        return self.send_request(self.requests_session, self.collector_url,
                'profile_data', self.license_key,
                self.agent_run_id, payload)

    def send_sql_traces(self, sql_traces):
        """Called to sub SQL traces. The SQL traces should be an
        iterable of individual SQL details.

        NOTE The agent currently only reports on the 10 slowest SQL
        queries in the most recent period being reported on.

        """

        if not sql_traces:
            return

        payload = (sql_traces,)

        return self.send_request(self.requests_session, self.collector_url,
                'sql_trace_data', self.license_key, self.agent_run_id,
                payload)

    def get_agent_commands(self):
        """Receive agent commands from the data collector.

        """

        payload = (self.agent_run_id,)

        return self.send_request(self.requests_session, self.collector_url,
                'get_agent_commands', self.license_key, self.agent_run_id,
                payload)

    def send_agent_command_results(self, cmd_results):
        """Acknowledge the receipt of an agent command.

        """

        payload = (self.agent_run_id, cmd_results)

        return self.send_request(self.requests_session, self.collector_url,
                'agent_command_results', self.license_key, self.agent_run_id,
                payload)

    def get_xray_metadata(self, xray_id):
        """Receive xray metadata from the data collector.

        """

        payload = (self.agent_run_id, xray_id)

        return self.send_request(self.requests_session, self.collector_url,
                'get_xray_metadata', self.license_key, self.agent_run_id,
                payload)

    def send_transaction_events(self, sample_set):
        """Called to submit sample set for analytics.

        """

        payload = (self.agent_run_id, sample_set)

        return self.send_request(self.requests_session, self.collector_url,
                'analytic_event_data', self.license_key, self.agent_run_id,
                payload)

    def send_error_events(self, sampling_info, error_data):
        """Called to submit sample set for error events.

        """

        payload = (self.agent_run_id, sampling_info, error_data)

        return self.send_request(self.requests_session, self.collector_url,
                'error_event_data', self.license_key, self.agent_run_id,
                payload)

    def send_custom_events(self, sampling_info, custom_event_data):
        """Called to submit sample set for custom events.

        """

        payload = (self.agent_run_id, sampling_info, custom_event_data)

        return self.send_request(self.requests_session, self.collector_url,
                'custom_event_data', self.license_key, self.agent_run_id,
                payload)

    @classmethod
    def create_session(cls, license_key, app_name, linked_applications,
            environment, settings):

        """Registers the agent for the specified application with the data
        collector and retrieves the server side configuration. Returns a
        session object if successful through which subsequent calls to the
        data collector are made. If unsuccessful then None is returned.

        """

        start = time.time()

        # If no license key provided in the call, fall back to using that
        # from the agent configuration file or environment variables.
        # Flag an error if the result still seems invalid.

        if not license_key:
            license_key = global_settings().license_key

        if not license_key:
            _logger.error('A valid account license key cannot be found. '
                'Has a license key been specified in the agent configuration '
                'file or via the NEW_RELIC_LICENSE_KEY environment variable?')

        try:
            # First need to ask the primary data collector which of the many
            # data collector instances we should use for this agent run.

            _logger.debug('Connecting to data collector to register agent '
                    'with license_key=%r, app_name=%r, '
                    'linked_applications=%r, environment=%r and settings=%r.',
                    license_key, app_name, linked_applications, environment,
                    settings)

            url = collector_url()

            redirect_host = cls.send_request(None, url,
                    'get_redirect_host', license_key)

            # Then we perform a connect to the actual data collector host
            # we need to use. All communications after this point should go
            # to the secondary data collector.
            #
            # We use the global requests session object for now as harvests
            # for different applications are all done in turn. If multiple
            # threads are used we will need to change this. We currently force
            # session objects to maintain only a single connection to ensure
            # that keep alive is effective.

            payload = cls._create_connect_payload(app_name,
                    linked_applications, environment, settings)

            url = collector_url(redirect_host)

            server_config = cls.send_request(None, url, 'connect',
                    license_key, None, payload)

            # Apply High Security Mode to server_config, so the local
            # security settings won't get overwritten when we overlay
            # the server settings on top of them.

            server_config = apply_high_security_mode_fixups(settings,
                    server_config)

            # The agent configuration for the application in constructed
            # by taking a snapshot of the locally constructed
            # configuration and overlaying it with that from the server,
            # as well as creating the attribute filter.

            application_config = finalize_application_settings(server_config)

        except NetworkInterfaceException:
            # The reason for errors of this type have already been logged.
            # No matter what the error we just pass back None. The upper
            # layer needs to count how many success times this has failed
            # and escalate things with a more sever error.

            pass

        except Exception:
            # Any other errors are going to be unexpected and likely will
            # indicate an issue with the implementation of the agent.

            _logger.exception('Unexpected exception when attempting to '
                    'register the agent with the data collector. Please '
                    'report this problem to New Relic support for further '
                    'investigation.')

            pass

        else:
            # Everything is fine so we create the session object through which
            # subsequent communication with data collector will be done.

            session = cls(url, license_key, application_config)

            duration = time.time() - start

            # Log successful agent registration and any server side messages.

            _logger.info('Successfully registered New Relic Python agent '
                    'where app_name=%r, pid=%r, redirect_host=%r and '
                    'agent_run_id=%r, in %.2f seconds.', app_name,
                    os.getpid(), redirect_host, session.agent_run_id,
                    duration)

            if getattr(application_config, 'high_security', False):
                _logger.info('High Security Mode is being applied to all '
                        'communications between the agent and the data '
                        'collector for this session.')

            logger_func_mapping = {
                'ERROR': _logger.error,
                'WARN': _logger.warning,
                'INFO': _logger.info,
                'VERBOSE': _logger.debug,
            }

            if 'messages' in server_config:
                for item in server_config['messages']:
                    message = item['message']
                    if six.PY2 and hasattr(message, 'encode'):
                        message = message.encode('utf-8')
                    level = item['level']
                    logger_func = logger_func_mapping.get(level, None)
                    if logger_func:
                        logger_func('%s', message)

            return session

    @staticmethod
    def _create_connect_payload(app_name, linked_applications, environment,
            settings):
        # Creates the payload to send on the initial connection to the
        # data collector.

        app_names = [app_name] + linked_applications

        hostname = system_info.gethostname(settings['heroku.use_dyno_names'],
                settings['heroku.dyno_name_prefixes_to_shorten'])

        connect_settings = {}
        connect_settings['browser_monitoring.loader'] = (
            settings['browser_monitoring.loader'])
        connect_settings['browser_monitoring.debug'] = (
            settings['browser_monitoring.debug'])

        security_settings = {}
        security_settings['capture_params'] = settings['capture_params']
        security_settings['transaction_tracer'] = {}
        security_settings['transaction_tracer']['record_sql'] = (
            settings['transaction_tracer.record_sql'])

        utilization_settings = {}
        # metadata_version corresponds to the utilization spec being used.
        utilization_settings['metadata_version'] = 3
        utilization_settings['logical_processors'] = logical_processor_count()
        utilization_settings['total_ram_mib'] = total_physical_memory()
        utilization_settings['hostname'] = hostname
        boot_id = BootIdUtilization.detect()
        if boot_id:
            utilization_settings['boot_id'] = boot_id

        utilization_conf = {}
        logical_processor_conf = settings.get('utilization.logical_processors')
        total_ram_conf = settings.get('utilization.total_ram_mib')
        hostname_conf = settings.get('utilization.billing_hostname')
        if logical_processor_conf:
            utilization_conf['logical_processors'] = logical_processor_conf
        if total_ram_conf:
            utilization_conf['total_ram_mib'] = total_ram_conf
        if hostname_conf:
            utilization_conf['hostname'] = hostname_conf
        if utilization_conf:
            utilization_settings['config'] = utilization_conf

        vendors = []
        if settings['utilization.detect_aws']:
            vendors.append(AWSUtilization)
        if settings['utilization.detect_pcf']:
            vendors.append(PCFUtilization)
        if settings['utilization.detect_gcp']:
            vendors.append(GCPUtilization)
        if settings['utilization.detect_azure']:
            vendors.append(AzureUtilization)

        utilization_vendor_settings = {}
        for vendor in vendors:
            metadata = vendor.detect()
            if metadata:
                utilization_vendor_settings[vendor.VENDOR_NAME] = metadata
                break

        if settings['utilization.detect_docker']:
            docker = DockerUtilization.detect()
            if docker:
                utilization_vendor_settings['docker'] = docker

        if utilization_vendor_settings:
            utilization_settings['vendors'] = utilization_vendor_settings

        display_host = settings['process_host.display_name']
        if display_host is None:
            display_host = hostname

        local_config = {
                'host': hostname,
                'pid': os.getpid(),
                'language': 'python',
                'app_name': app_names,
                'identifier': ','.join(app_names),
                'agent_version': version,
                'environment': environment,
                'settings': connect_settings,
                'security_settings': security_settings,
                'utilization': utilization_settings,
                'high_security': settings['high_security'],
                'labels': settings['labels'],
                'display_host': display_host,
        }
        return (local_config,)


_developer_mode_responses = {
    'get_redirect_host': u'fake-collector.newrelic.com',

    'agent_settings': [],

    'connect': {
        u'js_agent_loader': u'<!-- NREUM -->',
        u'js_agent_file': u'fake-js-agent.newrelic.com/nr-0.min.js',
        u'browser_key': u'1234567890',
        u'browser_monitoring.loader_version': u'0',
        u'beacon': u'fake-beacon.newrelic.com',
        u'error_beacon': u'fake-jserror.newrelic.com',
        u'apdex_t': 0.5,
        u'encoding_key': u'1111111111111111111111111111111111111111',
        u'agent_run_id': 1234567,
        u'product_level': 50,
        u'trusted_account_ids': [12345],
        u'url_rules': [],
        u'collect_errors': True,
        u'cross_process_id': u'12345#67890',
        u'messages': [{u'message': u'Reporting to fake collector',
            u'level': u'INFO'}],
        u'sampling_rate': 0,
        u'collect_traces': True,
        u'data_report_period': 60
    },

    'metric_data': [],

    'get_agent_commands': [],

    'error_data': None,

    'transaction_sample_data': None,

    'sql_trace_data': None,

    'analytic_event_data': None,

    'error_event_data': None,

    'custom_event_data': None,

    'shutdown': None,
}


class DeveloperModeSession(ApplicationSession):

    @classmethod
    def send_request(cls, session, url, method, license_key,
            agent_run_id=None, payload=()):

        assert method in _developer_mode_responses

        # Create fake details for the request being made so that we
        # can use the same audit logging functionality.

        params = {}
        headers = {}

        if not license_key:
            license_key = 'NO LICENSE KEY WAS SET IN AGENT CONFIGURATION'

        params['method'] = method
        params['license_key'] = license_key
        params['protocol_version'] = '14'
        params['marshal_format'] = 'json'

        if agent_run_id:
            params['run_id'] = str(agent_run_id)

        headers['User-Agent'] = USER_AGENT
        headers['Content-Encoding'] = 'identity'

        data = json_encode(payload)

        log_id = _log_request(url, params, headers, data)

        # Now create the fake responses so the agent still runs okay.

        result = _developer_mode_responses[method]

        if method == 'connect':
            settings = global_settings()
            if settings.high_security:
                result = dict(result)
                result['high_security'] = True

        # Even though they are always fake responses, still log them.

        if log_id is not None:
            _log_response(log_id, dict(return_value=result))

        return result


def create_session(license_key, app_name, linked_applications,
        environment, settings):

    _global_settings = global_settings()

    if _global_settings.developer_mode:
        session = DeveloperModeSession.create_session(license_key, app_name,
                linked_applications, environment, settings)
    else:
        session = ApplicationSession.create_session(license_key, app_name,
                linked_applications, environment, settings)

    # When session creation is unsuccessful None is returned. We need to catch
    # that and return None. Session creation can fail if data-collector is down
    # or if the configuration is wrong, such as having the capture_params true
    # in high security mode.

    if session is None:
        return None

    # We now need to send up the final merged configuration using the
    # agent_settings() method. We must make sure we pass the
    # configuration through global_settings_dump() to strip/mask any
    # sensitive settings. We also convert values which are strings or
    # numerics to strings before sending to avoid problems with UI
    # interpreting the values strangely if sent as native types.

    application_settings = global_settings_dump(session.configuration)

    for key, value in list(six.iteritems(application_settings)):
        if not isinstance(key, six.string_types):
            del application_settings[key]

        if (not isinstance(value, six.string_types) and
                not isinstance(value, float) and
                not isinstance(value, six.integer_types)):
            application_settings[key] = repr(value)

    try:
        session.agent_settings(application_settings)

    except NetworkInterfaceException:
        # The reason for errors of this type have already been logged.
        # No matter what the error we just pass back None. The upper
        # layer will deal with it not being successful.

        _logger.warning('Agent registration failed due to error in '
                'uploading agent settings. Registration should retry '
                'automatically.')

        pass

    except Exception:
        # Any other errors are going to be unexpected and likely will
        # indicate an issue with the implementation of the agent.

        _logger.exception('Unexpected exception when attempting to '
                'update agent settings with the data collector. Please '
                'report this problem to New Relic support for further '
                'investigation.')

        _logger.warning('Agent registration failed due to error in '
                'uploading agent settings. Registration should retry '
                'automatically.')

        pass

    else:
        return session
