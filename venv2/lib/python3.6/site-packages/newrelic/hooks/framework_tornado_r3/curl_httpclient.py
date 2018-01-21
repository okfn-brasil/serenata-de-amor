from newrelic.hooks.framework_tornado_r3.util import (
        retrieve_current_transaction, possibly_finalize_transaction)
from newrelic.common.object_wrapper import (function_wrapper,
        wrap_function_wrapper)


def _nr_wrapper_curl_httpclient_CurlAsyncHTTPClient_fetch_impl_(wrapped,
        instance, args, kwargs):

    def _bind_params(request, callback, *args, **kwargs):
        return request, callback

    request, callback = _bind_params(*args, **kwargs)

    # There's a delay between when streaming_callback is wrapped (and the
    # transaction is attached) and when it gets added to the IOLoop (no
    # transaction in the Transaction Cache).
    #
    # We want to bypass the check that makes sure the transaction in the
    # Transaction Cache matches the transaction attached to the callback
    # in order to add the callback without producing a logged error.
    #
    # Setting `_nr_transaction` to `None` will:
    #   1. Allow the callback to be added to the IOLoop without error message.
    #   2. Prevent transaction._ref_count from incrementing when added.
    #   3. Prevent transaction._ref_count from decrementing when run.
    #
    # Note that streaming_callback will still be traced when it runs.

    if request.streaming_callback:
        request.streaming_callback._nr_transaction = None

    if callback:
        transaction = retrieve_current_transaction()

        if transaction:
            transaction._ref_count += 1

            @function_wrapper
            def _nr_wrapper_decrementer(_wrapped, _instance, _args, _kwargs):
                try:
                    return _wrapped(*_args, **_kwargs)
                finally:
                    transaction._ref_count -= 1
                    possibly_finalize_transaction(transaction)

            wrapped_callback = _nr_wrapper_decrementer(callback)

            # Replace callback with one that will decrement the ref_count
            # when it runs.

            if len(args) > 1:
                args = list(args)
                args[1] = wrapped_callback
            else:
                kwargs['callback'] = wrapped_callback

    return wrapped(*args, **kwargs)


def instrument_tornado_curl_httpclient(module):
    wrap_function_wrapper(module, 'CurlAsyncHTTPClient.fetch_impl',
            _nr_wrapper_curl_httpclient_CurlAsyncHTTPClient_fetch_impl_)
