import sys

from newrelic.api.web_transaction import WSGIApplicationWrapper
from newrelic.common.object_wrapper import wrap_out_function


def _nr_wrapper_Application_wsgi_(application):
    # Normally Application.wsgi() returns a WSGI application, but in
    # the case of the Tornado worker it can return an Tornado ASYNC
    # application object. Not being a WSGI application object we can
    # not wrap it with a WSGI application wrapper as the prototype
    # mismatch will cause it to fail when called.
    #
    # Having to have this check in this way is a bit annoying, but
    # the only other alternative was to instrument separately all the
    # different worker types which would have been more work. Thus
    # tolerate having the check here.

    if not 'tornado.web' in sys.modules:
        return WSGIApplicationWrapper(application) 

    try:
        import tornado.web
    except ImportError:
        return WSGIApplicationWrapper(application) 

    if not isinstance(application, tornado.web.Application):
        return WSGIApplicationWrapper(application) 

    return application

def instrument_gunicorn_app_base(module): 
    wrap_out_function(module, 'Application.wsgi',
            _nr_wrapper_Application_wsgi_) 
