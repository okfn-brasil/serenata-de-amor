from newrelic.common.object_wrapper import wrap_function_wrapper


def _nr_wrapper__NormalizedHeaderCache___missing__(
        wrapped, instance, args, kwargs):

    def _bind_params(key, *args, **kwargs):
        return key

    key = _bind_params(*args, **kwargs)

    normalized = wrapped(*args, **kwargs)

    if key.startswith('X-NewRelic'):
        instance[key] = key
        return key

    return normalized


def instrument_tornado_httputil(module):
    wrap_function_wrapper(module, '_NormalizedHeaderCache.__missing__',
            _nr_wrapper__NormalizedHeaderCache___missing__)
