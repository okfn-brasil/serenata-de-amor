import logging
import sys
import traceback

from newrelic.api.function_trace import FunctionTrace, wrap_function_trace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper

from newrelic.hooks.framework_tornado import (retrieve_request_transaction,
        initiate_request_monitoring, suspend_request_monitoring,
        resume_request_monitoring, finish_request_monitoring,
        finalize_request_monitoring, request_finished,
        last_transaction_activation, retrieve_current_transaction)

_logger = logging.getLogger(__name__)

def _nr_wrapper_HTTPConnection__on_headers_(wrapped, instance, args, kwargs):
    # This is the first point at which we should ever be called for a
    # request. It is called when the request headers have been read in.
    # The next phase would be to read in any request content but we
    # can't tell whether that will happen or not at this point. We do
    # need to setup a callback when connection is closed due to client
    # disconnecting.

    assert instance is not None

    connection = instance

    # Check to see if we are being called within the context of any sort
    # of transaction. This should never occur, but if we are, then we
    # don't bother doing anything and just call the wrapped function
    # immediately as can't be sure what else to do.

    transaction = retrieve_current_transaction()

    if transaction is not None:
        _logger.error('Runtime instrumentation error. Starting a new '
                'Tornado web request but there is a transaction active '
                'already. Report this issue to New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))

        last = last_transaction_activation()

        if last is not None:
            _logger.info('The currently active transaction was possibly '
                    'initiated or resumed from %r.', last)

        return wrapped(*args, **kwargs)

    # Execute the wrapped function as we are only going to do something
    # after it has been called.

    result = wrapped(*args, **kwargs)

    # Check to see if the connection has already been closed or the
    # request finished. The connection can be closed where request
    # content length was too big.

    if connection.stream.closed():
        return result

    if connection._request_finished:
        return result

    # Check to see if we have already associated a transaction with the
    # request. This would happen if there was actually no request
    # content and so the application was called immediately. We can
    # return straight away in that case.

    request = connection._request

    if request is None:
        return result

    transaction = retrieve_request_transaction(request)

    if transaction is not None:
        return result

    # If we get here it is because there was request content which first
    # had to be read. No transaction should have been created as yet.
    # Create the transaction but if it is None then it means recording
    # of transactions is not enabled then do not need to do anything.

    transaction = initiate_request_monitoring(request)

    if transaction is None:
        return result

    # Add a callback variable to the connection object so that we can
    # be notified when the connection is closed before all the request
    # content has been read. This will be invoked from the method
    # BaseIOStream._maybe_run_close_callback().

    def _close():
        transaction = resume_request_monitoring(request)

        if transaction is None:
            return

        # Force a function trace to record the fact that the socket
        # connection was closed due to client disconnection.

        with FunctionTrace(transaction, name='Request/Close',
                group='Python/Tornado'):
            pass

        # We finish up the transaction and nothing else should occur.

        finalize_request_monitoring(request)

    connection.stream._nr_close_callback = _close

    # Name transaction initially after the wrapped function so that if
    # the connection is dropped before all the request content is read,
    # then we don't get metric grouping issues with it being named after
    # the URL.

    name = callable_name(wrapped)

    transaction.set_transaction_name(name)

    # Now suspend monitoring of current transaction until next callback.

    suspend_request_monitoring(request, name='Request/Input')

    return result

def _nr_wrapper_HTTPConnection__on_request_body_(wrapped, instance,
        args, kwargs):

    # Called when there was a request body and it has now all been
    # read in and buffered ready to call the request handler.

    assert instance is not None

    connection = instance
    request = connection._request

    # Wipe out our temporary callback for being notified that the
    # connection is being closed before content is read.

    connection.stream._nr_close_callback = None

    # Restore any transaction which may have been suspended.

    transaction = resume_request_monitoring(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    # Now call the orginal wrapped function.

    try:
        result = wrapped(*args, **kwargs)

    except:  # Catch all
        # There should never be an error from wrapped function but
        # in case there is, try finalizing transaction.

        finalize_request_monitoring(request)
        raise

    else:
        if not request_finished(request):
            suspend_request_monitoring(request, name='Callback/Wait')

        elif not request.connection.stream.writing():
            finalize_request_monitoring(request)

        else:
            suspend_request_monitoring(request, name='Request/Output')

        return result

def _nr_wrapper_HTTPConnection__finish_request(wrapped, instance,
        args, kwargs):

    # Normally called when the request is all complete meaning that we
    # have to finalize our own transaction. We may actually enter here
    # with the transaction already being the current one.

    connection = instance
    request = connection._request

    transaction = retrieve_request_transaction(request)

    # The wrapped function could be called more than once. If it is then
    # the transaction should already have been completed. In this case
    # the transaction should be None. To be safe also check whether the
    # request itself was already flagged as finished. If transaction was
    # the same as the current transaction the following check would have
    # just marked it as finished again, but this first check will cover
    # where the current transaction is for some reason different.

    if transaction is None:
        return wrapped(*args, **kwargs)

    if request_finished(request):
        return wrapped(*args, **kwargs)

    # Deal now with the possibility that the transaction is already the
    # current active transaction.

    if transaction == retrieve_current_transaction():
        finish_request_monitoring(request)

        return wrapped(*args, **kwargs)

    # If we enter here with an active transaction and it isn't the one
    # we expect, then not sure what we should be doing, so simply
    # return. This should hopefully never occur.

    if retrieve_current_transaction() is not None:
        return wrapped(*args, **kwargs)

    # Not the current active transaction and so we need to try and
    # resume the transaction associated with the request.

    transaction = resume_request_monitoring(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    finish_request_monitoring(request)

    try:
        result = wrapped(*args, **kwargs)

    except:  # Catch all
        # There should never be an error from wrapped function but
        # in case there is, try finalizing transaction.

        finalize_request_monitoring(request, *sys.exc_info())
        raise

    finalize_request_monitoring(request)

    return result

def instrument_tornado_httpserver(module):
    if hasattr(module, 'HTTPConnection'):
        # The HTTPConnection class only existed prior to Tornado 4.0.

        wrap_function_wrapper(module, 'HTTPConnection._on_headers',
                _nr_wrapper_HTTPConnection__on_headers_)
        wrap_function_wrapper(module, 'HTTPConnection._on_request_body',
                _nr_wrapper_HTTPConnection__on_request_body_)
        wrap_function_wrapper(module, 'HTTPConnection._finish_request',
                _nr_wrapper_HTTPConnection__finish_request)

    if hasattr(module.HTTPRequest, '_parse_mime_body'):
        wrap_function_trace(module, 'HTTPRequest._parse_mime_body')
