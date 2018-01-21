from newrelic.common.object_wrapper import wrap_function_wrapper


def _bind_make_coroutine_wrapper(func, *args, **kwargs):
    return func


def wrap_make_coroutine_wrapper(wrapped, instance, args, kwargs):
    coro = wrapped(*args, **kwargs)
    original_func = _bind_make_coroutine_wrapper(*args, **kwargs)
    coro.__wrapped__ = original_func
    coro.__tornado_coroutine__ = True
    return coro


def instrument_tornado_gen(module):
    import tornado
    if hasattr(tornado, 'version_info') and tornado.version_info < (4, 5):
        wrap_function_wrapper(module, '_make_coroutine_wrapper',
                wrap_make_coroutine_wrapper)
