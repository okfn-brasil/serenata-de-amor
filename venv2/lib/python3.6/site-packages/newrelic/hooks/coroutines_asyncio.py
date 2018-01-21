from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.api.transaction import current_transaction
from newrelic.api.transaction_context import CoroutineTransactionContext


def _bind_ensure_future(coro_or_future, *, loop=None):
    return coro_or_future, loop


def wrap_ensure_future(coroutines):

    def _wrap_ensure_future(wrapped, instance, args, kwargs):
        coro, loop = _bind_ensure_future(*args, **kwargs)

        if coroutines.iscoroutine(coro):
            coro = CoroutineTransactionContext(coro, current_transaction())
            return wrapped(coro, loop=loop)

        # Avoid any futures / async generators
        return wrapped(*args, **kwargs)

    return _wrap_ensure_future


def instrument_asyncio_tasks(module):
    if not hasattr(module, 'coroutines'):
        return

    if hasattr(module, 'ensure_future'):
        wrap_function_wrapper(module, 'ensure_future',
                wrap_ensure_future(module.coroutines))
    elif hasattr(module, 'async'):
        wrap_function_wrapper(module, 'async',
                wrap_ensure_future(module.coroutines))
