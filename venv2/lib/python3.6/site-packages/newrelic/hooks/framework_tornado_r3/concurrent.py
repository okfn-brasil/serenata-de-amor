from newrelic.hooks.framework_tornado_r3.util import (
        retrieve_current_transaction, create_transaction_aware_fxn)
from newrelic.common.object_wrapper import wrap_function_wrapper


def _nr_wrapper_Future_add_done_callback(wrapped, instance, args, kwargs):
    def _fxn_arg_extractor(fn, *args, **kwargs):
        return fn

    fxn = _fxn_arg_extractor(*args, **kwargs)

    should_trace = not hasattr(fxn, '_nr_last_object')

    # In Tornado, the coroutine runs inside of a lambda or a closure. In this
    # case, we don't know the name of the actual function until it's run. The
    # name is passed as an attribute on the future.
    if hasattr(instance, '_nr_coroutine_name'):
        old_fxn = fxn

        def new_fxn(*_args, **_kwargs):
            return old_fxn(*_args, **_kwargs)

        fxn = new_fxn
        fxn._nr_coroutine_name = instance._nr_coroutine_name

        # Clear name off of future in case the future is reused
        delattr(instance, '_nr_coroutine_name')

    transaction_aware_fxn = create_transaction_aware_fxn(fxn,
            should_trace=should_trace)

    # If transaction_aware_fxn is None then it is already wrapped, or the fxn
    # is None.
    if transaction_aware_fxn is None:
        return wrapped(*args, **kwargs)

    transaction = retrieve_current_transaction()

    transaction_aware_fxn._nr_transaction = transaction

    # We replace the function we call in the callback with the transaction
    # aware version of the function.
    if len(args) > 0:
        args = list(args)
        args[0] = transaction_aware_fxn
    else:
        # Keyword argument name for the callable function is 'fn'.
        kwargs['fn'] = transaction_aware_fxn

    return wrapped(*args, **kwargs)


def instrument_concurrent(module):

    # This is for instrumenting both tornado futures and python native futures

    wrap_function_wrapper(module, 'Future.add_done_callback',
            _nr_wrapper_Future_add_done_callback)
