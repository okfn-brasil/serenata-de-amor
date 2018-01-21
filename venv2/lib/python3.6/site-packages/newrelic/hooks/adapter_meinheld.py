import newrelic.api.web_transaction
import newrelic.api.in_function

def instrument_meinheld_server(module):

    def wrap_wsgi_application_entry_point(application, *args, **kwargs):
        application = newrelic.api.web_transaction.WSGIApplicationWrapper(
                application)
        args = [application] + list(args)
        return (args, kwargs)

    newrelic.api.in_function.wrap_in_function(module,
            'run', wrap_wsgi_application_entry_point)
