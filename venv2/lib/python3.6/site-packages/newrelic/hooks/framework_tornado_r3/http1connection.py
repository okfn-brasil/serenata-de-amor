from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper


def _nr_wrapper_HTTP1Connection_write_headers_(wrapped, instance, args,
        kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    # Only add response headers when we're a server!

    if instance.is_client:
        return wrapped(*args, **kwargs)

    def _bind_params(start_line, headers, *args, **kwargs):
        return start_line, headers

    start_line, headers = _bind_params(*args, **kwargs)

    try:
        http_status = str(start_line[1])
    except:
        cat_headers = []
    else:
        cat_headers = transaction.process_response(http_status, headers)

    for k, v in cat_headers:
        headers[k] = v

    return wrapped(*args, **kwargs)


def instrument_tornado_http1connection(module):
    wrap_function_wrapper(module, 'HTTP1Connection.write_headers',
            _nr_wrapper_HTTP1Connection_write_headers_)
