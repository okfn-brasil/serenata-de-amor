import inspect
import logging

from newrelic.common.object_wrapper import ObjectProxy
from newrelic.common.object_names import callable_name

_logger = logging.getLogger(__name__)


if hasattr(inspect, 'iscoroutinefunction'):
    def is_coroutine_function(wrapped):
        return (inspect.iscoroutinefunction(wrapped) or
                inspect.isgeneratorfunction(wrapped))
else:
    def is_coroutine_function(wrapped):
        return inspect.isgeneratorfunction(wrapped)


def _iscoroutinefunction_tornado(fn):
    return hasattr(fn, '__tornado_coroutine__')


class TraceContext(object):
    # Assumption made for this context manager: no other object maintains a
    # reference to trace after the TraceContext is constructed.
    # This is important because the assumption made by the logic below is that
    # only the TraceContext object can call __enter__ on the trace (which may
    # delete the transaction).

    def __init__(self, trace):
        if not trace.transaction:
            self.trace = None
        else:
            self.trace = trace

        self.current_trace = None

    def __enter__(self):
        if not self.trace:
            return self

        self.current_trace = self.trace.transaction.current_node
        if not self.trace.activated:
            self.trace.__enter__()

            # Transaction can be cleared by calling enter (such as when tracing
            # as a child of a terminal node)
            # In this case, we clear out the transaction and defer to the
            # wrapped function
            if not self.trace.transaction:
                self.trace = None
        else:
            # In the case that the function trace is already active, notify the
            # transaction that this coroutine is now the current node (for
            # automatic parenting)
            self.trace.transaction.current_node = self.trace

        return self

    def __exit__(self, exc, value, tb):
        if not self.trace:
            return

        txn = self.trace.transaction

        # If the current node has been changed, record this as an error in a
        # supportability metric.
        if txn.current_node is not self.trace:
            txn.record_custom_metric(
                    'Supportability/Python/TraceContext/ExitNodeMismatch',
                    {'count': 1})
            _logger.debug('Trace context exited with an unexpected current '
                    'node. Current trace is %r. Expected trace is %r. '
                    'Please report this issue to New Relic Support.',
                    self.current_trace, self.trace)

        if exc in (StopIteration, GeneratorExit):
            self.trace.__exit__(None, None, None)
            self.trace = None
        elif exc:
            self.trace.__exit__(exc, value, tb)
            self.trace = None

        # Since the coroutine is returning control to the parent at this
        # point, we should notify the transaction that this coroutine is no
        # longer the current node for parenting purposes
        if self.current_trace:
            txn.current_node = self.current_trace

            # Clear out the current trace so that it cannot be reused in future
            # exits and doesn't maintain a dangling reference to a trace.
            self.current_trace = None

    def __del__(self):
        # If the trace goes out of scope, it's possible it's still active.
        # It's important that we end the trace so that the trace is reported.
        # It's also important that we don't change the current node as part of
        # this reporting.
        if self.trace and self.trace.activated:
            txn = self.trace.transaction
            if txn:
                current_trace = txn.current_node
                self.trace.__exit__(None, None, None)
                if current_trace is not self.trace:
                    txn.current_node = current_trace


class CoroutineTrace(ObjectProxy):
    def __init__(self, wrapped, trace):

        self._nr_trace_context = TraceContext(trace)

        # get the coroutine
        coro = wrapped()

        # Wrap the coroutine
        super(CoroutineTrace, self).__init__(coro)

    def __iter__(self):
        return self

    def __await__(self):
        return self

    def __next__(self):
        return self.send(None)

    next = __next__

    def send(self, value):
        with self._nr_trace_context:
            return self.__wrapped__.send(value)

    def throw(self, *args, **kwargs):
        with self._nr_trace_context:
            return self.__wrapped__.throw(*args, **kwargs)

    def close(self):
        try:
            with self._nr_trace_context:
                result = self.__wrapped__.close()
        except:
            raise
        else:
            # If the trace hasn't been exited, then exit the trace
            if self._nr_trace_context.trace:
                self._nr_trace_context.trace.__exit__(None, None, None)
                self._nr_trace_context.trace = None
            return result


def return_value_fn(wrapped):
    if _iscoroutinefunction_tornado(wrapped):
        if hasattr(wrapped, '__wrapped__'):
            coro_name = callable_name(wrapped.__wrapped__)
        else:
            coro_name = callable_name(wrapped)
        _logger.warning('The tornado coroutine function %r '
                '(tornado.gen.coroutine) has been incorrectly wrapped. To '
                'trace a tornado coroutine, the New Relic trace decorator '
                'must be the innermost decorator. For more information see '
                'https://docs.newrelic.com/docs/agents/python-agent/'
                'trace-decorators-tornado-coroutines', coro_name)

    if is_coroutine_function(wrapped):
        def return_value(trace, fn):
            return CoroutineTrace(fn, trace)
    else:
        def return_value(trace, fn):
            with trace:
                return fn()

    return return_value
