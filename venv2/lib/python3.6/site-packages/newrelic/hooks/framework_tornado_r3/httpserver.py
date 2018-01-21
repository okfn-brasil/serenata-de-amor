import logging

from newrelic.hooks.framework_tornado_r3.util import (
        server_request_adapter_finish_finalize,
        server_request_adapter_on_connection_close_finalize)
from newrelic.common.object_wrapper import wrap_function_wrapper

_logger = logging.getLogger(__name__)

# For every request either finish() or on_connection_close() is called on the
# _ServerRequestAdapter. We require that one of these methods is called before
# the transaction is allowed to be finalized.


def _nr_wrapper__ServerRequestAdapter_on_connection_close_(wrapped, instance,
        args, kwargs):
    return server_request_adapter_on_connection_close_finalize(wrapped,
            instance, args, kwargs)


def _nr_wrapper__ServerRequestAdapter_finish_(wrapped, instance,
        args, kwargs):
    return server_request_adapter_finish_finalize(wrapped, instance, args,
            kwargs)


def _nr_wrapper__HTTPServer_start_request_(wrapped, instance,
        args, kwargs):

    delegate = wrapped(*args, **kwargs)

    wrap_function_wrapper(delegate, 'on_connection_close',
            _nr_wrapper__ServerRequestAdapter_on_connection_close_)
    wrap_function_wrapper(delegate, 'finish',
            _nr_wrapper__ServerRequestAdapter_finish_)

    return delegate


def instrument_tornado_httpserver(module):

    if hasattr(module, '_ServerRequestAdapter'):
        wrap_function_wrapper(module,
                '_ServerRequestAdapter.on_connection_close',
                _nr_wrapper__ServerRequestAdapter_on_connection_close_)
        wrap_function_wrapper(module, '_ServerRequestAdapter.finish',
                _nr_wrapper__ServerRequestAdapter_finish_)
    else:
        wrap_function_wrapper(module, 'HTTPServer.start_request',
                _nr_wrapper__HTTPServer_start_request_)
