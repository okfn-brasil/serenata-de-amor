import functools

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.hooks.external_httplib import httplib_connect_wrapper

def _nr_wrapper_make_request_(wrapped, instance, args, kwargs, scheme):

    def _bind_params(conn, method, url, *args, **kwargs):
        return "%s://%s:%s" % (scheme, conn.host, conn.port)

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    url_for_apm_ui = _bind_params(*args, **kwargs)

    with ExternalTrace(transaction, 'urllib3', url_for_apm_ui):
        return wrapped(*args, **kwargs)

def instrument_urllib3_connectionpool(module):
    wrap_function_wrapper(module, 'HTTPConnectionPool._make_request',
            functools.partial(_nr_wrapper_make_request_, scheme='http'))
    wrap_function_wrapper(module, 'HTTPSConnectionPool._make_request',
            functools.partial(_nr_wrapper_make_request_, scheme='https'))

def instrument_urllib3_connection(module):

    # Don't combine the instrument functions into a single function. Keep
    # the 'connect' monkey patch separate, because it is also used to patch
    # urllib3 within the requests package.

    wrap_function_wrapper(module, 'HTTPConnection.connect',
        functools.partial(httplib_connect_wrapper, scheme='http',
                library="urllib3"))

    wrap_function_wrapper(module, 'HTTPSConnection.connect',
        functools.partial(httplib_connect_wrapper, scheme='https',
                library="urllib3"))
