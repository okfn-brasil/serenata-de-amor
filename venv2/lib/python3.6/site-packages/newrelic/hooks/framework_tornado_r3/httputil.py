import logging
import weakref

from newrelic.hooks.framework_tornado_r3.util import purge_current_transaction
from newrelic.api.application import application as application_instance
from newrelic.api.web_transaction import WebTransaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper

_logger = logging.getLogger(__name__)

# We need a request to start monitoring a transaction (or we need to compute
# some values that will be recomputed when the request gets created) so we
# initiate our instrumentation here.
# We may need to handle wsgi apps differently.

def _nr_wrapper_HTTPServerRequest__init__(wrapped, instance, args, kwargs):
    # This is the first point of entry into our instrumentation. It gets called
    # after header but before the request body is read in one of 3 possible
    # places:
    #   web.py: The normal case when the application passed to the HTTPServer
    #     is an Tornado 4 Application object.
    #   httpserver.py: A strange case where the application passed to the
    #     HTTPServer is not a Tornado 4 Application object (so the
    #     HTTPServerAdapter has no delegate).
    #   wsgi.py: Needs more exploration.
    #
    # After this is called the request body may be streamed or not depending on
    # the application configuration (see tornado.web.stream_request_body).

    assert instance is not None

    result = wrapped(*args, **kwargs)

    # instance is now an initiated HTTPServerRequest object. Since instance was
    # just created there can not be a previously associated transaction.

    request = instance

    if is_websocket(request):
        transaction = None
    else:
        transaction = initiate_request_monitoring(request)

    # Transaction can still be None at this point, if it wasn't enabled during
    # WebTransaction.__init__().

    if transaction:

        # Name transaction initially after the wrapped function so that if
        # the connection is dropped before all the request content is read,
        # then we don't get metric grouping issues with it being named after
        # the URL.

        name = callable_name(wrapped)
        transaction.set_transaction_name(name)

        # Use HTTPServerRequest start time as transaction start time.

        transaction.start_time = request._start_time

    # Even if transaction is `None`, we still attach it to the request, so we
    # can distinguish between a missing _nr_transaction attribute (error) from
    # the case where _nr_transaction is None (ok).

    request._nr_transaction = transaction

    return result

def initiate_request_monitoring(request):
    # Creates a new transaction and associates it with the request.
    # We always use the default application specified in the agent
    # configuration.

    application = application_instance()

    # We need to fake up a WSGI like environ dictionary with the key
    # bits of information we need.

    environ = request_environment(request)

    # We now start recording the actual web transaction.

    purge_current_transaction()

    transaction = WebTransaction(application, environ)

    if not transaction.enabled:
        return None

    transaction.__enter__()

    # Immediately purge the transaction from the cache, so we don't associate
    # Tornado internals inappropriately with this transaction.

    purge_current_transaction()

    # We also need to add a reference to the request object in to the
    # transaction object so we can later access it in a deferred. We
    # need to use a weakref to avoid an object cycle which may prevent
    # cleanup of the transaction.

    transaction._nr_current_request = weakref.ref(request)

    # Records state of transaction

    transaction._is_finalized = False
    transaction._ref_count = 0

    # For requests that complete normally, a transaction can only be closed
    # after the `finish()` method is called on both the `_ServerRequestAdapter`
    # and the `RequestHandler`.

    transaction._request_handler_finalize = False
    transaction._server_adapter_finalize = False

    # Record framework information for generation of framework metrics.

    import tornado

    if hasattr(tornado, 'version_info'):
        version = '.'.join(map(str, tornado.version_info))
    else:
        version = None

    transaction.add_framework_info('Tornado/ASYNC', version)

    return transaction

def request_environment(request):
    # This creates a WSGI environ dictionary from a Tornado request.

    environ = {}

    environ['REQUEST_URI'] = request.uri
    environ['QUERY_STRING'] = request.query
    environ['REQUEST_METHOD'] = request.method

    for header, value in request.headers.items():
        if header in ['Content-Type', 'Content-Length']:
            wsgi_name = header.replace('-', '_').upper()
        else:
            wsgi_name = 'HTTP_' + header.replace('-', '_').upper()
        environ[wsgi_name] = value

    from tornado.httputil import split_host_and_port
    port = split_host_and_port(request.host.lower())[1]
    if port:
        environ['SERVER_PORT'] = port

    return environ

def is_websocket(request):
    return request.headers.get('Upgrade', '').lower() == 'websocket'

def _nr_wrapper__NormalizedHeaderCache___missing__(
        wrapped, instance, args, kwargs):

    if instance is None:
        def _bind_params(self, key, *args, **kwargs):
            return self, key

        instance, key = _bind_params(*args, **kwargs)

    else:
        def _bind_params(key, *args, **kwargs):
            return key

        key = _bind_params(*args, **kwargs)

    normalized = wrapped(*args, **kwargs)

    if key.startswith('X-NewRelic'):
        instance[key] = key
        return key

    return normalized

def instrument_tornado_httputil(module):
    wrap_function_wrapper(module, 'HTTPServerRequest.__init__',
            _nr_wrapper_HTTPServerRequest__init__)
    wrap_function_wrapper(module, '_NormalizedHeaderCache.__missing__',
            _nr_wrapper__NormalizedHeaderCache___missing__)
