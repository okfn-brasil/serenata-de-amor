import itertools
import asyncio
import sys

from newrelic.api.application import application_instance
from newrelic.api.coroutine_trace import is_coroutine_function, CoroutineTrace
from newrelic.api.external_trace import ExternalTrace
from newrelic.api.function_trace import function_trace
from newrelic.api.transaction import current_transaction, ignore_transaction
from newrelic.api.web_transaction import WebTransaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        function_wrapper, ObjectProxy)
from newrelic.core.config import ignore_status_code


def should_ignore(exc, value, tb):
    from aiohttp import web

    if isinstance(value, web.HTTPException):
        status_code = value.status_code
        return ignore_status_code(status_code)


def _nr_process_response(response, transaction):
    headers = dict(response.headers)
    status_str = str(response.status)

    nr_headers = transaction.process_response(status_str,
            headers.items())

    for k, v in nr_headers:
        response.headers.add(k, v)


class NRTransactionCoroutineWrapper(ObjectProxy):
    def __init__(self, wrapped, request):
        super(NRTransactionCoroutineWrapper, self).__init__(wrapped)
        self._nr_transaction = None
        self._nr_request = request

        environ = {
            'PATH_INFO': request.path,
            'REQUEST_METHOD': request.method,
            'CONTENT_TYPE': request.content_type,
            'QUERY_STRING': request.query_string,
        }
        for k, v in request.headers.items():
            normalized_key = k.replace('-', '_').upper()
            http_key = 'HTTP_%s' % normalized_key
            environ[http_key] = v
        self._nr_environ = environ

    def __iter__(self):
        return self

    def __await__(self):
        return self

    def __next__(self):
        return self.send(None)

    def send(self, value):
        if not self._nr_transaction:
            # create and start the transaction
            app = application_instance()
            txn = WebTransaction(app, self._nr_environ)

            import aiohttp
            txn.add_framework_info(
                    name='aiohttp', version=aiohttp.__version__)

            self._nr_transaction = txn

            if txn.enabled:
                txn.__enter__()
                txn.drop_transaction()

        txn = self._nr_transaction

        # transaction may not be active
        if not txn.enabled:
            return self.__wrapped__.send(value)

        import aiohttp.web as _web

        txn.save_transaction()

        try:
            r = self.__wrapped__.send(value)
            txn.drop_transaction()
            return r
        except (GeneratorExit, StopIteration) as e:
            try:
                response = e.value
                _nr_process_response(response, txn)
            except:
                pass
            self._nr_transaction.__exit__(None, None, None)
            self._nr_request = None
            raise
        except _web.HTTPException as e:
            exc_info = sys.exc_info()
            try:
                _nr_process_response(e, txn)
            except:
                pass
            if should_ignore(*exc_info):
                self._nr_transaction.__exit__(None, None, None)
            else:
                self._nr_transaction.__exit__(*exc_info)
            self._nr_request = None
            raise
        except:
            exc_info = sys.exc_info()
            try:
                nr_headers = txn.process_response('500', ())
                self._nr_request._nr_headers = dict(nr_headers)
            except:
                pass
            self._nr_transaction.__exit__(*exc_info)
            self._nr_request = None
            raise

    def throw(self, *args, **kwargs):
        txn = self._nr_transaction

        # transaction may not be active
        if not txn.enabled:
            return self.__wrapped__.throw(*args, **kwargs)

        import aiohttp.web as _web

        txn.save_transaction()
        try:
            r = self.__wrapped__.throw(*args, **kwargs)
            txn.drop_transaction()
            return r
        except (GeneratorExit, StopIteration) as e:
            try:
                response = e.value
                _nr_process_response(response, txn)
            except:
                pass
            self._nr_transaction.__exit__(None, None, None)
            self._nr_request = None
            raise
        except asyncio.CancelledError:
            self._nr_transaction.ignore_transaction = True
            self._nr_transaction.__exit__(None, None, None)
            self._nr_request = None
            raise
        except _web.HTTPException as e:
            exc_info = sys.exc_info()
            try:
                _nr_process_response(e, txn)
            except:
                pass
            if should_ignore(*exc_info):
                self._nr_transaction.__exit__(None, None, None)
            else:
                self._nr_transaction.__exit__(*exc_info)
            self._nr_request = None
            raise
        except:
            exc_info = sys.exc_info()
            try:
                nr_headers = txn.process_response('500', ())
                self._nr_request._nr_headers = dict(nr_headers)
            except:
                pass
            self._nr_transaction.__exit__(*exc_info)
            self._nr_request = None
            raise

    def close(self):
        txn = self._nr_transaction

        # transaction may not be active
        if not txn.enabled:
            return self.__wrapped__.close()

        txn.save_transaction()
        try:
            r = self.__wrapped__.close()
            self._nr_transaction.__exit__(None, None, None)
            self._nr_request = None
            return r
        except:
            exc_info = sys.exc_info()
            try:
                nr_headers = txn.process_response('', ())
                self._nr_request._nr_headers = dict(nr_headers)
            except:
                pass
            self._nr_transaction.__exit__(*exc_info)
            self._nr_request = None
            raise


@function_wrapper
def _nr_aiohttp_view_wrapper_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    name = instance and callable_name(instance) or callable_name(wrapped)
    transaction.set_transaction_name(name, priority=1)

    return function_trace(name=name)(wrapped)(*args, **kwargs)


def _nr_aiohttp_transaction_wrapper_(wrapped, instance, args, kwargs):
    def _bind_params(request, *_args, **_kwargs):
        return request

    # get the coroutine
    coro = wrapped(*args, **kwargs)
    request = _bind_params(*args, **kwargs)

    if hasattr(coro, '__iter__'):
        coro = iter(coro)

    # Wrap the coroutine
    return NRTransactionCoroutineWrapper(coro, request)


def _nr_aiohttp_wrap_view_(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    instance._handler = _nr_aiohttp_view_wrapper_(instance._handler)
    return result


def _nr_aiohttp_wrap_wsgi_response_(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    # We need to defer grabbing the response attribute in the case that the
    # WSGI application chooses not to call start_response before the first
    # iteration. The case where WSGI applications choose not to call
    # start_response before iteration is documented in the WSGI spec
    # (PEP-3333).
    #
    # > ...servers must not assume that start_response() has been called before
    # they begin iterating over the iterable.
    class ResponseProxy:
        def __getattr__(self, name):
            # instance.response should be overwritten at this point
            if instance.response is self:
                raise AttributeError("%r object has no attribute %r" % (
                        type(instance).__name__, 'response'))
            return getattr(instance.response, name)

    instance.response = ResponseProxy()

    return result


def _nr_aiohttp_response_prepare_(wrapped, instance, args, kwargs):

    def _bind_params(request):
        return request

    request = _bind_params(*args, **kwargs)

    nr_headers = getattr(request, '_nr_headers', None)
    if nr_headers:
        headers = dict(instance.headers)
        nr_headers.update(headers)
        instance._headers = nr_headers

    return wrapped(*args, **kwargs)


@function_wrapper
def _nr_aiohttp_wrap_middleware_(wrapped, instance, args, kwargs):

    @asyncio.coroutine
    def _inner():
        result = yield from wrapped(*args, **kwargs)
        return function_trace()(result)

    return _inner()


def _nr_aiohttp_wrap_application_init_(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    if hasattr(instance, '_middlewares'):
        for index, middleware in enumerate(instance._middlewares):
            traced_middleware = _nr_aiohttp_wrap_middleware_(middleware)
            instance._middlewares[index] = traced_middleware

    return result


def _nr_aiohttp_wrap_system_route_(wrapped, instance, args, kwargs):
    ignore_transaction()
    return wrapped(*args, **kwargs)


class HeaderProxy(ObjectProxy):
    def __init__(self, wrapped, nr_headers):
        super(HeaderProxy, self).__init__(wrapped)
        self._nr_headers = nr_headers

    def items(self):
        nr_headers = dict(self._nr_headers)

        # Remove all conflicts
        for key, _ in self._nr_headers:
            if key in self:
                nr_headers.pop(key)

        return itertools.chain(
                self.__wrapped__.items(), nr_headers.items())


def _nr_aiohttp_add_cat_headers_(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        cat_headers = ExternalTrace.generate_request_headers(transaction)
    except:
        return wrapped(*args, **kwargs)

    tmp = instance.headers
    instance.headers = HeaderProxy(tmp, cat_headers)

    if is_coroutine_function(wrapped):
        @asyncio.coroutine
        def new_coro():
            try:
                result = yield from wrapped(*args, **kwargs)
                return result
            finally:
                instance.headers = tmp

        return new_coro()
    else:
        try:
            return wrapped(*args, **kwargs)
        finally:
            instance.headers = tmp


def _bind_request(method, url, *args, **kwargs):
    return method, url


def _nr_aiohttp_request_wrapper_(wrapped, instance, args, kwargs):
    transaction = current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    method, url = _bind_request(*args, **kwargs)
    trace = ExternalTrace(transaction, 'aiohttp', url, method)

    @asyncio.coroutine
    def _coro():
        try:
            response = yield from wrapped(*args, **kwargs)

            try:
                trace.process_response_headers(response.headers.items())
            except:
                pass

            return response
        except Exception as e:
            try:
                trace.process_response_headers(e.headers.items())
            except:
                pass

            raise

    return CoroutineTrace(_coro, trace)


def instrument_aiohttp_client(module):
    wrap_function_wrapper(module, 'ClientSession._request',
            _nr_aiohttp_request_wrapper_)


def instrument_aiohttp_client_reqrep(module):
    import aiohttp
    version_info = tuple(int(_) for _ in aiohttp.__version__.split('.')[:2])

    if version_info >= (2, 0):
        wrap_function_wrapper(module, 'ClientRequest.send',
                _nr_aiohttp_add_cat_headers_)


def instrument_aiohttp_protocol(module):
    wrap_function_wrapper(module, 'Request.send_headers',
            _nr_aiohttp_add_cat_headers_)


def instrument_aiohttp_web_urldispatcher(module):
    wrap_function_wrapper(module, 'ResourceRoute.__init__',
            _nr_aiohttp_wrap_view_)
    wrap_function_wrapper(module, 'SystemRoute._handler',
            _nr_aiohttp_wrap_system_route_)


def instrument_aiohttp_web(module):
    wrap_function_wrapper(module, 'Application._handle',
            _nr_aiohttp_transaction_wrapper_)
    wrap_function_wrapper(module, 'Application.__init__',
            _nr_aiohttp_wrap_application_init_)


def instrument_aiohttp_wsgi(module):
    wrap_function_wrapper(module, 'WsgiResponse.__init__',
            _nr_aiohttp_wrap_wsgi_response_)


def instrument_aiohttp_web_response(module):
    wrap_function_wrapper(module, 'Response.prepare',
            _nr_aiohttp_response_prepare_)
