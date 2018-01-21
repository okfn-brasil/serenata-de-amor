from newrelic.common.object_wrapper import wrap_in_function
from newrelic.api.web_transaction import WSGIApplicationWrapper

def instrument_gevent_wsgi(module):

    def wrapper_WSGIServer___init__(*args, **kwargs):
        def _bind_params(self, listener, application, *args, **kwargs):
            return self, listener, application, args, kwargs

        self, listener, application, _args, _kwargs = _bind_params(
                *args, **kwargs)

        application = WSGIApplicationWrapper(application)

        _args = (self, listener, application) + _args

        return _args, _kwargs

    wrap_in_function(module, 'WSGIServer.__init__',
            wrapper_WSGIServer___init__)

def instrument_gevent_pywsgi(module):

    def wrapper_WSGIServer___init__(*args, **kwargs):
        def _bind_params(self, listener, application, *args, **kwargs):
            return self, listener, application, args, kwargs

        self, listener, application, _args, _kwargs = _bind_params(
                *args, **kwargs)

        application = WSGIApplicationWrapper(application)

        _args = (self, listener, application) + _args

        return _args, _kwargs

    wrap_in_function(module, 'WSGIServer.__init__',
            wrapper_WSGIServer___init__)
