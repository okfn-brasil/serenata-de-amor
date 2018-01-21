import sys
import logging

from newrelic.hooks.framework_tornado import (retrieve_transaction_request,
        resume_request_monitoring, suspend_request_monitoring,
        record_exception, retrieve_current_transaction)

from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (wrap_function_wrapper,
        function_wrapper)

_logger = logging.getLogger(__name__)

class GeneratorReturn(Exception): pass

def _nr_wrapper_gen_coroutine_generator_(generator):
    # This wrapper is applied around the generator returned by any
    # function which was wrapped by gen.engine or gen.coroutine. This is
    # to allows us to track separately each call back into the
    # generator. The first time we are called we should be in the
    # context of an active transaction. We need to cache that so we can
    # reinstate the transaction each time we return back into the
    # generator. We also reach back to the active node of the transaction
    # to get the name to be used for each function trace created when
    # the generator is re-entered.

    try:
        value = None
        exc = None

        active_transaction = retrieve_current_transaction()

        transaction = None
        request = None
        name = None

        # Cache the request object associated with the active
        # transaction. If there is a request, then calculate the name
        # for tracking each call into the generator from the current
        # active node. That node should be the function trace node added
        # when our wrapper around gen.engine or gen.coroutine was
        # called.

        request = (active_transaction is not None and
                retrieve_transaction_request(active_transaction))

        if request is not None:
            active_node = active_transaction.active_node()

            if hasattr(active_node, 'name'):
                active_name = active_node.name

                if active_name.endswith(' (coroutine)'):
                    name = active_name.replace(' (coroutine)', ' (yield)')

        while True:
            # The first time in the loop we should already have
            # inherited an active transaction. On subsequent times
            # however there may not be, in which case we need to resume
            # the transaction associated with the request. We need to
            # remember if we resumed the transaction as we need to
            # then make sure we suspend it again as the caller isn't
            # going to do that for us.

            suspend = None

            if name is not None:
                if retrieve_current_transaction() is None:
                    transaction = resume_request_monitoring(request)
                    suspend = transaction
                else:
                    transaction = active_transaction

            # The following code sits between the consumer of the
            # generator and the generator itself. It will add a function
            # trace around each call into the generator to yield a
            # value. Annotate the function trace with the location of
            # the code within the generator which will be executed.

            try:
                params = {}

                gi_frame = generator.gi_frame

                params['filename'] = gi_frame.f_code.co_filename
                params['lineno'] = gi_frame.f_lineno

                with FunctionTrace(transaction, name, params=params):
                    try:
                        if exc is not None:
                            yielded = generator.throw(*exc)
                            exc = None
                        else:
                            yielded = generator.send(value)

                    except (GeneratorReturn, StopIteration):
                        raise

                    except:  # Catch all.
                        # We need to record exceptions at this point
                        # as the call back into the generator could
                        # have been triggered by a future direct from
                        # the main loop. There isn't therefore anywhere
                        # else it can be captured.

                        if transaction is not None:
                            record_exception(transaction, sys.exc_info())

                        raise

            finally:
                if suspend is not None:
                    suspend_request_monitoring(request, name='Callback/Wait')

            # XXX This could present a problem if we are yielding a
            # future as the future will be scheduled outside of the
            # context of the active transaction if we had to do a
            # suspend of the transaction since we resumed it. We can't
            # do the suspend after the yield as it is during the yield
            # that control is returned back to the main loop.

            try:
                value = yield yielded

            except Exception:
                exc = sys.exc_info()

    finally:
        generator.close()

def _nr_wrapper_gen_Runner___init___(wrapped, instance, args, kwargs):
    # This wrapper intercepts the initialisation function of the Runner
    # class and wraps the generator.

    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _params(gen, *args, **kwargs):
        return gen, args, kwargs

    generator, _args, _kwargs = _params(*args, **kwargs)

    generator = _nr_wrapper_gen_coroutine_generator_(generator)

    return wrapped(generator, *_args, **_kwargs)

@function_wrapper
def _nr_wrapper_gen_coroutine_function_(wrapped, instance, args, kwargs):
    # This wrapper is applied outside of any instance of the gen.engine
    # and gen.coroutine decorators. We record the call as a function
    # trace, flagging it as a special coroutine instance. This also
    # works on conjunction with the wrapper on the Runner class, which
    # applies a wrapper to the generator when passed to the generator.
    # When this wrapped function is called, if the result of the
    # function that gen.engine or gen.coroutine calls is a generator,
    # the Runner is created and run. If running it, it will always call
    # into the generator at least once. On that first time the wrapper
    # for the generator will see the active transaction and can keep a
    # reference to it to allow the transaction to be reinstated across
    # calls of the generator to yield an item.

    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(wrapped)

    with FunctionTrace(transaction, '%s (coroutine)' % name):
        return wrapped(*args, **kwargs)

def _nr_wrapper_gen_coroutine_(wrapped, instance, args, kwargs):
    # This wrapper is used to wrap both gen.engine and gen.coroutine
    # decorators. We use it to apply a further wrapper around any
    # function which those decorators are in turn applied to. It is
    # applied outside to capture the initial call of the function that
    # the decorators was applied to and in particular allows us to
    # intercept the binding of a function when it is a method of a
    # class. We need to be able to do this because the decorators
    # internally uses a nested function to implement the decorator which
    # destroys the ability to get the proper name of the wrapped
    # function under Python 2.

    return _nr_wrapper_gen_coroutine_function_(wrapped(*args, **kwargs))

def _nr_wrapper_Task_start_(wrapped, instance, args, kwargs):
    # This wrapper is used around the start() method of the Task class.
    # The Task class executes a callback and we track that as a function
    # trace, naming it after the function the Task holds.

    transaction = retrieve_current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    name = callable_name(instance.func)

    with FunctionTrace(transaction, name):
        return wrapped(*args, **kwargs)

def instrument_tornado_gen(module):
    # The Return class type was introduced in Tornado 3.0.

    global GeneratorReturn

    if hasattr(module, 'Return'):
        GeneratorReturn = module.Return

    # The gen.coroutine decorator was introduced in Tornado 3.0.

    if hasattr(module, 'coroutine'):
        wrap_function_wrapper(module, 'coroutine', _nr_wrapper_gen_coroutine_)

    # The gen.engine decorator, Runner class type and Task class type
    # were introduced in Tornado 2.0.

    if hasattr(module, 'engine'):
        wrap_function_wrapper(module, 'engine', _nr_wrapper_gen_coroutine_)

    if hasattr(module, 'Runner'):
        wrap_function_wrapper(module, 'Runner.__init__',
                _nr_wrapper_gen_Runner___init___)

    if hasattr(module, 'Task'):
        if hasattr(module.Task, 'start'):
            # The start() method was removed in Tornado 4.0.

            wrap_function_wrapper(module, 'Task.start',
                    _nr_wrapper_Task_start_)
