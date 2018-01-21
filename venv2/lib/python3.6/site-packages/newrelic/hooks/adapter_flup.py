import newrelic.api.web_transaction
import newrelic.api.in_function

def wrap_wsgi_application_entry_point(server, application, *args, **kwargs):
    application = newrelic.api.web_transaction.WSGIApplicationWrapper(
            application)
    args = [server, application] + list(args)
    return (args, kwargs)

def instrument_flup_server_cgi(module):
    newrelic.api.in_function.wrap_in_function(module,
            'WSGIServer.__init__', wrap_wsgi_application_entry_point)

def instrument_flup_server_ajp_base(module):
    newrelic.api.in_function.wrap_in_function(module,
            'BaseAJPServer.__init__', wrap_wsgi_application_entry_point)

def instrument_flup_server_fcgi_base(module):
    newrelic.api.in_function.wrap_in_function(module,
            'BaseFCGIServer.__init__', wrap_wsgi_application_entry_point)

def instrument_flup_server_scgi_base(module):
    newrelic.api.in_function.wrap_in_function(module,
            'BaseSCGIServer.__init__', wrap_wsgi_application_entry_point)
