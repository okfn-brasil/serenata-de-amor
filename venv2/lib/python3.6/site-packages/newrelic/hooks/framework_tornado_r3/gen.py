import logging

from newrelic.hooks.framework_tornado_r3.util import (
        retrieve_current_transaction)
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (function_wrapper,
        wrap_function_wrapper, ObjectProxy)

_logger = logging.getLogger(__name__)

try:
    # sys._getframe is not part of the python spec and is not guaranteed to
    # exist in all python implemenations. However, it does exists in the
    # reference implemenations of cpython 2, 3 and in pypy.
    # It is about 3 orders of magnitude faster than inspect in python 2.7
    # on my laptop. Inspect touches the disk to get filenames and possibly
    # other information which we don't need.
    import sys
    get_frame = sys._getframe
except:
    _logger.warning('You are using a python implemenation without '
            'sys._getframe which is used by New Relic to get meaningful names '
            'for coroutines. We are falling back to use inspect.stack which is'
            ' very slow.')
    import inspect

    def getframe(depth):
        return inspect.stack(0)[depth]
    get_frame = getframe


def _coroutine_name(func):
    # Because of how coroutines get scheduled they will look like plain
    # functions (and not methods) in python 2 and will not have a class
    # associated with them. In particular, func will not have the attribute
    # im_class. This means callable_name will return the function name without
    # the class prefix. See PYTHON-1798.
    return '%s %s' % (callable_name(func), '(coroutine)')


class IOLoopProxy(ObjectProxy):

    def add_future(self, future, callback):
        future._nr_coroutine_name = self._nr_coroutine_name
        return self.__wrapped__.add_future(future, callback)


def _nr_wrapper_Runner__init__(wrapped, instance, args, kwargs):
    # We want to associate a function name from _make_coroutine_wrapper with
    # a call to Runner.__init__. This way we know the name of the function
    # running in Runner and can associate metrics with it.
    # One strategy would be to store the function name on the transaction.
    # This can be problematic because an asynchronous/blocking call can occur
    # in _make_coroutine_wrapper.wrapper before the call to Runner.__init__.
    # This means other coroutines could run in the transaction between when we
    # record the function name in the transaction and before Runner.__init__
    # is called. Since these coroutines run asynchronously and don't nest, we
    # can't use a stack to keep track of which _make_coroutine_wrapper.wrapper
    # call belongs to which Runner.__init__ call.
    # Instead of storing the name in the transaction, we will look up the call
    # stack to get the function name.

    transaction = retrieve_current_transaction()
    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        # The only place in the Tornado code where a Runner is instantiated
        # is in _make_coroutine_wrapper in Tornado's gen.py. We look up the
        # stack from this call to __init__ to get the function name.
        frame = get_frame(1)

    except ValueError:
        _logger.debug('tornado.gen.Runner is being created at the top of the '
                'stack. That means the Runner object is being created outside '
                'of a tornado.gen decorator. NewRelic will not be able to '
                'name this instrumented function meaningfully (it will be '
                'named lambda.')
        return wrapped(*args, **kwargs)

    # In Python 2 we look up one frame. In Python 3 and PyPy, our wrapping
    # gets in the way and we have to look up 2 frames. In general, we want
    # to go up the call stack until we first encounter the tornado.gen
    # module. We restrict our search to 5 frames.
    max_frame_depth = 5
    frame_depth = 1
    while frame and frame_depth <= max_frame_depth:
        if frame.f_globals['__name__'] == 'tornado.gen':
            break
        frame = frame.f_back
        frame_depth += 1

    # Verify that we are in the frame we think we are.
    if ('__name__' in frame.f_globals and
            frame.f_globals['__name__'] == 'tornado.gen' and
            'func' in frame.f_locals and
            'replace_callback' in frame.f_locals and
            frame.f_code.co_name == 'wrapper'):
        instance._nr_coroutine_name = _coroutine_name(
                frame.f_locals['func'])
    else:
        _logger.debug('tornado.gen.Runner is being called outside of a '
                'tornado.gen decorator (or the tornado implemenation has '
                'changed). NewRelic will not be able to name this instrumented'
                ' function meaningfully (it will be named lambda or inner).')

    # Bump the ref count, so we don't end the transaction before
    # the Runner finishes.

    transaction._ref_count += 1

    return wrapped(*args, **kwargs)


def _nr_wrapper_Runner_handle_yield_(wrapped, instance, args, kwargs):
    if (hasattr(instance, 'io_loop') and
            hasattr(instance, '_nr_coroutine_name')):
        _io_loop = instance.io_loop
        proxy = IOLoopProxy(_io_loop)
        proxy._nr_coroutine_name = instance._nr_coroutine_name
        instance.io_loop = proxy
    return wrapped(*args, **kwargs)


def _nr_wrapper_Runner_run_(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)

    transaction = retrieve_current_transaction()
    if transaction is None:
        return result

    if instance.finished:
        transaction._ref_count -= 1

    return result


@function_wrapper
def _wrap_decorated(wrapped, instance, args, kwargs):
    # Wraps the output of a tornado decorator.
    #
    # For an example see our wrapper for coroutine,
    # _nr_wrapper_coroutine_wrapper_.

    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)
    with FunctionTrace(transaction, name=name):
        return wrapped(*args, **kwargs)


# We explictly wrap the first time we enter a coroutine decorated function.
def _nr_wrapper_coroutine_wrapper_(wrapped, instance, args, kwargs):
    func = wrapped(*args, **kwargs)
    return _wrap_decorated(func)


# We explicitly wrap the first time we enter an engine decorated function.
def _nr_wrapper_engine_wrapper_(wrapped, instance, args, kwargs):
    func = wrapped(*args, **kwargs)
    return _wrap_decorated(func)


def instrument_tornado_gen(module):
    wrap_function_wrapper(module, 'Runner.__init__',
            _nr_wrapper_Runner__init__)
    wrap_function_wrapper(module, 'Runner.handle_yield',
            _nr_wrapper_Runner_handle_yield_)
    wrap_function_wrapper(module, 'Runner.run', _nr_wrapper_Runner_run_)
    wrap_function_wrapper(module, 'coroutine', _nr_wrapper_coroutine_wrapper_)
    wrap_function_wrapper(module, 'engine', _nr_wrapper_engine_wrapper_)
