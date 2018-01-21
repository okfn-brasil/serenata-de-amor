import functools

from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.common.object_names import callable_name

def TransactionNameWrapper(wrapped, name=None, group=None, priority=None):

    def dynamic_wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        if callable(name):
            if instance is not None:
                _name = name(instance, *args, **kwargs)
            else:
                _name = name(*args, **kwargs)

        elif name is None:
            _name = callable_name(wrapped)

        else:
            _name = name

        if callable(group):
            if instance is not None:
                _group = group(instance, *args, **kwargs)
            else:
                _group = group(*args, **kwargs)

        else:
            _group = group

        transaction.set_transaction_name(_name, _group, priority)

        return wrapped(*args, **kwargs)

    def literal_wrapper(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        _name = name or callable_name(wrapped)

        transaction.set_transaction_name(_name, group, priority)

        return wrapped(*args, **kwargs)

    if callable(name) or callable(group):
        return FunctionWrapper(wrapped, dynamic_wrapper)

    return FunctionWrapper(wrapped, literal_wrapper)

def transaction_name(name=None, group=None, priority=None):
    return functools.partial(TransactionNameWrapper, name=name,
            group=group, priority=priority)

def wrap_transaction_name(module, object_path, name=None, group=None,
                          priority=None):
    return wrap_object(module, object_path, TransactionNameWrapper,
            (name, group, priority))
