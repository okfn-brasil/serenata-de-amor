"""This module implement decorators for wrapping data sources so as to
simplify their construction and attribution of properties.

"""

import functools

def data_source_generator(name=None, **properties):
    """Decorator for applying to a simple data source which directly
    returns an iterable/generator with the metrics for each sample. The
    function the decorator is applied to must take no arguments.

    """

    def _decorator(func):
        @functools.wraps(func)
        def _properties(settings):
            def _factory(environ):
                return func
            d = dict(properties)
            d['name'] = name
            d['factory'] = _factory
            return d
        return _properties
    return _decorator

def data_source_factory(name=None, **properties):
    """Decorator for applying to a data source defined as a factory. The
    decorator can be applied to a class or a function. The class
    constructor or function must accept arguments of 'settings', being
    configuration settings for the data source, and 'environ' being
    information about the context in which the data source is being
    used. The resulting object must be a callable which directly returns
    an iterable/generator with the metrics for each sample.

    """

    def _decorator(func):
        @functools.wraps(func)
        def _properties(settings):
            def _factory(environ):
                return func(settings, environ)
            d = dict(properties)
            d['name'] = name
            d['factory'] = _factory
            return d
        return _properties
    return _decorator
