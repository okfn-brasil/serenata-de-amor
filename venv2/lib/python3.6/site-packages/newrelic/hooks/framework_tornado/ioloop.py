from newrelic.api.function_trace import wrap_function_trace, FunctionTrace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper

from newrelic.hooks.framework_tornado import retrieve_current_transaction

def _nr_wrapper_IOLoop_add_callback_(wrapped, instance, args, kwargs):
    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    def _args(callback, *args, **kwargs):
        return callback

    callback = _args(*args, **kwargs)

    params = dict(callback=callable_name(callback))

    with FunctionTrace(transaction, name, params=params, terminal=True):
        return wrapped(*args, **kwargs)

def _nr_wrapper_IOLoop_add_future_(wrapped, instance, args, kwargs):
    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    def _args(future, callback, *args, **kwargs):
        return future, callback

    future, callback = _args(*args, **kwargs)

    params = dict(callback=callable_name(callback))

    with FunctionTrace(transaction, name, params=params, terminal=True):
        return wrapped(*args, **kwargs)

def instrument_tornado_ioloop(module):
    wrap_function_trace(module, 'IOLoop.add_handler')
    wrap_function_trace(module, 'IOLoop.add_timeout')

    wrap_function_wrapper(module, 'IOLoop.add_callback',
            _nr_wrapper_IOLoop_add_callback_)

    if hasattr(module.IOLoop, 'add_future'):
        wrap_function_wrapper(module, 'IOLoop.add_future',
                _nr_wrapper_IOLoop_add_future_)

    if hasattr(module, 'PollIOLoop'):
        wrap_function_trace(module, 'PollIOLoop.add_handler')
        wrap_function_trace(module, 'PollIOLoop.add_timeout')

        wrap_function_wrapper(module, 'PollIOLoop.add_callback',
                _nr_wrapper_IOLoop_add_callback_)

        wrap_function_trace(module, 'PollIOLoop.add_callback_from_signal')
