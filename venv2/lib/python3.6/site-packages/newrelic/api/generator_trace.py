import functools
import types

from newrelic.api.transaction import current_transaction
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.common.object_names import callable_name

def GeneratorTraceWrapper(wrapped, name=None, group=None, label=None,
            params=None):

    def wrapper(wrapped, instance, args, kwargs):
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

        if callable(label):
            if instance is not None:
                _label = label(instance, *args, **kwargs)
            else:
                _label = label(*args, **kwargs)

        else:
            _label = label

        if callable(params):
            if instance is not None:
                _params = params(instance, *args, **kwargs)
            else:
                _params = params(*args, **kwargs)

        else:
            _params = params

        def _generator(generator):
            _gname = '%s (generator)' % _name

            try:
                value = None
                exc = None

                while True:
                    transaction = current_transaction()

                    params = {}

                    frame = generator.gi_frame

                    params['filename'] = frame.f_code.co_filename
                    params['lineno'] = frame.f_lineno

                    with FunctionTrace(transaction, _gname, _group,
                             params=params):
                        try:
                            if exc is not None:
                                yielded = generator.throw(*exc)
                                exc = None
                            else:
                                yielded = generator.send(value)

                        except StopIteration:
                            raise

                        except Exception:
                            raise

                    try:
                        value = yield yielded

                    except Exception:
                        exc = sys.exc_info()

            finally:
                generator.close()

        with FunctionTrace(transaction, _name, _group, _label, _params):
            try:
                result = wrapped(*args, **kwargs)

            except:  # Catch all
                raise

            else:
                if isinstance(result, types.GeneratorType):
                    return _generator(result)

                else:
                    return result

    return FunctionWrapper(wrapped, wrapper)

def generator_trace(name=None, group=None, label=None, params=None):
    return functools.partial(GeneratorTraceWrapper, name=name,
            group=group, label=label, params=params)

def wrap_generator_trace(module, object_path, name=None,
        group=None, label=None, params=None):
    return wrap_object(module, object_path, GeneratorTraceWrapper,
            (name, group, label, params))
