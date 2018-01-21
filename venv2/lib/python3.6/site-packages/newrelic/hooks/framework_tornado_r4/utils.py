import inspect
try:
    _inspect_iscoroutinefunction = inspect.iscoroutinefunction
except AttributeError:
    def _inspect_iscoroutinefunction(*args, **kwargs):
        return False

try:
    import asyncio
    _asyncio_iscoroutinefunction = asyncio.iscoroutinefunction
except ImportError:
    def _asyncio_iscoroutinefunction(*args, **kwargs):
        return False


def _iscoroutinefunction_tornado(fn):
    return hasattr(fn, '__tornado_coroutine__')


def _iscoroutinefunction_native(fn):
    return _asyncio_iscoroutinefunction(fn) or _inspect_iscoroutinefunction(fn)
