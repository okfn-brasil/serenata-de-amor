import inspect
import logging

from newrelic.api.function_trace import FunctionTrace
from newrelic.core.config import ignore_status_code
from newrelic.api.transaction_context import TransactionContext
from newrelic.common.object_wrapper import (wrap_function_wrapper, ObjectProxy,
        function_wrapper)

from newrelic.hooks.framework_tornado_r4.utils import (
        _iscoroutinefunction_tornado, _iscoroutinefunction_native)

_logger = logging.getLogger(__name__)
_instrumented = set()


def _wrap_if_not_wrapped(obj, attr, wrapper):
    wrapped = getattr(obj, attr)
    if not (hasattr(wrapped, '__wrapped__') and
            wrapped.__wrapped__ in _instrumented):
        setattr(obj, attr, wrapper(wrapped))
        _instrumented.add(wrapped)


def _nr_rulerouter_process_rule(wrapped, instance, args, kwargs):
    def _bind_params(rule, *args, **kwargs):
        return rule

    rule = _bind_params(*args, **kwargs)

    _wrap_handlers(rule)

    return wrapped(*args, **kwargs)


def _wrap_handlers(rule):
    if isinstance(rule, (tuple, list)):
        handler = rule[1]
    elif hasattr(rule, 'target'):
        handler = rule.target
    elif hasattr(rule, 'handler_class'):
        handler = rule.handler_class
    else:
        return

    from tornado.web import RequestHandler

    if isinstance(handler, (tuple, list)):
        # Tornado supports nested rules. For example
        #
        # application = web.Application([
        #     (HostMatches("example.com"), [
        #         (r"/", MainPageHandler),
        #         (r"/feed", FeedHandler),
        #     ]),
        # ])
        for subrule in handler:
            _wrap_handlers(subrule)
        return

    elif (not inspect.isclass(handler) or
            not issubclass(handler, RequestHandler)):
        # This handler does not inherit from RequestHandler so we ignore it.
        # Tornado supports non class based views and this is probably one of
        # those. It has also been observed that tornado's internals will pass
        # class instances as well.
        return

    # Wrap on_finish which will end transactions
    _wrap_if_not_wrapped(handler, 'on_finish', _nr_request_end)

    # wrap log_exception which records exceptions
    _wrap_if_not_wrapped(handler, 'log_exception', _nr_record_exception)

    if not hasattr(handler, 'SUPPORTED_METHODS'):
        return

    # Wrap all supported view methods with our FunctionTrace
    # instrumentation
    for request_method in handler.SUPPORTED_METHODS:
        method = getattr(handler, request_method.lower(), None)
        if not method:
            continue

        _wrap_if_not_wrapped(handler, request_method.lower(), _nr_method)


def _bind_log_exception(typ, value, tb, *args, **kwargs):
    return (typ, value, tb)


def should_ignore(exc, value, tb):
    from tornado.web import HTTPError

    if exc is HTTPError:
        status_code = value.status_code
        if ignore_status_code(status_code):
            return True


@function_wrapper
def _nr_record_exception(wrapped, instance, args, kwargs):
    transaction = getattr(instance, '_nr_transaction', None)

    if transaction is None:
        return wrapped(*args, **kwargs)

    exc_info = _bind_log_exception(*args, **kwargs)
    transaction.record_exception(*exc_info, ignore_errors=should_ignore)
    return wrapped(*args, **kwargs)


@function_wrapper
def _nr_request_end(wrapped, instance, args, kwargs):
    if hasattr(instance, '_nr_transaction'):
        transaction = instance._nr_transaction
        with TransactionContext(transaction):
            transaction.__exit__(None, None, None)

    # Execute the wrapped on_finish after ending the transaction since the
    # response has now already been sent.
    return wrapped(*args, **kwargs)


def _nr_method(method):

    if _iscoroutinefunction_native(method):

        @function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            transaction = getattr(instance, '_nr_transaction', None)

            if transaction is None:
                return wrapped(*args, **kwargs)

            coro = wrapped(*args, **kwargs)
            name = transaction.name
            return NRFunctionTraceCoroutineWrapper(coro, transaction, name)

    elif (_iscoroutinefunction_tornado(method) and
            inspect.isgeneratorfunction(method.__wrapped__)):

        @function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            transaction = getattr(instance, '_nr_transaction', None)

            if transaction is None:
                return wrapped(*args, **kwargs)

            method = wrapped.__wrapped__
            name = transaction.name

            import tornado.gen

            @tornado.gen.coroutine
            def _wrapped_coro():
                coro = method(instance, *args, **kwargs)
                return NRFunctionTraceCoroutineWrapper(coro, transaction, name)

            return _wrapped_coro()

    else:

        @function_wrapper
        def wrapper(wrapped, instance, args, kwargs):
            transaction = getattr(instance, '_nr_transaction', None)

            if transaction is None:
                return wrapped(*args, **kwargs)

            name = transaction.name
            with TransactionContext(transaction):
                with FunctionTrace(transaction, name):
                    return wrapped(*args, **kwargs)

    return wrapper(method)


class NRFunctionTraceCoroutineWrapper(ObjectProxy):
    def __init__(self, wrapped, transaction, name):
        super(NRFunctionTraceCoroutineWrapper, self).__init__(wrapped)
        self._nr_transaction = transaction
        self._nr_trace = FunctionTrace(transaction, name)

    def __iter__(self):
        return self

    def __await__(self):
        return self

    def __next__(self):
        return self.send(None)

    next = __next__

    def send(self, value):
        if not self._nr_trace.activated:
            self._nr_trace.__enter__()

        with TransactionContext(self._nr_transaction):
            try:
                return self.__wrapped__.send(value)
            except:
                self._nr_trace.__exit__(None, None, None)
                raise

    def throw(self, *args, **kwargs):
        with TransactionContext(self._nr_transaction):
            try:
                return self.__wrapped__.throw(*args, **kwargs)
            except:
                self._nr_trace.__exit__(None, None, None)
                raise

    def close(self):
        try:
            return self.__wrapped__.close()
        finally:
            self._nr_trace.__exit__(None, None, None)


def instrument_tornado_routing(module):
    wrap_function_wrapper(module, 'RuleRouter.process_rule',
            _nr_rulerouter_process_rule)
