import logging
import weakref
import traceback
import contextlib

from newrelic.api.application import application_instance
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.config import extra_settings
from newrelic.core.config import ignore_status_code

_logger = logging.getLogger('newrelic.hooks.framework_tornado')

_boolean_states = {
   '1': True, 'yes': True, 'true': True, 'on': True,
   '0': False, 'no': False, 'false': False, 'off': False
}

def _setting_boolean(value):
    if value.lower() not in _boolean_states:
        raise ValueError('Not a boolean: %s' % value)
    return _boolean_states[value.lower()]

_settings_types = {
    'debug.transaction_monitoring': _setting_boolean,
    'instrumentation.metrics.async_wait_rollup': _setting_boolean,
}

_settings_defaults = {
    'debug.transaction_monitoring': False,
    'instrumentation.metrics.async_wait_rollup': True,
}

tornado_settings = extra_settings('import-hook:tornado',
        types=_settings_types, defaults=_settings_defaults)

_last_transaction_activation = None

def last_transaction_activation():
    return _last_transaction_activation

def record_exception(transaction, exc_info):
    # Record the details of any exception ignoring status codes which
    # have been configured to be ignored.

    import tornado.web

    exc = exc_info[0]
    value = exc_info[1]

    if exc is tornado.web.HTTPError:
        if ignore_status_code(value.status_code):
            return

    transaction.record_exception(*exc_info)

def request_environment(application, request):
    # This creates a WSGI environ dictionary from a Tornado request.

    result = getattr(request, '_nr_request_environ', None)

    if result is not None:
        return result

    # We don't bother if the agent hasn't as yet been registered.

    settings = application.settings

    if not settings:
        return {}

    request._nr_request_environ = result = {}

    result['REQUEST_URI'] = request.uri
    result['QUERY_STRING'] = request.query

    value = request.headers.get('X-NewRelic-ID')
    if value:
        result['HTTP_X_NEWRELIC_ID'] = value

    value = request.headers.get('X-NewRelic-Transaction')
    if value:
        result['HTTP_X_NEWRELIC_TRANSACTION'] = value

    value = request.headers.get('X-Request-Start')
    if value:
        result['HTTP_X_REQUEST_START'] = value

    value = request.headers.get('X-Queue-Start')
    if value:
        result['HTTP_X_QUEUE_START'] = value

    for key in settings.include_environ:
        if key == 'REQUEST_METHOD':
            result[key] = request.method
        elif key == 'HTTP_USER_AGENT':
            value = request.headers.get('User-Agent')
            if value:
                result[key] = value
        elif key == 'HTTP_REFERER':
            value = request.headers.get('Referer')
            if value:
                result[key] = value
        elif key == 'CONTENT_TYPE':
            value = request.headers.get('Content-Type')
            if value:
                result[key] = value
        elif key == 'CONTENT_LENGTH':
            value = request.headers.get('Content-Length')
            if value:
                result[key] = value

    return result

def retrieve_current_transaction():
    # Retrieves the current transaction regardless of whether it has
    # been stopped or ignored. We can't just return the current
    # transaction gated by whether the transaction has been stopped or
    # is being ignored as that would screw things up because of all the
    # funny checks we need to do against the transaction when resuming a
    # transaction and so on.

    return current_transaction(active_only=False)

def retrieve_transaction_request(transaction):
    # Retrieves any request already associated with the transaction.

    if hasattr(transaction, '_nr_current_request'):
        if transaction._nr_current_request is not None:
            return transaction._nr_current_request()

def retrieve_request_transaction(request):
    # Retrieves any transaction already associated with the request.

    return getattr(request, '_nr_transaction', None)

def request_finished(request):
    # Returns whether the request is in the process of being finished.
    # If we haven't started tracking of the request returns None.

    return getattr(request, '_nr_request_finished', None)

def request_caller_context(request):
    # Returns the most recently specified named caller context.

    if not hasattr(request, '_nr_caller_context'):
        return

    if not request._nr_caller_context:
        return

    return request._nr_caller_context[-1]

@contextlib.contextmanager
def _nr_wrapper_named_caller_context_(request, name):
    if not hasattr(request, '_nr_caller_context'):
        request._nr_caller_context = []

    request._nr_caller_context.append(name)

    yield

    request._nr_caller_context.pop(-1)

def initiate_request_monitoring(request):
    # Creates a new transaction and associates it with the request.
    # We always use the default application specified in the agent
    # configuration.

    application = application_instance()

    # We need to fake up a WSGI like environ dictionary with the key
    # bits of information we need.

    environ = request_environment(application, request)

    # We now start recording the actual web transaction. Bail out though
    # if it turns out that recording of transactions is not enabled.

    transaction = WebTransaction(application, environ)

    if not transaction.enabled:
        return

    if tornado_settings.debug.transaction_monitoring:
        global _last_transaction_activation
        _last_transaction_activation = ''.join(traceback.format_stack()[:-1])

    transaction.__enter__()

    request._nr_transaction = transaction

    request._nr_wait_function_trace = None
    request._nr_request_finished = False

    # We also need to add a reference to the request object in to the
    # transaction object so we can later access it in a deferred. We
    # need to use a weakref to avoid an object cycle which may prevent
    # cleanup of the transaction.

    transaction._nr_current_request = weakref.ref(request)

    # Record framework information for generation of framework metrics.

    import tornado

    if hasattr(tornado, 'version_info'):
        version = '.'.join(map(str, tornado.version_info))
    else:
        version = None

    transaction.add_framework_info('Tornado/ASYNC', version)

    return transaction

def suspend_request_monitoring(request, name, group='Python/Tornado',
        terminal=True, rollup=None):

    # Suspend the monitoring of the transaction. We do this because
    # we can't rely on thread local data to separate transactions for
    # requests. We thus have to move it out of the way.

    transaction = retrieve_request_transaction(request)

    if transaction is None:
        _logger.error('Runtime instrumentation error. Suspending the '
                'Tornado transaction but there was no transaction cached '
                'against the request object. Report this issue to New Relic '
                'support.\n%s', ''.join(traceback.format_stack()[:-1]))

        return

    # Create a function trace to track the time while monitoring of
    # this transaction is suspended.

    if request._nr_wait_function_trace:
        _logger.error('Runtime instrumentation error. Suspending the '
                'Tornado transaction when it has already been suspended. '
                'Report this issue to New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))

        last = last_transaction_activation()

        if last is not None:
            _logger.info('The currently active transaction was possibly '
                    'initiated or resumed from %r.', last)

        return

    if rollup is None:
        if tornado_settings.instrumentation.metrics.async_wait_rollup:
            rollup = 'Async Wait'

    request._nr_wait_function_trace = FunctionTrace(transaction,
            name=name, group=group, terminal=terminal, rollup=rollup)

    request._nr_wait_function_trace.__enter__()

    transaction.drop_transaction()

def resume_request_monitoring(request, required=False):
    # Resume the monitoring of the transaction. This is moving the
    # transaction stored against the request as the active one.

    transaction = retrieve_request_transaction(request)

    if transaction is None:
        if not required:
            return

        _logger.error('Runtime instrumentation error. Resuming the '
                'Tornado transaction but there was no transaction cached '
                'against the request object. Report this issue to New Relic '
                'support.\n%s', ''.join(traceback.format_stack()[:-1]))

        return

    # Now make the transaction stored against the request the current
    # transaction.

    if tornado_settings.debug.transaction_monitoring:
        global _last_transaction_activation
        _last_transaction_activation = ''.join(traceback.format_stack()[:-1])

    transaction.save_transaction()

    # Close out any active function trace used to track the time while
    # monitoring of the transaction was suspended. Technically there
    # should always be an active function trace but check and ignore
    # it if there isn't for now.

    try:
        if request._nr_wait_function_trace:
            request._nr_wait_function_trace.__exit__(None, None, None)

    finally:
        request._nr_wait_function_trace = None

    return transaction

def finish_request_monitoring(request):
    # Marks that the request should be finishing up.

    request._nr_request_finished = True

def finalize_request_monitoring(request, exc=None, value=None, tb=None):
    # Finalize monitoring of the transaction.

    transaction = retrieve_request_transaction(request)

    if transaction is None:
        _logger.error('Runtime instrumentation error. Finalizing the '
                'Tornado transaction but there was no transaction cached '
                'against the request object. Report this issue to New Relic '
                'support.\n%s', ''.join(traceback.format_stack()[:-1]))

        return

    # If all nodes hadn't been popped from the transaction stack then
    # error messages will be logged by the transaction. We therefore do
    # not need to check here.
    #
    # We must ensure we cleanup here even if __exit__() fails with an
    # exception for some reason. This is especially the case for our own
    # test harnesses.

    try:
        transaction.__exit__(exc, value, tb)

    finally:
        transaction._nr_current_request = None

        request._nr_transaction = None
        request._nr_wait_function_trace = None
        request._nr_request_finished = True
