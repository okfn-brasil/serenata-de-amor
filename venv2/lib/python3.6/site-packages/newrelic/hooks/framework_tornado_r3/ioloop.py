import logging
import sys
import traceback

from newrelic.hooks.framework_tornado_r3.util import (
        possibly_finalize_transaction, record_exception,
        retrieve_current_transaction, current_thread_id, TransactionContext)
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.core.agent import remove_thread_utilization

_logger = logging.getLogger(__name__)


def _nr_wrapper_IOLoop__run_callback_(wrapped, instance, args, kwargs):
    # callback in wrapped in functools.partial so to get the actual callback
    # we need to grab the func attribute.
    # TODO(bdirks): asyncio and twisted override add_callback but should still
    # work. See tornado-4.2/tornado/platform/(asyncio|twisted).py. We should
    # explicitly test this.
    def _callback_extractor(callback, *args, **kwargs):
        try:
            return callback.func
        except:
            _logger.error('Runtime instrumentation error. A callback is '
                    'registered on the ioloop that isn\'t wrapped in '
                    'functools.partial. Perhaps a nonstandard IOLoop is being'
                    'used?')
            return None

    callback = _callback_extractor(*args, **kwargs)
    transaction = getattr(callback, '_nr_transaction', None)

    ret = wrapped(*args, **kwargs)

    if transaction is not None:
        transaction._ref_count -= 1

        # Finalize the transaction if this is the last callback.
        possibly_finalize_transaction(callback._nr_transaction)

    return ret


def _nr_wrapper_IOLoop_handle_callback_exception_(
        wrapped, instance, args, kwargs):

    def _callback_extractor(callback, *args, **kwargs):
        return callback

    cb = _callback_extractor(*args, **kwargs)

    if hasattr(cb, 'func'):
        if not (hasattr(cb.func, '_nr_last_object') and
                hasattr(cb.func._nr_last_object, '_nr_recorded_exception')):
            record_exception(sys.exc_info())
    else:
        # If cb is an unexpected form (ie it's not a callback wrapped in a
        # partial function) we record an error against the app. This can
        # happen, for example, when too many file handles get opened and cb
        # will be a tuple of the form: (socketobject, FunctionWrapper).
        record_exception(sys.exc_info())

    return wrapped(*args, **kwargs)


def _increment_ref_count(callback, wrapped, instance, args, kwargs):
    transaction = retrieve_current_transaction()

    if hasattr(callback, '_nr_transaction'):

        if callback._nr_transaction is not None:
            if current_thread_id() != callback._nr_transaction.thread_id:
                # Callback being added not in the main thread; ignore.

                # Since we are not incrementing the counter for this callback,
                # we need to remove the transaction from the callback, so it
                # doesn't get decremented either.
                callback._nr_transaction = None
                return wrapped(*args, **kwargs)

        if transaction is not callback._nr_transaction:
            _logger.error('Attempt to add callback to ioloop with different '
                    'transaction attached than in the cache. Please report '
                    'this issue to New Relic support.\n%s',
                    ''.join(traceback.format_stack()[:-1]))

            # Since we are not incrementing the counter for this callback, we
            # need to remove the transaction from the callback, so it doesn't
            # get decremented either.
            callback._nr_transaction = None
            return wrapped(*args, **kwargs)

    if transaction is None:
        return wrapped(*args, **kwargs)

    transaction._ref_count += 1

    return wrapped(*args, **kwargs)


def _nr_wrapper_PollIOLoop_add_callback(wrapped, instance, args, kwargs):

    def _callback_extractor(callback, *args, **kwargs):
        return callback
    callback = _callback_extractor(*args, **kwargs)

    return _increment_ref_count(callback, wrapped, instance, args, kwargs)


def _nr_wrapper_PollIOLoop_call_at(wrapped, instance, args, kwargs):

    with TransactionContext(None):
        return wrapped(*args, **kwargs)


def _nr_wrapper_PollIOLoop_add_handler(wrapped, instance, args, kwargs):

    with TransactionContext(None):
        return wrapped(*args, **kwargs)


def _nr_wrapper_PollIOLoop_add_callback_from_signal(wrapped, instance, args,
        kwargs):

    with TransactionContext(None):
        return wrapped(*args, **kwargs)


def instrument_tornado_ioloop(module):

    # Thread utilization data is meaningless in a tornado app. Remove it here,
    # once, since we know that tornado has been imported now. The following
    # call to agent_instance will initialize data sources, if they have not
    # been already. Thus, we know that this is a single place that we can
    # remove the thread utilization, regardless of the order of imports/agent
    # registration.

    remove_thread_utilization()

    wrap_function_wrapper(module, 'IOLoop._run_callback',
            _nr_wrapper_IOLoop__run_callback_)
    wrap_function_wrapper(module, 'IOLoop.handle_callback_exception',
            _nr_wrapper_IOLoop_handle_callback_exception_)
    wrap_function_wrapper(module, 'PollIOLoop.add_callback',
            _nr_wrapper_PollIOLoop_add_callback)
    wrap_function_wrapper(module, 'PollIOLoop.call_at',
            _nr_wrapper_PollIOLoop_call_at)
    wrap_function_wrapper(module, 'PollIOLoop.add_handler',
            _nr_wrapper_PollIOLoop_add_handler)
    wrap_function_wrapper(module, 'PollIOLoop.add_callback_from_signal',
            _nr_wrapper_PollIOLoop_add_callback_from_signal)


def instrument_tornado_asyncio_loop(module):
    wrap_function_wrapper(module, 'AsyncIOLoop.add_callback',
            _nr_wrapper_PollIOLoop_add_callback)
    wrap_function_wrapper(module, 'AsyncIOLoop.call_at',
            _nr_wrapper_PollIOLoop_call_at)
    wrap_function_wrapper(module, 'AsyncIOLoop.add_handler',
            _nr_wrapper_PollIOLoop_add_handler)
    wrap_function_wrapper(module, 'AsyncIOLoop.add_callback_from_signal',
            _nr_wrapper_PollIOLoop_add_callback_from_signal)
