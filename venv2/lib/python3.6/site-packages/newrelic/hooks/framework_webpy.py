import sys

import newrelic.packages.six as six

import newrelic.api.transaction
import newrelic.api.function_trace
import newrelic.api.in_function
import newrelic.api.out_function
import newrelic.api.pre_function
from newrelic.api.object_wrapper import callable_name
from newrelic.api.web_transaction import WSGIApplicationWrapper

def transaction_name_delegate(*args, **kwargs):
    transaction = newrelic.api.transaction.current_transaction()
    if transaction:
        if isinstance(args[1], six.string_types):
            f = args[1]
        else:
            f = callable_name(args[1])
        transaction.set_transaction_name(f)
    return (args, kwargs)

def wrap_handle_exception(self):
    transaction = newrelic.api.transaction.current_transaction()
    if transaction:
        transaction.record_exception(*sys.exc_info())

def template_name(render_obj, name):
    return name

def instrument(module):

    if module.__name__ == 'web.application':
        newrelic.api.out_function.wrap_out_function(
                module, 'application.wsgifunc', WSGIApplicationWrapper)
        newrelic.api.in_function.wrap_in_function(
                module, 'application._delegate', transaction_name_delegate)
        newrelic.api.pre_function.wrap_pre_function(
                module, 'application.internalerror', wrap_handle_exception)

    elif module.__name__ == 'web.template':
        newrelic.api.function_trace.wrap_function_trace(
                module, 'render.__getattr__', template_name, 'Template/Render')
