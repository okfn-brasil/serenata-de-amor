"""Instrumentation module for CherryPy framework.

"""

# TODO
#
# * We don't track time spent in a user supplied error response callback.
#   We do track time in the handle_error() function which calls it though.
#   Because the error_response attribute of the request object could be
#   updated dynamically, is tricky to handle. We would need to replace
#   error_response attribute at the time the request is created, with a
#   data descriptor which detects when it is set and saves away value, and
#   then wraps the value with a function trace when later access. May
#   have to deal with someone overriding the class attribute version of
#   error_response as well, which means need a class level data descriptor
#   which gets trickier as it isn't bound to an instance and has to do
#   tricks to store the error response handler being set against the
#   instance if set via an instance.
#
# * We don't track time spent in hook functions which may be registered
#   for events such as before_handler, on_end_request etc.
#
# * We don't handle any sub dispatching that may be occuring due to the
#   use of XMLRPCDispatcher.

from newrelic.api.function_trace import FunctionTrace, wrap_function_trace
from newrelic.api.transaction import current_transaction
from newrelic.api.web_transaction import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import (ObjectProxy, function_wrapper,
        wrap_function_wrapper)
from newrelic.core.config import ignore_status_code

def framework_details():
    import cherrypy
    return ('CherryPy', getattr(cherrypy, '__version__', None))

def should_ignore(exc, value, tb):
    from cherrypy import HTTPError, HTTPRedirect

    # Ignore certain exceptions based on HTTP status codes.

    if isinstance(value, (HTTPError, HTTPRedirect)):
        if ignore_status_code(value.status):
            return True

    # Ignore certain exceptions based on their name.

    module = value.__class__.__module__
    name = value.__class__.__name__
    fullname = '%s:%s' % (module, name)

    ignore_exceptions = ('cherrypy._cperror:InternalRedirect',)

    if fullname in ignore_exceptions:
        return True

@function_wrapper
def handler_wrapper(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    # Name the web transaction after the handler function.

    name = callable_name(wrapped)
    transaction.set_transaction_name(name=name)

    # Track how long is spent in the handler and record any exceptions
    # except those which are used for controlling the actions of the
    # application.

    with FunctionTrace(transaction, name=name):
        try:
            return wrapped(*args, **kwargs)

        except:  # Catch all
            transaction.record_exception(ignore_errors=should_ignore)
            raise

class ResourceProxy(ObjectProxy):

    def __getattr__(self, name):
        # Methods on the wrapped object corresponding to the HTTP
        # method will always be upper case. Wrap the method when
        # returned with the handler wrapper.

        attr = super(ResourceProxy, self).__getattr__(name)
        return name.isupper() and handler_wrapper(attr) or attr

def wrapper_Dispatcher_find_handler(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        # Call the original wrapped function to find the handler.

        obj, vpath = wrapped(*args, **kwargs)

    except:  # Catch all
        # Can end up here when a custom _cp_dispatch() method is
        # used and that raises an exception.

        transaction.record_exception()
        raise

    if obj:
        if instance.__class__.__name__ == 'MethodDispatcher':
            # We initially name the web transaction as if the
            # corresponding method for the HTTP method will not
            # be found and the request will not be allowed. This
            # will be overridden with the actual handler name
            # when the subsequent wrapper around the handler is
            # executed.

            transaction.set_transaction_name('405', group='StatusCode')

            # We have to use a custom object proxy here in order
            # to intercept accesses made by the dispatcher on the
            # returned object, after this function returns, to
            # retrieve the method of the object corresponding to
            # the HTTP method. For each such access we wrap what
            # is returned in the handler wrapper.

            obj = ResourceProxy(obj)

        else:
            # Should be the actual handler, wrap it with the
            # handler wrapper.

            obj = handler_wrapper(obj)

    else:
        # No handler could be found so name the web transaction
        # after the 404 status code.

        transaction.set_transaction_name('404', group='StatusCode')

    return obj, vpath

def wrapper_RoutesDispatcher_find_handler(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    try:
        # Call the original wrapped function to find the handler.

        handler = wrapped(*args, **kwargs)

    except:  # Catch all
        # Can end up here when the URL was invalid in some way.

        transaction.record_exception()
        raise

    if handler:
        # Should be the actual handler, wrap it with the handler
        # wrapper.

        handler = handler_wrapper(handler)

    else:
        # No handler could be found so name the web transaction
        # after the 404 status code.

        transaction.set_transaction_name('404', group='StatusCode')

    return handler

def instrument_cherrypy__cpreqbody(module):
    wrap_function_trace(module, 'process_multipart')
    wrap_function_trace(module, 'process_multipart_form_data')

def instrument_cherrypy__cprequest(module):
    wrap_function_trace(module, 'Request.handle_error')

def instrument_cherrypy__cpdispatch(module):
    wrap_function_wrapper(module, 'Dispatcher.find_handler',
            wrapper_Dispatcher_find_handler)
    wrap_function_wrapper(module, 'RoutesDispatcher.find_handler',
            wrapper_RoutesDispatcher_find_handler)

def instrument_cherrypy__cpwsgi(module):
    wrap_wsgi_application(module, 'CPWSGIApp.__call__',
            framework=framework_details())

def instrument_cherrypy__cptree(module):
    wrap_wsgi_application(module, 'Application.__call__',
            framework=framework_details())
