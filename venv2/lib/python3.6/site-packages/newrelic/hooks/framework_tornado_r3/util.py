import logging
import sys
import traceback

from newrelic.api.application import application as application_instance
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import Sentinel, current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import function_wrapper
from newrelic.core.config import ignore_status_code
from newrelic.core.transaction_cache import transaction_cache

_logger = logging.getLogger(__name__)


# To pass the name of the coroutine back we attach it as an attribute to a
# returned value. If this returned value is None, we instead pass up a
# NoneProxy object with the attribute. When the attribute is consumed we must
# restore the None value.
class NoneProxy(object):
    pass


def current_thread_id():
    return transaction_cache().current_thread_id()


def record_exception(exc_info):
    # Record the details of any exception ignoring status codes which
    # have been configured to be ignored.

    import tornado.web

    exc = exc_info[0]
    value = exc_info[1]

    # Not an error so we just return.
    if exc is tornado.web.Finish:
        return

    if exc is tornado.web.HTTPError:
        if ignore_status_code(value.status_code):
            return

    transaction = retrieve_current_transaction()
    if transaction:
        transaction.record_exception(*exc_info)
    else:
        # If we are not in a transaction we record the exception to the default
        # application specified in the agent configuration.
        application = application_instance()
        if application and application.enabled:
            application.record_exception(*exc_info)


def retrieve_current_transaction():
    # Retrieves the current transaction regardless of whether it has
    # been stopped or ignored. We sometimes want to purge the current
    # transaction from the transaction cache and remove it with the
    # known current transaction that is being called into asynchronously.

    return current_transaction(active_only=False)


def retrieve_request_transaction(request):
    # Retrieves any transaction already associated with the request.

    try:
        transaction = getattr(request, '_nr_transaction')
    except AttributeError:
        _logger.error('Runtime instrumentation error. Attempt to retrieve '
                'the transaction from the request object failed. Please '
                'report this issue to New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))
        return None
    else:
        return transaction


def retrieve_transaction_request(transaction):
    # Retrieves any request already associated with the transaction.
    request_weakref = getattr(transaction, '_nr_current_request', None)
    if request_weakref is not None:
        return request_weakref()
    return None

# We sometimes want to purge the current transaction out of the queue and
# replace it with the known current transaction which has been called into
# asynchronously.


def purge_current_transaction():
    old_transaction = retrieve_current_transaction()
    if old_transaction is not None:
        old_transaction.drop_transaction()
    return old_transaction


def replace_current_transaction(new_transaction):
    old_transaction = purge_current_transaction()
    if new_transaction:
        new_transaction.save_transaction()
    return old_transaction


def possibly_finalize_transaction(transaction, exc=None, value=None, tb=None):
    if transaction is None:
        _logger.error('Runtime instrumentation error. Attempting to finalize '
                'an empty transaction. Please report this issue to New Relic '
                'support.\n%s', ''.join(traceback.format_stack()[:-1]))
        return

    if (transaction._request_handler_finalize and
            transaction._server_adapter_finalize and
            transaction._ref_count == 0 and
            not isinstance(transaction.current_node.parent, Sentinel)):
        _finalize_transaction(transaction, exc, value, tb)


def _finalize_transaction(transaction, exc=None, value=None, tb=None):
    if transaction._is_finalized:
        _logger.error('Runtime instrumentation error. Attempting to finalize '
                'a transaction which has already been finalized. Please '
                'report this issue to New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))
        return
    old_transaction = replace_current_transaction(transaction)

    try:
        transaction.__exit__(exc, value, tb)

    finally:
        transaction._is_finalized = True
        request = retrieve_transaction_request(transaction)

        if request is not None:
            request._nr_transaction = None
        transaction._nr_current_request = None

        # We place the previous transaction back in the cache unless
        # it is the transaction that just completed.
        if old_transaction != transaction:
            replace_current_transaction(old_transaction)


class TransactionContext(object):
    def __init__(self, transaction):
        self.transaction = transaction

    def __enter__(self):
        self.old_transaction = replace_current_transaction(self.transaction)

    def __exit__(self, exc_type, exc_value, traceback):
        replace_current_transaction(self.old_transaction)


def create_transaction_aware_fxn(fxn, fxn_for_name=None, should_trace=True):
    # Returns a version of fxn that will switch context to the appropriate
    # transaction and then restore the previous transaction on exit.
    # If fxn is already transaction aware or if there is no transaction
    # associated with fxn, this will return None.
    #
    # Arguments:
    #  fxn: The function we want to wrap in a transaction aware context.
    #  fxn_for_name: Defaults to fxn. The function we want to use the get the
    #      name for our transaction aware fxn (by calling
    #      callable_name(fxn_for_name). One may not want to use the default fxn
    #      itself if is wrapped and we want to use the inner function for
    #      naming. This happens, for example, when tornado wraps a function in
    #      stack_context.wrap and we want to wrap the output function.
    #  should_trace: Defaults to True. Usually we want to trace the transaction
    #      aware function. However, to prevent tracing a function multiple
    #      times we may not want to trace a particular function. See our
    #      instrumentation, stack_context._nr_wrapper_stack_context_wrap.

    if fxn is None or hasattr(fxn, '_nr_transaction'):
        return None

    if fxn_for_name is None:
        fxn_for_name = fxn

    # We want to get the transaction associated with this path of execution
    # whether or not we are actively recording information about it.
    transaction = [retrieve_current_transaction()]

    @function_wrapper
    def transaction_aware(wrapped, instance, args, kwargs):
        # Variables from the outer scope are not assignable in a closure,
        # so we use a mutable object to hold the transaction, so we can
        # change it if we need to.
        inner_transaction = transaction[0]

        if inner_transaction is not None:
            # Callback run outside the main thread must not affect the cache
            if inner_transaction.thread_id != current_thread_id():
                return fxn(*args, **kwargs)

        if inner_transaction is not None and inner_transaction._is_finalized:
            inner_transaction = None
            transaction[0] = None

        with TransactionContext(inner_transaction):
            if inner_transaction is None:
                # A transaction will be None for fxns scheduled on the ioloop
                # not associated with a transaction.
                ret = fxn(*args, **kwargs)

            elif should_trace is False:
                try:
                    ret = fxn(*args, **kwargs)
                except:
                    record_exception(sys.exc_info())
                    wrapped._nr_recorded_exception = True
                    raise

            else:
                name = callable_name(fxn_for_name)
                with FunctionTrace(inner_transaction, name=name) as ft:

                    try:
                        ret = fxn(*args, **kwargs)
                    except:
                        record_exception(sys.exc_info())
                        wrapped._nr_recorded_exception = True
                        raise

                    # Coroutines are wrapped in lambdas when they are
                    # scheduled. See tornado.gen.Runner.run(). In this
                    # case, we don't know the name until the function
                    # is run. We only know it then because we pass
                    # out the name as an attribute on the result.
                    # We update the name now.

                    if hasattr(fxn, '_nr_coroutine_name'):
                        ft.name = fxn._nr_coroutine_name

        # If decrementing the ref count in Runner.run() takes it to 0, then
        # we need to end the transaction here.

        if inner_transaction:
            possibly_finalize_transaction(inner_transaction)

        return ret

    return transaction_aware(fxn)


def request_handler_finish_finalize(wrapped, instance, args, kwargs):
    request = instance.request
    transaction = retrieve_request_transaction(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        return wrapped(*args, **kwargs)
    finally:
        transaction._request_handler_finalize = True
        transaction.last_byte_time = request._finish_time
        possibly_finalize_transaction(transaction)


def server_request_adapter_finish_finalize(wrapped, instance, args, kwargs):
    delegate = instance
    while not hasattr(delegate, 'request') or delegate.request is None:
        delegate = delegate.delegate
        if delegate is None:
            break

    transaction = None
    if delegate is not None:
        request = delegate.request
        transaction = retrieve_request_transaction(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        return wrapped(*args, **kwargs)
    finally:
        transaction._server_adapter_finalize = True
        possibly_finalize_transaction(transaction)


def server_request_adapter_on_connection_close_finalize(wrapped,
        instance, args, kwargs):
    if instance.delegate is not None:
        request = instance.delegate.request
    else:
        request = instance.request

    transaction = retrieve_request_transaction(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        return wrapped(*args, **kwargs)
    finally:
        transaction._request_handler_finalize = True
        transaction._server_adapter_finalize = True
        possibly_finalize_transaction(transaction)
