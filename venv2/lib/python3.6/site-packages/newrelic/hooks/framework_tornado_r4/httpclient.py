import sys

from newrelic.api.transaction import current_transaction
from newrelic.api.external_trace import ExternalTrace
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        function_wrapper)


def _prepare_request(*args, **kwargs):
    from tornado.httpclient import HTTPRequest

    def _extract_request(request, callback=None, raise_error=True, **_kwargs):
        return request, callback, raise_error, _kwargs

    request, callback, raise_error, _kwargs = _extract_request(*args,
            **kwargs)

    # request is either a string or a HTTPRequest object
    if not isinstance(request, HTTPRequest):
        url = request
        request = HTTPRequest(url, **_kwargs)

    return request, callback, raise_error


def wrap_handle_response(raise_error, trace):
    @function_wrapper
    def wrapper(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)

        def _bind_params(response, *args, **kwargs):
            return response

        response = _bind_params(*args, **kwargs)

        # Process CAT response headers
        trace.process_response_headers(response.headers.get_all())

        trace.__exit__(None, None, None)

        return result
    return wrapper


@function_wrapper
def wrap_fetch_impl(wrapped, instance, args, kwargs):
    _nr_args = getattr(instance, '_nr_args', None)

    if not _nr_args:
        return wrapped(*args, **kwargs)

    def _bind_params(request, callback, *args, **kwargs):
        return request, callback

    request, handle_response = _bind_params(*args, **kwargs)
    wrapped_handle_response = wrap_handle_response(*_nr_args)(handle_response)

    return wrapped(request, wrapped_handle_response)


def _nr_wrapper_httpclient_AsyncHTTPClient_fetch_(
        wrapped, instance, args, kwargs):

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        req, _cb, _raise_error = _prepare_request(*args, **kwargs)
    except:
        return wrapped(*args, **kwargs)

    # Prepare outgoing CAT headers
    outgoing_headers = ExternalTrace.generate_request_headers(transaction)
    for header_name, header_value in outgoing_headers:
        # User headers should override our CAT headers
        if header_name in req.headers:
            continue
        req.headers[header_name] = header_value

    # wrap the fetch_impl on the unbound method
    instance_type = type(instance)
    if not hasattr(instance_type, '_nr_wrapped'):
        instance_type.fetch_impl = wrap_fetch_impl(instance_type.fetch_impl)
        instance_type._nr_wrapped = True

    trace = ExternalTrace(transaction,
            'tornado.httpclient', req.url, req.method.upper())
    instance._nr_args = (_raise_error, trace)
    trace.__enter__()
    if trace.transaction and trace.transaction.current_node is trace:
        # externals should not have children
        trace.transaction._pop_current(trace)

    try:
        future = wrapped(req, _cb, _raise_error)
    except Exception:
        trace.__exit__(*sys.exc_info())
        raise
    return future


def instrument_tornado_httpclient(module):
    wrap_function_wrapper(module, 'AsyncHTTPClient.fetch',
            _nr_wrapper_httpclient_AsyncHTTPClient_fetch_)
