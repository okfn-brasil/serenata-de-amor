import functools

from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object

class ErrorTrace(object):

    def __init__(self, transaction, ignore_errors=[]):
        self._transaction = transaction
        self._ignore_errors = ignore_errors

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        if exc is None or value is None or tb is None:
            return

        if self._transaction is None:
            return

        self._transaction.record_exception(exc=exc, value=value, tb=tb,
                ignore_errors=self._ignore_errors)

def ErrorTraceWrapper(wrapped, ignore_errors=[]):

    def wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        with ErrorTrace(transaction, ignore_errors):
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, wrapper)

def error_trace(ignore_errors=[]):
    return functools.partial(ErrorTraceWrapper, ignore_errors=ignore_errors)

def wrap_error_trace(module, object_path, ignore_errors=[]):
    wrap_object(module, object_path, ErrorTraceWrapper, (ignore_errors, ))
