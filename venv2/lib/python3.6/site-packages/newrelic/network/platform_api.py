import logging
import time
import zlib
import sys
import socket
import os

from newrelic.packages import six

from newrelic.packages import requests

from newrelic import version as agent_version

from newrelic.network.addresses import platform_url, proxy_details
from newrelic.network.exceptions import (NetworkInterfaceException,
        ForceAgentRestart, ForceAgentDisconnect, DiscardDataForRequest,
        RetryDataForRequest, ServerIsUnavailable)

from newrelic.common import certs
from newrelic.common.encoding_utils import json_encode, json_decode

_logger = logging.getLogger(__name__)

# User agent string that must be used in all requests. The data collector
# does not rely on this, but is used to target specific agents if there
# is a problem with data collector handling requests.

USER_AGENT = 'NewRelic-PythonAgent/%s (Python %s %s)' % (
         agent_version, sys.version.split()[0], sys.platform)

# Platform agent collector interface.

class PlatformInterface(object):

    def __init__(self, license_key, host='platform-api.newrelic.com',
            port=None, ssl=True, timeout=30.0, proxy_host=None,
            proxy_port=None, proxy_user=None, proxy_pass=None):

        self.license_key = license_key

        self.host = host
        self.port = port
        self.ssl = ssl

        self.timeout = timeout

        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass

    def send_request(self, url, proxies, session, payload=()):
        """Constructs and sends a request to the data collector."""

        headers = {}
        config = {}

        start = time.time()

        # Validate that the license key was actually set and if not replace
        # it with a string which makes it more obvious it was not set.

        license_key = self.license_key

        if not self.license_key:
            license_key = 'NO LICENSE KEY WAS SET IN AGENT CONFIGURATION'

        headers['User-Agent'] = USER_AGENT
        headers['Content-Encoding'] = 'identity'
        headers['X-License-Key'] = license_key

        # At this time we use JSON content encoding for the data being
        # sent. If an error does occur when encoding the JSON, then it
        # isn't likely going to work later on in a subsequent request
        # with same data, even if aggregated with other data, so we need
        # to log the details and then flag that data should be thrown
        # away. Don't mind being noisy in the the log in this situation
        # as it would indicate a problem with the implementation of the
        # agent.

        try:
            data = json_encode(payload)

        except Exception as exc:
            _logger.error('Error encoding data for JSON payload '
                    'with payload of %r. Exception which occurred was %r. '
                    'Please report this problem to New Relic support.',
                    payload, exc)

            raise DiscardDataForRequest(str(exc))

        # Log details of call and/or payload for debugging. Use the JSON
        # encoded value so know that what is encoded is correct.

        _logger.debug('Calling data collector to report custom metrics '
                'with payload=%r.', data)

        # Compress the serialized JSON being sent as content if over 64KiB
        # in size.

        if len(data) > 64*1024:
            headers['Content-Encoding'] = 'deflate'
            data = zlib.compress(six.b(data))

        # If there is no requests session object provided for making
        # requests create one now. We want to close this as soon as we
        # are done with it.

        auto_close_session = False

        if not session:
            session = requests.session()
            auto_close_session = True

        # The 'requests' library can raise a number of exception derived
        # from 'RequestException' before we even manage to get a connection
        # to the data collector. The data collector can the generate a
        # number of different types of HTTP errors for requests.

        try:
            cert_loc = certs.where()

            r = session.post(url, headers=headers, proxies=proxies,
                    timeout=self.timeout, data=data, verify=cert_loc)

            # Read the content now so we can force close the socket
            # connection if this is a transient session as quickly
            # as possible.

            content = r.content

        except requests.RequestException as exc:
            if not self.proxy_host or not self.proxy_port:
                _logger.warning('Data collector is not contactable. This can '
                        'be because of a network issue or because of the data '
                        'collector being restarted. In the event that contact '
                        'cannot be made after a period of time then please '
                        'report this problem to New Relic support for further '
                        'investigation. The error raised was %r.', exc)
            else:
                _logger.warning('Data collector is not contactable via the '
                        'proxy host %r on port %r with proxy user of %r. This '
                        'can be because of a network issue or because of the '
                        'data collector being restarted. In the event that '
                        'contact cannot be made after a period of time then '
                        'please report this problem to New Relic support for '
                        'further investigation. The error raised was %r.',
                        self.proxy_host, self.proxy_port, self.proxy_user, exc)

            raise RetryDataForRequest(str(exc))

        finally:
            if auto_close_session:
                session.close()
                session = None

        if r.status_code != 200:
            _logger.debug('Received a non 200 HTTP response from the data '
                    'collector where url=%r, license_key=%r, headers=%r, '
                    'status_code=%r and content=%r.', url, license_key,
                    headers, r.status_code, content)

        if r.status_code == 400:
            if headers['Content-Encoding'] == 'deflate':
                data = zlib.decompress(data)

            _logger.error('Data collector is indicating that a bad '
                    'request has been submitted for url %r, headers of %r '
                    'and payload of %r with response of %r. Please report '
                    'this problem to New Relic support.', url, headers, data,
                    content)

            raise DiscardDataForRequest()

        elif r.status_code == 403:
            _logger.error('Data collector is indicating that the license '
                    'key %r is not valid.', license_key)

            raise DiscardDataForRequest()

        elif r.status_code == 413:
            _logger.warning('Data collector is indicating that a request '
                    'was received where the request content size '
                    'was over the maximum allowed size limit. The length of '
                    'the request content was %d. If this keeps occurring on a '
                    'regular basis, please report this problem to New Relic '
                    'support for further investigation.', len(data))

            raise DiscardDataForRequest()

        elif r.status_code in  (503, 504):
            _logger.warning('Data collector is unavailable. This can be a '
                    'transient issue because of the data collector or our '
                    'core application being restarted. If the issue persists '
                    'it can also be indicative of a problem with our servers. '
                    'In the event that availability of our servers is not '
                    'restored after a period of time then please report this '
                    'problem to New Relic support for further investigation.')

            raise ServerIsUnavailable()

        elif r.status_code != 200:
            if not self.proxy_host or not self.proxy_port:
                _logger.warning('An unexpected HTTP response was received '
                        'from the data collector of %r. The payload for '
                        'the request was %r. If this issue persists then '
                        'please report this problem to New Relic support '
                        'for further investigation.', r.status_code, payload)
            else:
                _logger.warning('An unexpected HTTP response was received '
                        'from the data collector of %r while connecting '
                        'via proxy host %r on port %r with proxy user of %r. '
                        'The payload for the request was %r. If this issue '
                        'persists then please report this problem to New '
                        'Relic support for further investigation.',
                        r.status_code, self.proxy_host, self.proxy_port,
                        self.proxy_user, payload)

            raise DiscardDataForRequest()

        # Log details of response payload for debugging. Use the JSON
        # encoded value so know that what original encoded value was.

        duration = time.time() - start

        _logger.debug('Valid response from data collector after %.2f '
                'seconds with content=%r.', duration, content)

        # If we got this far we should have a legitimate response from the
        # data collector. The response is JSON so need to decode it.
        # Everything will come back as Unicode.

        try:
            if six.PY3:
                content = content.decode('UTF-8')

            result = json_decode(content)

        except Exception as exc:
            _logger.error('Error decoding data for JSON payload '
                    'with payload of %r. Exception which occurred was %r. '
                    'Please report this problem to New Relic support.',
                    content, exc)

            raise DiscardDataForRequest(str(exc))

        # The decoded JSON can be either for a successful response or an
        # error. A successful response has a 'return_value' element and an
        # error an 'exception' element.

        if 'status' in result:
            return result['status']

        error_message = result['error']

        # Now need to check for server side exceptions. The following
        # exceptions can occur for abnormal events.

        _logger.debug('Received an exception from the data collector where '
                'url=%r, license_key=%r, headers=%r and error_message=%r. ',
                url, license_key, headers, error_message)

        raise DiscardDataForRequest(error_message)

    def create_session(self):
        url = platform_url(self.host, self.port, self.ssl)

        proxies = proxy_details(None, self.proxy_host, self.proxy_port,
                self.proxy_user, self.proxy_pass)

        return PlatformSession(self, url, proxies)

class PlatformSession(object):

    def __init__(self, interface, platform_url, http_proxies):
        self._interface = interface
        self._platform_url = platform_url
        self._http_proxies = http_proxies
        self._requests_session_object = None

    @property
    def _requests_session(self):
        if self._requests_session_object is None:
            self._requests_session_object = requests.session()
        return self._requests_session_object

    def close_connection(self):
        if self._requests_session_object:
            self._requests_session_object.close()
        self._requests_session_object = None

    def send_metric_data(self, name, guid, version, duration, metrics):
        agent = {}
        agent['host'] = socket.gethostname()
        agent['pid'] = os.getpid()
        agent['version'] = version or '0.0.0.'

        component = {}
        component['name'] = name
        component['guid'] = guid
        component['duration'] = duration
        component['metrics'] = metrics

        payload = {}
        payload['agent'] = agent
        payload['components'] = [component]

        return self._interface.send_request(self._platform_url,
                self._http_proxies, self._requests_session, payload)
