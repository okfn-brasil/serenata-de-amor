import sys
import logging

from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        FunctionWrapper)

from newrelic.hooks.framework_tornado import (retrieve_transaction_request,
        request_finished, suspend_request_monitoring,
        resume_request_monitoring, finalize_request_monitoring,
        record_exception, retrieve_current_transaction)

_logger = logging.getLogger(__name__)

module_stack_context = None

def _nr_stack_context_wrap_wrapped_(request):

    def _nr_stack_context_function_wrapper_(wrapped, instance, args, kwargs):

        # We can come in here with either an active transaction
        # or a request with a transaction bound to it. If there
        # is an active transaction then call the wrapped function
        # within function trace and return immediately.

        transaction = retrieve_current_transaction()

        if transaction is not None:
            name = callable_name(wrapped)

            with FunctionTrace(transaction, name=name):
                return wrapped(*args, **kwargs)

        # For the case of a request with a transaction bound to
        # it, we need to resume the transaction and then call it.
        # As we resumed the transaction, need to handle
        # suspending or finalizing it.

        transaction = resume_request_monitoring(request)

        if transaction is None:
            return wrapped(*args, **kwargs)

        try:
            name = callable_name(wrapped)

            with FunctionTrace(transaction, name=name):
                return wrapped(*args, **kwargs)

        except:  # Catch all.
            record_exception(transaction, sys.exc_info())
            raise

        finally:
            if not request_finished(request):
                suspend_request_monitoring(request, name='Callback/Wait')

            elif not request.connection.stream.writing():
                finalize_request_monitoring(request)

            else:
                suspend_request_monitoring(request, name='Request/Output')

    return _nr_stack_context_function_wrapper_

def _nr_stack_context_wrap_wrapper_(wrapped, instance, args, kwargs):
    def _args(fn, *args, **kwargs):
        return fn

    transaction = retrieve_current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    request = retrieve_transaction_request(transaction)

    if request is None:
        return wrapped(*args, **kwargs)

    fn = _args(*args, **kwargs)

    # We need to filter out certain out types of wrapped functions.
    # Tornado 3.1 doesn't use _StackContextWrapper and checks for a
    # '_wrapped' attribute instead which makes this a bit more fragile.

    if hasattr(module_stack_context, '_StackContextWrapper'):
        if (fn is None or
                fn.__class__ is module_stack_context._StackContextWrapper):
            return fn
    else:
        if fn is None or hasattr(fn, '_wrapped'):
            return fn

    fn = FunctionWrapper(fn, _nr_stack_context_wrap_wrapped_(request))

    return wrapped(fn)

def instrument_tornado_stack_context(module):
    global module_stack_context
    module_stack_context = module

    wrap_function_wrapper(module, 'wrap', _nr_stack_context_wrap_wrapper_)
