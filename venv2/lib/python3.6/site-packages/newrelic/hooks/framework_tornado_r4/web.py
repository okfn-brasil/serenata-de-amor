import logging
import traceback

from newrelic.api.application import application_instance
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.core.agent import remove_thread_utilization

from newrelic.hooks.framework_tornado_r4.routing import _wrap_handlers

_logger = logging.getLogger(__name__)
_VERSION = None


def _store_version_info():
    import tornado
    global _VERSION

    try:
        _VERSION = '.'.join(map(str, tornado.version_info))
    except:
        pass

    return tornado.version_info


def _get_environ(request):
    # This creates a WSGI environ dictionary from a Tornado request.
    environ = {
        'REQUEST_URI': request.path,
        'QUERY_STRING': request.query,
        'REQUEST_METHOD': request.method,
    }

    try:
        # We only want to record port for ipv4 and ipv6 socket families.
        # Unix socket will just return a string instead of a tuple, so
        # skip this.
        sockname = request.connection.stream.socket.getsockname()
        if isinstance(sockname, tuple):
            environ['SERVER_PORT'] = sockname[1]
    except:
        pass

    for header, value in request.headers.items():
        if header in ('Content-Type', 'Content-Length'):
            wsgi_name = header.replace('-', '_').upper()
        else:
            wsgi_name = 'HTTP_' + header.replace('-', '_').upper()
        environ[wsgi_name] = value

    return environ


def _nr_request_handler_init(wrapped, instance, args, kwargs):
    if current_transaction() is not None:
        _logger.error('Attempting to make a request (new transaction) when a '
                'transaction is already running. Please report this issue to '
                'New Relic support.\n%s',
                ''.join(traceback.format_stack()[:-1]))
        return wrapped(*args, **kwargs)

    def _bind_params(application, request, *args, **kwargs):
        return request

    request = _bind_params(*args, **kwargs)
    environ = _get_environ(request)

    if request.method not in instance.SUPPORTED_METHODS:
        # If the method isn't one of the supported ones, then we expect the
        # wrapped method to raise an exception for HTTPError(405). In this case
        # we name the transaction after the wrapped method.
        name = callable_name(instance)
    else:
        # Otherwise we name the transaction after the handler function that
        # should end up being executed for the request.
        method = getattr(instance, request.method.lower())
        name = callable_name(method)

    environ = _get_environ(request)

    app = application_instance()
    txn = WebTransaction(app, environ)
    txn.__enter__()

    if txn.enabled:
        txn.drop_transaction()
        instance._nr_transaction = txn

    txn.set_transaction_name(name)

    # Record framework information for generation of framework metrics.
    txn.add_framework_info('Tornado/ASYNC', _VERSION)

    return wrapped(*args, **kwargs)


def _nr_process_response(wrapped, instance, args, kwargs):
    if not hasattr(instance, '_headers_written') or instance._headers_written:
        return wrapped(*args, **kwargs)

    if not hasattr(instance, '_nr_transaction'):
        return wrapped(*args, **kwargs)

    transaction = instance._nr_transaction

    get_status = getattr(instance, 'get_status', None)
    try:
        raw_status = get_status()
        skip_cat_header_insertion = raw_status in (204, 304)
        http_status = str(raw_status)
    except:
        skip_cat_header_insertion = True
        http_status = None

    headers = getattr(instance, '_headers', None)
    try:
        headers = list(headers.get_all())
    except:
        pass

    cat_headers = transaction.process_response(http_status, headers)

    if not skip_cat_header_insertion:
        try:
            for k, v in cat_headers:
                instance.set_header(k, v)
        except:
            pass

    return wrapped(*args, **kwargs)


def _nr_application_add_handlers(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    _wrap_handlers(args)
    return result


def instrument_tornado_web(module):

    # Thread utilization data is meaningless in a tornado app. Remove it here,
    # once, since we know that tornado has been imported now. The following
    # call to agent_instance will initialize data sources, if they have not
    # been already. Thus, we know that this is a single place that we can
    # remove the thread utilization, regardless of the order of imports/agent
    # registration.

    remove_thread_utilization()

    wrap_function_wrapper(module, 'RequestHandler.__init__',
            _nr_request_handler_init)
    wrap_function_wrapper(module, 'RequestHandler.flush',
            _nr_process_response)

    version_info = _store_version_info()

    if version_info and version_info < (4, 5):
        wrap_function_wrapper(module, 'Application.add_handlers',
                _nr_application_add_handlers)
