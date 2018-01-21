import functools

from newrelic.packages import six

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import ObjectWrapper

def httplib_connect_wrapper(wrapped, instance, args, kwargs, scheme, library):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _connect_unbound(instance, *args, **kwargs):
        return instance

    if instance is None:
        instance = _connect_unbound(*args, **kwargs)

    connection = instance

    url = '%s://%s:%s' % (scheme, connection.host, connection.port)

    with ExternalTrace(transaction, library=library, url=url) as tracer:
        # Add the tracer to the connection object. The tracer will be
        # used in getresponse() to add back into the external trace,
        # after the trace has already completed, details from the
        # response headers.

        connection._nr_external_tracer = tracer

        return wrapped(*args, **kwargs)

def httplib_endheaders_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    connection = instance

    # Check if the NR headers have already been added. This is just in
    # case a higher level library which uses httplib underneath so
    # happened to have been instrumented to also add the headers.

    try:
        skip_headers = getattr(connection, '_nr_skip_headers', False)

        if skip_headers:
            return wrapped(*args, **kwargs)

        outgoing_headers = ExternalTrace.generate_request_headers(transaction)
        for header_name, header_value in outgoing_headers:
            connection.putheader(header_name, header_value)

        return wrapped(*args, **kwargs)

    finally:
        try:
            del connection._nr_skip_headers
        except AttributeError:
            pass

def httplib_getresponse_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    connection = instance
    tracer = getattr(connection, '_nr_external_tracer', None)

    if not tracer:
        return wrapped(*args, **kwargs)

    response = wrapped(*args, **kwargs)

    # Make sure we remove the tracer from the connection object so that it
    # doesn't hold onto objects. Do this after we call the wrapped function so
    # if an exception occurs the higher library might retry the call again with
    # the same connection object. Both urllib3 and requests do this in Py2.7

    del connection._nr_external_tracer

    if hasattr(tracer, 'process_response_headers'):
        tracer.process_response_headers(response.getheaders())

    return response

def httplib_putheader_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    # Remember if we see any NR headers being set. This is only doing
    # it if we see either, but they should always both be getting set.

    def nr_header(header, *args, **kwargs):
        return header.upper() in ('X-NEWRELIC-ID', 'X-NEWRELIC-TRANSACTION')

    connection = instance

    if nr_header(*args, **kwargs):
        connection._nr_skip_headers = True

    return wrapped(*args, **kwargs)

def instrument(module):

    if six.PY2:
        library = 'httplib'
    else:
        library = 'http'


    module.HTTPConnection.connect = ObjectWrapper(
            module.HTTPConnection.connect,
            None,
            functools.partial(httplib_connect_wrapper, scheme='http',
                    library=library))

    module.HTTPSConnection.connect = ObjectWrapper(
            module.HTTPSConnection.connect,
            None,
            functools.partial(httplib_connect_wrapper, scheme='https',
                    library=library))

    module.HTTPConnection.endheaders = ObjectWrapper(
            module.HTTPConnection.endheaders,
            None,
            httplib_endheaders_wrapper
            )

    module.HTTPConnection.getresponse = ObjectWrapper(
            module.HTTPConnection.getresponse,
            None,
            httplib_getresponse_wrapper
            )

    module.HTTPConnection.putheader = ObjectWrapper(
            module.HTTPConnection.putheader,
            None,
            httplib_putheader_wrapper
            )
