import sys
import cgi
import time
import string
import logging
import functools

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from newrelic.api.application import application_instance
from newrelic.api.transaction import Transaction, current_transaction
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.html_insertion import insert_html_snippet, verify_body_exists

from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object, FunctionWrapper
from newrelic.common.encoding_utils import (obfuscate, deobfuscate,
        json_encode, json_decode)

from newrelic.core.attribute_filter import DST_BROWSER_MONITORING

from newrelic.packages import six

_logger = logging.getLogger(__name__)

_js_agent_header_fragment = '<script type="text/javascript">%s</script>'
_js_agent_footer_fragment = '<script type="text/javascript">'\
                            'window.NREUM||(NREUM={});NREUM.info=%s</script>'

# Seconds since epoch for Jan 1 2000
JAN_1_2000 = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, 0))


def _lookup_environ_setting(environ, name, default=False):
    flag = environ.get(name, default)
    if default is None or default:
        try:
            flag = not flag.lower() in ['off', 'false', '0']
        except AttributeError:
            pass
    else:
        try:
            flag = flag.lower() in ['on', 'true', '1']
        except AttributeError:
            pass
    return flag


def _parse_synthetics_header(header):
    # Return a dictionary of values from Synthetics header
    # Returns empty dict, if version is not supported.

    synthetics = {}
    version = None

    if len(header) > 0:
        version = int(header[0])

    if version == 1:
        synthetics['version'] = version
        synthetics['account_id'] = int(header[1])
        synthetics['resource_id'] = header[2]
        synthetics['job_id'] = header[3]
        synthetics['monitor_id'] = header[4]

    return synthetics


def _remove_query_string(url):
    out = urlparse.urlsplit(url)
    return urlparse.urlunsplit((out.scheme, out.netloc, out.path, '', ''))


def _is_websocket(environ):
    return environ.get('HTTP_UPGRADE', '').lower() == 'websocket'


class WebTransaction(Transaction):

    report_unicode_error = True

    def __init__(self, application, environ):

        # The web transaction can be enabled/disabled by
        # the value of the variable "newrelic.enabled"
        # in the WSGI environ dictionary. We need to check
        # this before initialising the transaction as needs
        # to be passed in base class constructor. The
        # default is None, which would then result in the
        # base class making the decision based on whether
        # application or agent as a whole are enabled.

        enabled = _lookup_environ_setting(environ,
                'newrelic.enabled', None)

        # Initialise the common transaction base class.

        super(WebTransaction, self).__init__(application, enabled)

        # Disable transactions for websocket connections.
        # Also disable autorum if this is a websocket. This is a good idea for
        # two reasons. First, RUM is unnecessary for websocket transactions
        # anyway. Secondly, due to a bug in the gevent-websocket (0.9.5)
        # package, if our _WSGIApplicationMiddleware is applied a websocket
        # connection cannot be made.

        if _is_websocket(environ):
            self.autorum_disabled = True
            self.enabled = False

        # Bail out if the transaction is running in a
        # disabled state.

        if not self.enabled:
            return

        # Will need to check the settings a number of times.

        settings = self._settings

        # Check for override settings from WSGI environ.

        self.background_task = _lookup_environ_setting(environ,
                'newrelic.set_background_task', False)

        self.ignore_transaction = _lookup_environ_setting(environ,
                'newrelic.ignore_transaction', False)
        self.suppress_apdex = _lookup_environ_setting(environ,
                'newrelic.suppress_apdex_metric', False)
        self.suppress_transaction_trace = _lookup_environ_setting(environ,
                'newrelic.suppress_transaction_trace', False)
        self.capture_params = _lookup_environ_setting(environ,
                'newrelic.capture_request_params',
                settings.capture_params)
        self.autorum_disabled = _lookup_environ_setting(environ,
                'newrelic.disable_browser_autorum',
                not settings.browser_monitoring.auto_instrument)

        # Make sure that if high security mode is enabled that
        # capture of request params is still being disabled.
        # No warning is issued for this in the logs because it
        # is a per request configuration and would create a lot
        # of noise.

        if settings.high_security:
            self.capture_params = False

        # WSGI spec says SERVER_PORT "can never be empty string",
        # but I'm going to set a default value anyway...

        port = environ.get('SERVER_PORT', None)
        if port:
            try:
                self._port = int(port)
            except Exception:
                pass

        # Extract from the WSGI environ dictionary
        # details of the URL path. This will be set as
        # default path for the web transaction. This can
        # be overridden by framework to be more specific
        # to avoid metrics explosion problem resulting
        # from too many distinct URLs for same resource
        # due to use of REST style URL concepts or
        # otherwise.

        request_uri = environ.get('REQUEST_URI', None)

        if request_uri is None:
            # The gunicorn WSGI server uses RAW_URI instead
            # of the more typical REQUEST_URI used by Apache
            # and other web servers.

            request_uri = environ.get('RAW_URI', None)

        script_name = environ.get('SCRIPT_NAME', None)
        path_info = environ.get('PATH_INFO', None)

        self._request_uri = request_uri

        if self._request_uri is not None:
            # Need to make sure we drop off any query string
            # arguments on the path if we have to fallback
            # to using the original REQUEST_URI. Can't use
            # attribute access on result as only support for
            # Python 2.5+.

            self._request_uri = urlparse.urlparse(self._request_uri)[2]

        if script_name is not None or path_info is not None:
            if path_info is None:
                path = script_name
            elif script_name is None:
                path = path_info
            else:
                path = script_name + path_info

            self.set_transaction_name(path, 'Uri', priority=1)

            if self._request_uri is None:
                self._request_uri = path
        else:
            if self._request_uri is not None:
                self.set_transaction_name(self._request_uri, 'Uri', priority=1)

        # See if the WSGI environ dictionary includes the
        # special 'X-Request-Start' or 'X-Queue-Start' HTTP
        # headers. These header are optional headers that can be
        # set within the underlying web server or WSGI server to
        # indicate when the current request was first received
        # and ready to be processed. The difference between this
        # time and when application starts processing the
        # request is the queue time and represents how long
        # spent in any explicit request queuing system, or how
        # long waiting in connecting state against listener
        # sockets where request needs to be proxied between any
        # processes within the application server.
        #
        # Note that mod_wsgi sets its own distinct variables
        # automatically. Initially it set mod_wsgi.queue_start,
        # which equated to when Apache first accepted the
        # request. This got changed to mod_wsgi.request_start
        # however, and mod_wsgi.queue_start was instead used
        # just for when requests are to be queued up for the
        # daemon process and corresponded to the point at which
        # they are being proxied, after Apache does any
        # authentication etc. We check for both so older
        # versions of mod_wsgi will still work, although we
        # don't try and use the fact that it is possible to
        # distinguish the two points and just pick up the
        # earlier of the two.
        #
        # Checking for the mod_wsgi values means it is not
        # necessary to enable and use mod_headers to add X
        # -Request-Start or X-Queue-Start. But we still check
        # for the headers and give priority to the explicitly
        # added header in case that header was added in front
        # end server to Apache instead.
        #
        # Which ever header is used, we accommodate the value
        # being in seconds, milliseconds or microseconds. Also
        # handle it being prefixed with 't='.

        now = time.time()

        def _parse_time_stamp(time_stamp):
            """
            Converts time_stamp to seconds. Input can be microseconds,
            milliseconds or seconds

            Divide the timestamp by the highest resolution divisor. If
            the result is older than Jan 1 2000, then pick a lower
            resolution divisor and repeat.  It is safe to assume no
            requests were queued for more than 10 years.

            """
            for divisor in (1000000.0, 1000.0, 1.0):
                converted_time = time_stamp / divisor

                # If queue_start is in the future, return 0.0.

                if converted_time > now:
                    return 0.0

                if converted_time > JAN_1_2000:
                    return converted_time

            return 0.0

        queue_time_headers = ('HTTP_X_REQUEST_START', 'HTTP_X_QUEUE_START',
                'mod_wsgi.request_start', 'mod_wsgi.queue_start')

        for queue_time_header in queue_time_headers:
            value = environ.get(queue_time_header, None)

            try:
                if value.startswith('t='):
                    try:
                        self.queue_start = _parse_time_stamp(float(value[2:]))
                    except Exception:
                        pass
                else:
                    try:
                        self.queue_start = _parse_time_stamp(float(value))
                    except Exception:
                        pass

            except Exception:
                pass

            if self.queue_start > 0.0:
                break

        # Capture query request string parameters, unless we're in
        # High Security Mode.

        if not settings.high_security:

            value = environ.get('QUERY_STRING', None)

            if value:
                try:
                    params = urlparse.parse_qs(value, keep_blank_values=True)
                except Exception:
                    params = cgi.parse_qs(value, keep_blank_values=True)

                self._request_params.update(params)

        # Check for Synthetics header

        if settings.synthetics.enabled and \
                settings.trusted_account_ids and settings.encoding_key:

            try:
                header_name = 'HTTP_X_NEWRELIC_SYNTHETICS'
                header = self.decode_newrelic_header(environ, header_name)
                synthetics = _parse_synthetics_header(header)

                if synthetics['account_id'] in settings.trusted_account_ids:

                    # Save obfuscated header, because we will pass it along
                    # unchanged in all external requests.

                    self.synthetics_header = environ.get(header_name)

                    if synthetics['version'] == 1:
                        self.synthetics_resource_id = synthetics['resource_id']
                        self.synthetics_job_id = synthetics['job_id']
                        self.synthetics_monitor_id = synthetics['monitor_id']

            except Exception:
                pass

        # Process the New Relic cross process ID header and extract
        # the relevant details.
        client_cross_process_id = environ.get('HTTP_X_NEWRELIC_ID')
        txn_header = environ.get('HTTP_X_NEWRELIC_TRANSACTION')
        self._process_incoming_cat_headers(client_cross_process_id, txn_header)

        # Capture WSGI request environ dictionary values. We capture
        # content length explicitly as will need it for cross process
        # metrics.

        self._read_length = int(environ.get('CONTENT_LENGTH') or -1)

        if settings.capture_environ:
            for name in settings.include_environ:
                if name in environ:
                    self._request_environment[name] = environ[name]

        # Strip query params from referer URL.
        if 'HTTP_REFERER' in self._request_environment:
            self._request_environment['HTTP_REFERER'] = _remove_query_string(
                    self._request_environment['HTTP_REFERER'])

        try:
            if 'CONTENT_LENGTH' in self._request_environment:
                self._request_environment['CONTENT_LENGTH'] = int(
                        self._request_environment['CONTENT_LENGTH'])
        except Exception:
            del self._request_environment['CONTENT_LENGTH']

        # Flags for tracking whether RUM header and footer have been
        # generated.

        self.rum_header_generated = False
        self.rum_footer_generated = False

    def decode_newrelic_header(self, environ, header_name):
        encoded_header = environ.get(header_name)
        if encoded_header:
            try:
                decoded_header = json_decode(deobfuscate(
                        encoded_header, self._settings.encoding_key))
            except Exception:
                decoded_header = None

        return decoded_header

    def process_response(self, status, response_headers, *args):
        """Processes response status and headers, extracting any
        details required and returning a set of additional headers
        to merge into that being returned for the web transaction.

        """

        # Set our internal response code based on WSGI status.
        # Per spec, it is expected that this is a string. If this is not
        # the case, skip setting the internal response code as we cannot
        # make the determination. (An integer 200 for example when passed
        # would raise as a 500 for WSGI applications).

        try:
            self.response_code = int(status.split(' ')[0])
        except Exception:
            pass

        # Extract response content length and type for inclusion in agent
        # attributes

        try:

            for header, value in response_headers:
                lower_header = header.lower()
                if 'content-length' == lower_header:
                    self._response_properties['CONTENT_LENGTH'] = int(value)
                elif 'content-type' == lower_header:
                    self._response_properties['CONTENT_TYPE'] = value

        except Exception:
            pass

        # Generate CAT response headers
        return self._generate_response_headers()

    def browser_timing_header(self):
        """Returns the JavaScript header to be included in any HTML
        response to perform real user monitoring. This function returns
        the header as a native Python string. In Python 2 native strings
        are stored as bytes. In Python 3 native strings are stored as
        unicode.

        """

        if not self.enabled:
            return ''

        if self._state != self.STATE_RUNNING:
            return ''

        if self.background_task:
            return ''

        if self.ignore_transaction:
            return ''

        if not self._settings:
            return ''

        if not self._settings.browser_monitoring.enabled:
            return ''

        if not self._settings.license_key:
            return ''

        # Don't return the header a second time if it has already
        # been generated.

        if self.rum_header_generated:
            return ''

        # Requirement is that the first 13 characters of the account
        # license key is used as the key when obfuscating values for
        # the RUM footer. Will not be able to perform the obfuscation
        # if license key isn't that long for some reason.

        if len(self._settings.license_key) < 13:
            return ''

        # Return the RUM header only if the agent received a valid value
        # for js_agent_loader from the data collector. The data
        # collector is not meant to send a non empty value for the
        # js_agent_loader value if browser_monitoring.loader is set to
        # 'none'.

        if self._settings.js_agent_loader:
            header = _js_agent_header_fragment % self._settings.js_agent_loader

            # To avoid any issues with browser encodings, we will make sure
            # that the javascript we inject for the browser agent is ASCII
            # encodable. Since we obfuscate all agent and user attributes, and
            # the transaction name with base 64 encoding, this will preserve
            # those strings, if they have values outside of the ASCII character
            # set. In the case of Python 2, we actually then use the encoded
            # value as we need a native string, which for Python 2 is a byte
            # string. If encoding as ASCII fails we will return an empty
            # string.

            try:
                if six.PY2:
                    header = header.encode('ascii')
                else:
                    header.encode('ascii')

            except UnicodeError:
                if not WebTransaction.unicode_error_reported:
                    _logger.error('ASCII encoding of js-agent-header failed.',
                            header)
                    WebTransaction.unicode_error_reported = True

                header = ''

        else:
            header = ''

        # We remember if we have returned a non empty string value and
        # if called a second time we will not return it again. The flag
        # will also be used to check whether the footer should be
        # generated.

        if header:
            self.rum_header_generated = True

        return header

    def browser_timing_footer(self):
        """Returns the JavaScript footer to be included in any HTML
        response to perform real user monitoring. This function returns
        the footer as a native Python string. In Python 2 native strings
        are stored as bytes. In Python 3 native strings are stored as
        unicode.

        """

        if not self.enabled:
            return ''

        if self._state != self.STATE_RUNNING:
            return ''

        if self.ignore_transaction:
            return ''

        # Only generate a footer if the header had already been
        # generated and we haven't already generated the footer.

        if not self.rum_header_generated:
            return ''

        if self.rum_footer_generated:
            return ''

        # Make sure we freeze the path.

        self._freeze_path()

        # When obfuscating values for the footer, we only use the
        # first 13 characters of the account license key.

        obfuscation_key = self._settings.license_key[:13]

        intrinsics = self.browser_monitoring_intrinsics(obfuscation_key)

        attributes = {}

        user_attributes = {}
        for attr in self.user_attributes:
            if attr.destinations & DST_BROWSER_MONITORING:
                user_attributes[attr.name] = attr.value

        if user_attributes:
            attributes['u'] = user_attributes

        agent_attributes = {}
        for attr in self.request_parameters_attributes:
            if attr.destinations & DST_BROWSER_MONITORING:
                agent_attributes[attr.name] = attr.value

        if agent_attributes:
            attributes['a'] = agent_attributes

        # create the data structure that pull all our data in

        footer_data = intrinsics

        if attributes:
            attributes = obfuscate(json_encode(attributes), obfuscation_key)
            footer_data['atts'] = attributes

        footer = _js_agent_footer_fragment % json_encode(footer_data)

        # To avoid any issues with browser encodings, we will make sure that
        # the javascript we inject for the browser agent is ASCII encodable.
        # Since we obfuscate all agent and user attributes, and the transaction
        # name with base 64 encoding, this will preserve those strings, if
        # they have values outside of the ASCII character set.
        # In the case of Python 2, we actually then use the encoded value
        # as we need a native string, which for Python 2 is a byte string.
        # If encoding as ASCII fails we will return an empty string.

        try:
            if six.PY2:
                footer = footer.encode('ascii')
            else:
                footer.encode('ascii')

        except UnicodeError:
            if not WebTransaction.unicode_error_reported:
                _logger.error('ASCII encoding of js-agent-footer failed.',
                        footer)
                WebTransaction.unicode_error_reported = True

            footer = ''

        # We remember if we have returned a non empty string value and
        # if called a second time we will not return it again.

        if footer:
            self.rum_footer_generated = True

        return footer

    def browser_monitoring_intrinsics(self, obfuscation_key):
        txn_name = obfuscate(self.path, obfuscation_key)

        queue_start = self.queue_start or self.start_time
        start_time = self.start_time
        end_time = time.time()

        queue_duration = int((start_time - queue_start) * 1000)
        request_duration = int((end_time - start_time) * 1000)

        intrinsics = {
            "beacon": self._settings.beacon,
            "errorBeacon": self._settings.error_beacon,
            "licenseKey": self._settings.browser_key,
            "applicationID": self._settings.application_id,
            "transactionName": txn_name,
            "queueTime": queue_duration,
            "applicationTime": request_duration,
            "agent": self._settings.js_agent_file,
        }

        if self._settings.browser_monitoring.ssl_for_http is not None:
            ssl_for_http = self._settings.browser_monitoring.ssl_for_http
            intrinsics['sslForHttp'] = ssl_for_http

        return intrinsics


class _WSGIApplicationIterable(object):

    def __init__(self, transaction, generator):
        self.transaction = transaction
        self.generator = generator
        self.response_trace = None
        self.closed = False

    def __iter__(self):
        self.start_trace()

        try:
            for item in self.generator:
                try:
                    self.transaction._calls_yield += 1
                    self.transaction._bytes_sent += len(item)
                except Exception:
                    pass

                yield item

        except GeneratorExit:
            raise

        except:  # Catch all
            self.transaction.record_exception(*sys.exc_info())
            raise

        finally:
            self.close()

    def start_trace(self):
        if not self.transaction._sent_start:
            self.transaction._sent_start = time.time()

        if not self.response_trace:
            self.response_trace = FunctionTrace(self.transaction,
                    name='Response', group='Python/WSGI')
            self.response_trace.__enter__()

    def close(self):
        if self.closed:
            return

        if self.response_trace:
            self.response_trace.__exit__(None, None, None)
            self.response_trace = None

        try:
            with FunctionTrace(self.transaction, name='Finalize',
                    group='Python/WSGI'):

                if isinstance(self.generator, _WSGIApplicationMiddleware):
                    self.generator.close()

                elif hasattr(self.generator, 'close'):
                    name = callable_name(self.generator.close)
                    with FunctionTrace(self.transaction, name):
                        self.generator.close()

        except:  # Catch all
            self.transaction.__exit__(*sys.exc_info())
            raise

        else:
            self.transaction.__exit__(None, None, None)
            self.transaction._sent_end = time.time()

        finally:
            self.closed = True


class _WSGIInputWrapper(object):

    def __init__(self, transaction, input):
        self.__transaction = transaction
        self.__input = input

    def __getattr__(self, name):
        return getattr(self.__input, name)

    def close(self):
        if hasattr(self.__input, 'close'):
            self.__input.close()

    def read(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            data = self.__input.read(*args, **kwargs)
            try:
                self.__transaction._calls_read += 1
                self.__transaction._bytes_read += len(data)
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return data

    def readline(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            line = self.__input.readline(*args, **kwargs)
            try:
                self.__transaction._calls_readline += 1
                self.__transaction._bytes_read += len(line)
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return line

    def readlines(self, *args, **kwargs):
        if not self.__transaction._read_start:
            self.__transaction._read_start = time.time()
        try:
            lines = self.__input.readlines(*args, **kwargs)
            try:
                self.__transaction._calls_readlines += 1
                self.__transaction._bytes_read += sum(map(len, lines))
            except Exception:
                pass
        finally:
            self.__transaction._read_end = time.time()
        return lines


class _WSGIApplicationMiddleware(object):

    # This is a WSGI middleware for automatically inserting RUM into
    # HTML responses. It only works for where a WSGI application is
    # returning response content via a iterable/generator. It does not
    # work if the WSGI application write() callable is being used. It
    # will buffer response content up to the start of <body>. This is
    # technically in violation of the WSGI specification if one is
    # strict, but will still work with all known WSGI servers. Because
    # it does buffer, then technically it may cause a problem with
    # streamed responses. For that to occur then it would have to be a
    # HTML response that doesn't actually use <body> and so technically
    # is not a valid HTML response. It is assumed though that in
    # streaming a response, the <head> itself isn't streamed out only
    # gradually.

    search_maximum = 64 * 1024

    def __init__(self, application, environ, start_response, transaction):
        self.application = application

        self.pass_through = True

        self.request_environ = environ
        self.outer_start_response = start_response
        self.outer_write = None

        self.transaction = transaction

        self.response_status = None
        self.response_headers = []
        self.response_args = ()

        self.content_length = None

        self.response_length = 0
        self.response_data = []

        settings = transaction.settings

        self.debug = settings and settings.debug.log_autorum_middleware

        # Grab the iterable returned by the wrapped WSGI
        # application.
        self.iterable = self.application(self.request_environ,
                self.start_response)

    def process_data(self, data):
        # If this is the first data block, then immediately try
        # for an insertion using full set of criteria. If this
        # works then we are done, else we move to next phase of
        # buffering up content until we find the body element.

        def html_to_be_inserted():
            header = self.transaction.browser_timing_header()

            if not header:
                return b''

            footer = self.transaction.browser_timing_footer()

            return six.b(header) + six.b(footer)

        if not self.response_data:
            modified = insert_html_snippet(data, html_to_be_inserted)

            if modified is not None:
                if self.debug:
                    _logger.debug('RUM insertion from WSGI middleware '
                            'triggered on first yielded string from '
                            'response. Bytes added was %r.',
                            len(modified) - len(data))

                if self.content_length is not None:
                    length = len(modified) - len(data)
                    self.content_length += length

                return [modified]

        # Buffer up the data. If we haven't found the start of
        # the body element, that is all we do. If we have reached
        # the limit of buffering allowed, then give up and return
        # the buffered data.

        if not self.response_data or not verify_body_exists(data):
            self.response_length += len(data)
            self.response_data.append(data)

            if self.response_length >= self.search_maximum:
                buffered_data = self.response_data
                self.response_data = []
                return buffered_data

            return

        # Now join back together any buffered data into a single
        # string. This makes it easier to process, but there is a
        # risk that we could temporarily double memory use for
        # the response content if had small data blocks followed
        # by very large data block. Expect that the risk of this
        # occurring is very small.

        if self.response_data:
            self.response_data.append(data)
            data = b''.join(self.response_data)
            self.response_data = []

        # Perform the insertion of the HTML. This should always
        # succeed as we would only have got here if we had found
        # the body element, which is the fallback point for
        # insertion.

        modified = insert_html_snippet(data, html_to_be_inserted)

        if modified is not None:
            if self.debug:
                _logger.debug('RUM insertion from WSGI middleware '
                        'triggered on subsequent string yielded from '
                        'response. Bytes added was %r.',
                        len(modified) - len(data))

            if self.content_length is not None:
                length = len(modified) - len(data)
                self.content_length += length

            return [modified]

        # Something went very wrong as we should never get here.

        return [data]

    def flush_headers(self):
        # Add back in any response content length header. It will
        # have been updated with the adjusted length by now if
        # additional data was inserted into the response.

        if self.content_length is not None:
            header = (('Content-Length', str(self.content_length)))
            self.response_headers.append(header)

        self.outer_write = self.outer_start_response(self.response_status,
                self.response_headers, *self.response_args)

    def inner_write(self, data):
        # If the write() callable is used, we do not attempt to
        # do any insertion at all here after.

        self.pass_through = True

        # Flush the response headers if this hasn't yet been done.

        if self.outer_write is None:
            self.flush_headers()

        # Now write out any buffered response data in case the
        # WSGI application was doing something evil where it
        # mixed use of yield and write. Technically if write()
        # is used, it is supposed to be before any attempt to
        # yield a string. When done switch to pass through mode.

        if self.response_data:
            for buffered_data in self.response_data:
                self.outer_write(buffered_data)
            self.response_data = []

        return self.outer_write(data)

    def start_response(self, status, response_headers, *args):
        # The start_response() function can be called more than
        # once. In that case, the values derived from the most
        # recent call are used. We therefore need to reset any
        # calculated values.

        self.pass_through = True

        self.response_status = status
        self.response_headers = response_headers
        self.response_args = args

        self.content_length = None

        # We need to check again if auto RUM has been disabled.
        # This is because it can be disabled using an API call.
        # Also check whether RUM insertion has already occurred.

        if (self.transaction.autorum_disabled or
                self.transaction.rum_header_generated):

            self.flush_headers()
            self.pass_through = True

            return self.inner_write

        # Extract values for response headers we need to work. Do
        # not copy across the content length header at this time
        # as we will need to adjust the length later if we are
        # able to inject our Javascript.

        pass_through = False

        headers = []

        content_type = None
        content_length = None
        content_encoding = None
        content_disposition = None

        for (name, value) in response_headers:
            _name = name.lower()

            if _name == 'content-length':
                try:
                    content_length = int(value)
                    continue

                except ValueError:
                    pass_through = True

            elif _name == 'content-type':
                content_type = value

            elif _name == 'content-encoding':
                content_encoding = value

            elif _name == 'content-disposition':
                content_disposition = value

            headers.append((name, value))

        # We can only inject our Javascript if the content type
        # is an allowed value, no content encoding has been set
        # and an attachment isn't being used.

        def should_insert_html():
            if pass_through:
                return False

            if content_encoding is not None:
                # This will match any encoding, including if the
                # value 'identity' is used. Technically the value
                # 'identity' should only be used in the header
                # Accept-Encoding and not Content-Encoding. In
                # other words, a WSGI application should not be
                # returning identity. We could check and allow it
                # anyway and still do RUM insertion, but don't.

                return False

            if (content_disposition is not None and
                    content_disposition.split(';')[0].strip().lower() ==
                    'attachment'):
                return False

            if content_type is None:
                return False

            settings = self.transaction.settings
            allowed_content_type = settings.browser_monitoring.content_type

            if content_type.split(';')[0] not in allowed_content_type:
                return False

            return True

        if should_insert_html():
            self.pass_through = False

            self.content_length = content_length
            self.response_headers = headers

        # If in pass through mode at this point, we need to flush
        # out the headers. We technically might do this again
        # later if start_response() was called more than once.

        if self.pass_through:
            self.flush_headers()

        return self.inner_write

    def close(self):
        # Call close() on the iterable as required by the
        # WSGI specification.

        if hasattr(self.iterable, 'close'):
            name = callable_name(self.iterable.close)
            with FunctionTrace(self.transaction, name):
                self.iterable.close()

    def __iter__(self):
        # Process the response content from the iterable.

        for data in self.iterable:
            # If we are in pass through mode, simply pass it
            # through. If we are in pass through mode then
            # the headers should already have been flushed.

            if self.pass_through:
                yield data

                continue

            # If the headers haven't been flushed we need to
            # check for the potential insertion point and
            # buffer up data as necessary if we can't find it.

            if self.outer_write is None:
                # Ignore any empty strings.

                if not data:
                    continue

                # Check for the insertion point. Will return
                # None if data was buffered.

                buffered_data = self.process_data(data)

                if buffered_data is None:
                    continue

                # The data was returned, with it being
                # potentially modified. It would not have
                # been modified if we had reached maximum to
                # be buffer. Flush out the headers, switch to
                # pass through mode and yield the data.

                self.flush_headers()
                self.pass_through = True

                for data in buffered_data:
                    yield data

            else:
                # Depending on how the WSGI specification is
                # interpreted, this shouldn't occur. That is,
                # nothing should be yielded prior to the
                # start_response() function being called. The
                # CGI/WSGI example in the WSGI specification
                # does allow that though as do various WSGI
                # servers that followed that example.

                yield data

        # Ensure that headers have been written if the
        # response was actually empty.

        if self.outer_write is None:
            self.flush_headers()
            self.pass_through = True

        # Ensure that any remaining buffered data is also
        # written. Technically this should never be able
        # to occur at this point, but do it just in case.

        if self.response_data:
            for data in self.response_data:
                yield data


def WSGIApplicationWrapper(wrapped, application=None, name=None,
        group=None, framework=None):

    if framework is not None and not isinstance(framework, tuple):
        framework = (framework, None)

    def _nr_wsgi_application_wrapper_(wrapped, instance, args, kwargs):
        # Check to see if any transaction is present, even an inactive
        # one which has been marked to be ignored or which has been
        # stopped already.

        transaction = current_transaction(active_only=False)

        if transaction:
            # If there is any active transaction we will return without
            # applying a new WSGI application wrapper context. In the
            # case of a transaction which is being ignored or which has
            # been stopped, we do that without doing anything further.

            if transaction.ignore_transaction or transaction.stopped:
                return wrapped(*args, **kwargs)

            # For any other transaction, we record the details of any
            # framework against the transaction for later reporting as
            # supportability metrics.

            if framework:
                transaction.add_framework_info(
                        name=framework[0], version=framework[1])

            # Also override the web transaction name to be the name of
            # the wrapped callable if not explicitly named, and we want
            # the default name to be that of the WSGI component for the
            # framework. This will override the use of a raw URL which
            # can result in metric grouping issues where a framework is
            # not instrumented or is leaking URLs.

            settings = transaction._settings

            if name is None and settings:
                if framework is not None:
                    naming_scheme = settings.transaction_name.naming_scheme
                    if naming_scheme in (None, 'framework'):
                        transaction.set_transaction_name(
                                callable_name(wrapped), priority=1)

            elif name:
                transaction.set_transaction_name(name, group, priority=1)

            return wrapped(*args, **kwargs)

        # Otherwise treat it as top level transaction. We have to though
        # look first to see whether the application name has been
        # overridden through the WSGI environ dictionary.

        def _args(environ, start_response, *args, **kwargs):
            return environ, start_response

        environ, start_response = _args(*args, **kwargs)

        app_name = environ.get('newrelic.app_name')

        target_application = application

        if app_name:
            if app_name.find(';') != -1:
                app_names = [string.strip(n) for n in app_name.split(';')]
                app_name = app_names[0]
                target_application = application_instance(app_name)
                for altname in app_names[1:]:
                    target_application.link_to_application(altname)
            else:
                target_application = application_instance(app_name)
        else:
            # If application has an activate() method we assume it is an
            # actual application. Do this rather than check type so that
            # can easily mock it for testing.

            # FIXME Should this allow for multiple apps if a string.

            if not hasattr(application, 'activate'):
                target_application = application_instance(application)

        # Now start recording the actual web transaction.

        transaction = WebTransaction(target_application, environ)
        transaction.__enter__()

        # Record details of framework against the transaction for later
        # reporting as supportability metrics.

        if framework:
            transaction.add_framework_info(
                    name=framework[0], version=framework[1])

        # Override the initial web transaction name to be the supplied
        # name, or the name of the wrapped callable if wanting to use
        # the callable as the default. This will override the use of a
        # raw URL which can result in metric grouping issues where a
        # framework is not instrumented or is leaking URLs.
        #
        # Note that at present if default for naming scheme is still
        # None and we aren't specifically wrapping a designated
        # framework, then we still allow old URL based naming to
        # override. When we switch to always forcing a name we need to
        # check for naming scheme being None here.

        settings = transaction._settings

        if name is None and settings:
            naming_scheme = settings.transaction_name.naming_scheme

            if framework is not None:
                if naming_scheme in (None, 'framework'):
                    transaction.set_transaction_name(
                            callable_name(wrapped), priority=1)

            elif naming_scheme in ('component', 'framework'):
                transaction.set_transaction_name(
                        callable_name(wrapped), priority=1)

        elif name:
            transaction.set_transaction_name(name, group, priority=1)

        def _start_response(status, response_headers, *args):

            additional_headers = transaction.process_response(
                    status, response_headers, *args)

            _write = start_response(status,
                    response_headers + additional_headers, *args)

            def write(data):
                if not transaction._sent_start:
                    transaction._sent_start = time.time()
                result = _write(data)
                transaction._calls_write += 1
                try:
                    transaction._bytes_sent += len(data)
                except Exception:
                    pass
                transaction._sent_end = time.time()
                return result

            return write

        try:
            # Should always exist, but check as test harnesses may not
            # have it.

            if 'wsgi.input' in environ:
                environ['wsgi.input'] = _WSGIInputWrapper(transaction,
                        environ['wsgi.input'])

            with FunctionTrace(transaction, name='Application',
                    group='Python/WSGI'):
                with FunctionTrace(transaction, name=callable_name(wrapped)):
                    if (settings and settings.browser_monitoring.enabled and
                            not transaction.autorum_disabled):
                        result = _WSGIApplicationMiddleware(wrapped,
                                environ, _start_response, transaction)
                    else:
                        result = wrapped(environ, _start_response)

        except:  # Catch all
            transaction.__exit__(*sys.exc_info())
            raise

        return _WSGIApplicationIterable(transaction, result)

    return FunctionWrapper(wrapped, _nr_wsgi_application_wrapper_)


def wsgi_application(application=None, name=None, group=None, framework=None):
    return functools.partial(WSGIApplicationWrapper, application=application,
            name=name, group=group, framework=framework)


def wrap_wsgi_application(module, object_path, application=None,
            name=None, group=None, framework=None):
    wrap_object(module, object_path, WSGIApplicationWrapper,
            (application, name, group, framework))
