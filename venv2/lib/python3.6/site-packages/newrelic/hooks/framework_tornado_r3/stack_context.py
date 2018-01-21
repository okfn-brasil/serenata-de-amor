from newrelic.hooks.framework_tornado_r3.util import (
        create_transaction_aware_fxn, record_exception,
        retrieve_current_transaction)
from newrelic.common.object_wrapper import wrap_function_wrapper

def _nr_wrapper_stack_context_wrap_(wrapped, instance, args, kwargs):
    # Lots of wrapping going on here. There's the original function, and
    # then 2 layers of wrapping around it.
    #
    # unwrapped_fxn (unwrapped original):
    #     The original function passed into `stack_context.wrap()`.
    #
    # wrapped_fxn (wrapped by Tornado):
    #    The resulting function after `unwrapped_fxn` has been wrapped by
    #    `stack_context.wrap()`.
    #
    # transaction_aware_fxn (wrapped by NR agent):
    #    The resulting function after our `create_transaction_aware_fxn()`
    #    has wrapped `wrapped_fxn` and associated it with the current
    #    transaction.

    def _fxn_arg_extractor(fn, *args, **kwargs):
        # fn is the name of the callable argument in stack_context.wrap
        return fn

    unwrapped_fxn = _fxn_arg_extractor(*args, **kwargs)
    wrapped_fxn = wrapped(*args, **kwargs)

    should_trace = not hasattr(unwrapped_fxn, '_nr_last_object')

    # There are circumstances we want to make a function transaction aware
    # even if we don't want to trace it. If a function is decorated with
    # @function_trace, it will be traced but it will not yet be linked to a
    # transaction. Calling create_transaction_aware_fxn with
    # `should_trace=False` will link the transaction to the function without
    # re-tracing it.
    transaction_aware_fxn = create_transaction_aware_fxn(wrapped_fxn,
            fxn_for_name=unwrapped_fxn, should_trace=should_trace)

    if transaction_aware_fxn is None:
        return wrapped_fxn

    # To prevent stack_context.wrap from re-wrapping this function we attach
    # Tornado's attribute indicating the function was wrapped here.
    transaction_aware_fxn._wrapped = True

    # To prevent us from re-wrapping and to associate the transaction with the
    # function, we attach the transaction as an attribute.
    transaction_aware_fxn._nr_transaction = retrieve_current_transaction()

    return transaction_aware_fxn

# When an exception occurs in a stack context wrapped function,
# _handle_exception is called. We wrap it to record the exception.
def _nr_wrapper_handle_exception_(wrapped, instance, args, kwargs):

    # We extract the exception passed in. This handler is called from outside
    # an except block. In python3, sys.exc_info() will be cleared when the
    # except block exits (this is more aggressive clearing than occurs in
    # python2) so we can't call sys.exc_info() to record the exception.
    # Instead we retrieve the exception from the argument passed in.

    def _exc_extractor(tail, exc, *args, **kwargs):
        return exc

    exc = _exc_extractor(*args, **kwargs)

    record_exception(exc)
    return wrapped(*args, **kwargs)

def instrument_tornado_stack_context(module):
    wrap_function_wrapper(module, 'wrap', _nr_wrapper_stack_context_wrap_)
    wrap_function_wrapper(module, '_handle_exception',
            _nr_wrapper_handle_exception_)
