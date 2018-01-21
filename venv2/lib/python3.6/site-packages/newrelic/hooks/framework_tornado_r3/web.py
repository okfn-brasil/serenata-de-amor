import logging
import traceback
import sys

from newrelic.hooks.framework_tornado_r3.util import (
        retrieve_current_transaction, retrieve_request_transaction,
        record_exception, TransactionContext, request_handler_finish_finalize)
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (function_wrapper,
        wrap_function_wrapper)

_logger = logging.getLogger(__name__)

def _find_defined_class(meth):
    # Returns the name of the class where the bound function method 'meth'
    # is implemented.
    mro = meth.__self__.__class__.__mro__
    for cls in mro:
        if meth.__name__ in cls.__dict__:
            return cls.__name__
    return None

def _nr_wrapper_RequestHandler__execute_(wrapped, instance, args, kwargs):
    handler = instance
    request = handler.request

    if request is None:
        _logger.error('Runtime instrumentation error. Calling _execute on '
                'a RequestHandler when no request is present. Please '
                'report this issue to New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))
        return wrapped(*args, **kwargs)

    transaction = retrieve_request_transaction(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    if request.method not in handler.SUPPORTED_METHODS:
        # If the method isn't one of the supported ones, then we expect the
        # wrapped method to raise an exception for HTTPError(405). In this case
        # we name the transaction after the wrapped method.
        name = callable_name(wrapped)
    else:
        # Otherwise we name the transaction after the handler function that
        # should end up being executed for the request.
        name = callable_name(getattr(handler, request.method.lower()))

    transaction.set_transaction_name(name)

    # We need to set the current transaction so that the user code executed by
    # running _execute is traced to the transaction we grabbed off the request

    with TransactionContext(transaction):
      return wrapped(*args, **kwargs)

def _nr_wrapper_RequestHandler__handle_request_exception_(wrapped, instance,
        args, kwargs):

    transaction = retrieve_request_transaction(instance.request)
    with TransactionContext(transaction):
        # sys.exc_info() will have the correct exception context.
        # _handle_request_exception is private to tornado's web.py and also uses
        # sys.exc_info. The exception context has explicitly set the type, value,
        # and traceback.
        record_exception(sys.exc_info())
        return wrapped(*args, **kwargs)

# The following 2 methods are used to trace request handler member functions.
@function_wrapper
def _requesthandler_transaction_function_trace(wrapped, instance, args, kwargs):
    # Use this function tracer when the function you want to trace is called
    # synchronously from a function that is not run inside the transaction,
    # such as http1connection.HTTP1Connection._read_message.
    request = instance.request
    transaction = retrieve_request_transaction(request)

    if transaction is None:
        # If transaction is None we don't want to trace this function.
        return wrapped(*args, **kwargs)

    with TransactionContext(transaction):
        name = callable_name(wrapped)
        with FunctionTrace(transaction, name=name):
            return wrapped(*args, **kwargs)

@function_wrapper
def _requesthandler_function_trace(wrapped, instance, args, kwargs):
    # Use this function tracer when a function you want to trace is called
    # synchronously from a function that is already in the transaction, such as
    # web.RequestHandler._execute.
    transaction = retrieve_current_transaction()

    name = callable_name(wrapped)
    with FunctionTrace(transaction, name=name):
        return wrapped(*args, **kwargs)

def _nr_wrapper_RequestHandler__init__(wrapped, instance, args, kwargs):

    methods = ['head', 'get', 'post', 'delete', 'patch', 'put', 'options']

    for method in methods:
        func = getattr(instance, method, None)

        # Check `_nr_last_object` attribute to see if we've already
        # wrapped func. For instance, if the method has been decorated
        # with `@tornado.gen.coroutine`, then we've already wrapped it,
        # so we don't want to wrap it again.

        if func is not None and not hasattr(func, '_nr_last_object'):
            wrapped_func = _requesthandler_function_trace(func)
            setattr(instance, method, wrapped_func)

    # Only instrument prepare or on_finish if it has been re-implemented by
    # the user, the stubs on RequestHandler are meaningless noise.

    if _find_defined_class(instance.prepare) != 'RequestHandler':
        instance.prepare = _requesthandler_function_trace(instance.prepare)

    if _find_defined_class(instance.on_finish) != 'RequestHandler':
        instance.on_finish = _requesthandler_function_trace(instance.on_finish)

    if _find_defined_class(instance.data_received) != 'RequestHandler':
        instance.data_received =  _requesthandler_transaction_function_trace(
                instance.data_received)

    # A user probably has not overridden on_connection_close but we want to
    # associate it with the transaction since it indicates a bad end state.
    instance.on_connection_close = _requesthandler_transaction_function_trace(
        instance.on_connection_close)

    return wrapped(*args, **kwargs)

def _nr_wrapper_RequestHandler_finish_(wrapped, instance, args, kwargs):
    return request_handler_finish_finalize(wrapped, instance, args, kwargs)

def instrument_tornado_web(module):
    wrap_function_wrapper(module, 'RequestHandler._execute',
            _nr_wrapper_RequestHandler__execute_)
    wrap_function_wrapper(module, 'RequestHandler._handle_request_exception',
            _nr_wrapper_RequestHandler__handle_request_exception_)
    wrap_function_wrapper(module, 'RequestHandler.__init__',
            _nr_wrapper_RequestHandler__init__)
    wrap_function_wrapper(module, 'RequestHandler.finish',
            _nr_wrapper_RequestHandler_finish_)
