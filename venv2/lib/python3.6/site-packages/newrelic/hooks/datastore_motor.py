from newrelic.common.object_wrapper import wrap_function_wrapper

# This is NOT a fully-featured instrumentation for the motor library. Instead
# this is a monkey-patch of the motor library to work around a bug that causes
# the __name__ lookup on a MotorCollection object to fail. This bug was causing
# customer's applications to fail when they used motor in Tornado applications.


def _nr_wrapper_Motor_getattr_(wrapped, instance, args, kwargs):

    def _bind_params(name, *args, **kwargs):
        return name

    name = _bind_params(*args, **kwargs)

    if name.startswith('__') or name.startswith('_nr_'):
        raise AttributeError('%s class has no attribute %s. To access '
                'use object[%r].' % (instance.__class__.__name__,
                name, name))

    return wrapped(*args, **kwargs)


def patch_motor(module):
    if (hasattr(module, 'version_tuple') and
            module.version_tuple >= (0, 6)):
        return

    patched_classes = ['MotorClient', 'MotorReplicaSetClient', 'MotorDatabase',
            'MotorCollection']
    for patched_class in patched_classes:
        if hasattr(module, patched_class):
            wrap_function_wrapper(module, patched_class + '.__getattr__',
                    _nr_wrapper_Motor_getattr_)
