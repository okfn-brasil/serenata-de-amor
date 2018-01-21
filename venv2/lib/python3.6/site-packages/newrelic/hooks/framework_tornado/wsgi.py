import sys
import logging

from newrelic.api.function_trace import FunctionTrace
from newrelic.api.web_transaction import wrap_wsgi_application
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_function_wrapper

from newrelic.hooks.framework_tornado import (retrieve_request_transaction,
        initiate_request_monitoring, suspend_request_monitoring,
        finalize_request_monitoring, request_finished,
        retrieve_current_transaction)

_logger = logging.getLogger(__name__)

def _nr_wrapper_WSGIContainer___call__no_body_(wrapped, instance,
        args, kwargs):

    # This variant of the WSGIContainer.__call__() wrapper is used when
    # being used direct with HTTPServer and it is believed that we are
    # being called for a HTTP request where there is no request content.
    # There should be no transaction associated with the Tornado request
    # object and also no current active transaction. Create the
    # transaction but if it is None then it means recording of
    # transactions is not enabled then do not need to do anything.

    def _params(request, *args, **kwargs):
        return request

    request = _params(*args, **kwargs)

    transaction = initiate_request_monitoring(request)

    if transaction is None:
        return wrapped(*args, **kwargs)

    # Call the original method in a trace object to give better context
    # in transaction traces. It should only every return an exception is
    # situation where application was being shutdown so finalize the
    # transaction on any error.

    transaction.set_transaction_name(request.uri, 'Uri', priority=1)

    try:
        with FunctionTrace(transaction, name='Request/Process',
                group='Python/Tornado'):
            result = wrapped(*args, **kwargs)

    except:  # Catch all
        finalize_request_monitoring(request, *sys.exc_info())
        raise

    else:
        # In the case of the response completing immediately or an
        # exception occuring, then finish() should have been called on
        # the request already. We can't just exit the transaction in the
        # finish() call however as will need to still pop back up
        # through the above function trace. So if it has been flagged
        # that it is finished, which Tornado does by setting the request
        # object in the connection to None, then we exit the transaction
        # here. Otherwise we setup a function trace to track wait time
        # for deferred and suspend monitoring.

        if not request_finished(request):
            suspend_request_monitoring(request, name='Callback/Wait')

        elif not request.connection.stream.writing():
            finalize_request_monitoring(request)

        else:
            suspend_request_monitoring(request, name='Request/Output')

        return result

def _nr_wrapper_WSGIContainer___call__body_(wrapped, instance, args, kwargs):
    # This variant of the WSGIContainer.__call__() wrapper is used when
    # being used with HTTPServer directly and it is believed that we are
    # being called for a HTTP request where there is request content.
    # This would also be used where FallbackHandler was being used.
    # There should already be a transaction associated with the Tornado
    # request object and also a current active transaction.

    def _params(request, *args, **kwargs):
        return request

    request = _params(*args, **kwargs)

    transaction = retrieve_current_transaction()

    transaction.set_transaction_name(request.uri, 'Uri', priority=1)

    with FunctionTrace(transaction, name='Request/Process',
            group='Python/Tornado'):
        return wrapped(*args, **kwargs)

def _nr_wrapper_WSGIContainer___call___(wrapped, instance, args, kwargs):
    # This wrapper is used around the call which processes the complete
    # WSGI application execution. We do not have to deal with WSGI
    # itererable responses as that is all handled within the wrapped
    # function.
    #
    # We have to deal with a few cases in this wrapper, made more
    # complicated based on whether WSGIContainer is used in conjunction
    # with a FallbackHandler or whether it is used directly with a
    # HTTPServer instance.
    #
    # If WSGIContainer is used directly with a HTTPServer instance, if
    # we are called when there is no request content, there will be no
    # active transaction. If we are called when there is request content
    # then there will be an active transaction.
    #
    # If WSGIContainer is used in conjunction with a FallbackHandler
    # then there will always be an active transaction whether or not
    # there is any request content. We treat this case the same is if
    # there was request content even though there may not have been.

    def _params(request, *args, **kwargs):
        return request

    request = _params(*args, **kwargs)

    # We need to check to see if an existing transaction object has
    # already been created for the request. If there isn't one but there
    # is an active transaction, something is not right and we don't do
    # anything.

    transaction = retrieve_request_transaction(request)

    if transaction is None and retrieve_current_transaction():
        return wrapped(*args, **kwargs)

    # Now check for where we are being called on a HTTP request where
    # there is no request content. This will only be where used with
    # HTTPServer directly.

    if transaction is None:
        return _nr_wrapper_WSGIContainer___call__no_body_(wrapped, instance,
                args, kwargs)

    # Finally have case where being called on a HTTP request where there
    # is request content and used directly with HTTPServer or where being
    # used with FallbackHandler.

    return _nr_wrapper_WSGIContainer___call__body_(wrapped, instance,
            args, kwargs)

class _WSGIApplicationIterable(object): 

    def __init__(self, transaction, generator): 
        self.transaction = transaction 
        self.generator = generator 

    def __iter__(self): 
        try: 
            with FunctionTrace(self.transaction, name='Response', 
                    group='Python/WSGI'): 
                for item in self.generator: 
                    yield item 

        except GeneratorExit: 
            raise 

        except: # Catch all 
            self.transaction.record_exception() 
            raise 

    def close(self): 
        try: 
            with FunctionTrace(self.transaction, name='Finalize', 
                    group='Python/WSGI'): 
                if hasattr(self.generator, 'close'): 
                    name = callable_name(self.generator.close) 
                    with FunctionTrace(self.transaction, name): 
                        self.generator.close() 

        except: # Catch all 
            self.transaction.record_exception() 
            raise

class _WSGIApplication(object): 

    def __init__(self, wsgi_application): 
        self.wsgi_application = wsgi_application 

    def __call__(self, environ, start_response): 
        transaction = retrieve_current_transaction() 

        if transaction is None: 
            return self.wsgi_application(environ, start_response) 

        name = callable_name(self.wsgi_application) 

        with FunctionTrace(transaction, name='Application', 
                group='Python/WSGI'): 
            with FunctionTrace(transaction, name=name): 
                result = self.wsgi_application(environ, start_response) 

        return _WSGIApplicationIterable(transaction, result)

def _nr_wrapper_WSGIContainer___init___(wrapped, instance, args, kwargs):
    # This wrapper is used to inject a wrapper around the WSGI
    # application object passed into the WSGI container. That wrapper is
    # going to perform a subset of what we would normally do in the
    # WSGIApplicationWrapper class for normal WSGI applications.

    def _params(wsgi_application, *args, **kwargs):
        return wsgi_application

    wsgi_application = _params(*args, **kwargs)

    return wrapped(_WSGIApplication(wsgi_application))

def instrument_tornado_wsgi(module):
    wrap_function_wrapper(module, 'WSGIContainer.__init__',
            _nr_wrapper_WSGIContainer___init___)
    wrap_function_wrapper(module, 'WSGIContainer.__call__',
            _nr_wrapper_WSGIContainer___call___)

    import tornado

    if hasattr(tornado, 'version_info'):
        version = '.'.join(map(str, tornado.version_info))
    else:
        version = None

    wrap_wsgi_application(module, 'WSGIApplication.__call__',
            framework=('Tornado/WSGI', version))
