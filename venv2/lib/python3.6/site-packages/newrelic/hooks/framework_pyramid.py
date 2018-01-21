"""Instrumentation module for Pyramid framework.

"""

# TODO
#
# * When using multi views, the PredicateMismatch exception will be
#   raised when one view cannot handle a request. This will be caught and
#   subsequent views then checked. If no view can handle the request,
#   by virtue of PredicateMismatch deriving from NotFound/HTTPException,
#   it would then finally be interpreted as a 404.
#
#   The problem is that exceptions are picked up around the attempt to
#   match the request against each view and it is not possible to know
#   if the PredicateMismatch is being raised against the last view or
#   an earlier one. This is important as it should be ignored for all but
#   the last view to be checked unless error_collector.ignore_status_codes
#   includes 404. In this case where 404 is to be ignored, it is ignored
#   for the last view as well.
#
#   As it stands, 404 will normally be ignored and so not an issue. If
#   however 404 was configured not to be ignored, then PredicateMismatch
#   as raised by views other than the last will be logged as an error when
#   it technically isn't. As a result, we always need to ignore the
#   PredicateMismatch exception. This does though then mean that if it
#   was actually raised by the last view to be checked, then we would
#   still ignore it, even though configured not to ignore 404.
#
#   The instrumentation could be improved to deal with this corner case
#   but since likely that error_collector.ignore_status_codes would not
#   be overridden, so tolerate it for now.

from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import FunctionWrapper, wrap_out_function
from newrelic.core.config import ignore_status_code

def instrument_pyramid_router(module):
    pyramid_version = None

    try:
        import pkg_resources
        pyramid_version = pkg_resources.get_distribution('pyramid').version
    except Exception:
        pass

    wrap_wsgi_application(module, 'Router.__call__',
            framework=('Pyramid', pyramid_version))

def should_ignore(exc, value, tb):
    from pyramid.httpexceptions import HTTPException
    from pyramid.exceptions import PredicateMismatch

    # Ignore certain exceptions based on HTTP status codes.

    if isinstance(value, HTTPException):
        if ignore_status_code(value.code):
            return True

    # Always ignore PredicateMismatch as it is raised by views to force
    # subsequent views to be consulted when multi views are being used.
    # It isn't therefore strictly an error as such as a subsequent view
    # could still handle the request. See TODO items though for a corner
    # case where this can mean an error isn't logged when it should.

    if isinstance(value, PredicateMismatch):
        return True

def view_handler_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    try:
        view_callable = wrapped.__original_view__ or wrapped
    except AttributeError:
        view_callable = wrapped

    name = callable_name(view_callable)

    transaction.set_transaction_name(name)

    with FunctionTrace(transaction, name):
        try:
            return wrapped(*args, **kwargs)

        except:  # Catch all
            transaction.record_exception(ignore_errors=should_ignore)
            raise

def wrap_view_handler(mapped_view):
    if hasattr(mapped_view, '_nr_wrapped'):
        return mapped_view
    else:
        wrapped = FunctionWrapper(mapped_view, view_handler_wrapper)
        wrapped._nr_wrapped = True
        return wrapped

def default_view_mapper_wrapper(wrapped, instance, args, kwargs):
    wrapper = wrapped(*args, **kwargs)

    def _args(view, *args, **kwargs):
        return view

    view = _args(*args, **kwargs)

    def _wrapper(context, request):
        transaction = current_transaction()

        if not transaction:
            return wrapper(context, request)

        name = callable_name(view)

        with FunctionTrace(transaction, name=name) as tracer:
            try:
                return wrapper(context, request)
            finally:
                attr = instance.attr
                if attr:
                    inst = getattr(request, '__view__', None)
                    if inst is not None:
                        name = callable_name(getattr(inst, attr))
                        transaction.set_transaction_name(name, priority=1)
                        tracer.name = name
                else:
                    inst = getattr(request, '__view__', None)
                    if inst is not None:
                        method = getattr(inst, '__call__')
                        if method:
                            name = callable_name(method)
                            transaction.set_transaction_name(name, priority=1)
                            tracer.name = name

    return _wrapper

def instrument_pyramid_config_views(module):
    # Location of the ViewDeriver class changed from pyramid.config to
    # pyramid.config.views so check if present before trying to update.

    if hasattr(module, 'ViewDeriver'):
        wrap_out_function(module, 'ViewDeriver.__call__',
                wrap_view_handler)
    elif hasattr(module, 'Configurator'):
        wrap_out_function(module, 'Configurator._derive_view',
                wrap_view_handler)

    if hasattr(module, 'DefaultViewMapper'):
        module.DefaultViewMapper.map_class_requestonly = FunctionWrapper(
                module.DefaultViewMapper.map_class_requestonly,
                default_view_mapper_wrapper)
        module.DefaultViewMapper.map_class_native = FunctionWrapper(
                module.DefaultViewMapper.map_class_native,
                default_view_mapper_wrapper)
