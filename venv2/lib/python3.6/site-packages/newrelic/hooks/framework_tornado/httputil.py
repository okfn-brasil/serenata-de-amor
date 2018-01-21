from newrelic.api.function_trace import wrap_function_trace

def instrument_tornado_httputil(module):
    if hasattr(module, 'parse_body_arguments'):
        wrap_function_trace(module, 'parse_body_arguments')
    if hasattr(module, 'parse_multipart_form_data'):
        wrap_function_trace(module, 'parse_multipart_form_data')
