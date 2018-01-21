import sys

from newrelic.hooks.framework_tornado_r3.util import (
        retrieve_current_transaction)
from newrelic.api.external_trace import ExternalTrace
from newrelic.common.object_wrapper import wrap_function_wrapper


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


def _nr_wrapper_httpclient_AsyncHTTPClient_fetch_(
        wrapped, instance, args, kwargs):

    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    req, _cb, _raise_error = _prepare_request(*args, **kwargs)

    # Prepare outgoing CAT headers
    outgoing_headers = ExternalTrace.generate_request_headers(transaction)
    for header_name, header_value in outgoing_headers:
        req.headers[header_name] = header_value

    trace = ExternalTrace(transaction, 'tornado.httpclient', req.url)

    def external_trace_done(future):
        exc_info = future.exc_info()
        if exc_info:
            trace.__exit__(*exc_info)
        else:
            response = future.result()
            # Process CAT response headers
            trace.process_response_headers(response.headers.get_all())
            trace.__exit__(None, None, None)
        transaction._ref_count -= 1

    transaction._ref_count += 1
    trace.__enter__()

    # Because traces are terminal but can be generated concurrently in
    # tornado, pop the trace immediately after entering.
    if trace.transaction and trace.transaction.current_node is trace:
        trace.transaction._pop_current(trace)

    try:
        future = wrapped(req, _cb, _raise_error)
        future.add_done_callback(external_trace_done)
    except Exception:
        transaction._ref_count -= 1
        trace.__exit__(*sys.exc_info())
        raise
    return future


def instrument_tornado_httpclient(module):
    wrap_function_wrapper(module, 'AsyncHTTPClient.fetch',
            _nr_wrapper_httpclient_AsyncHTTPClient_fetch_)
