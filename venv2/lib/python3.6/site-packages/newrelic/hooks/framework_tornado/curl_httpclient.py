from newrelic.api.function_trace import wrap_function_trace

def instrument_tornado_curl_httpclient(module):
    wrap_function_trace(module, 'CurlAsyncHTTPClient.fetch')
