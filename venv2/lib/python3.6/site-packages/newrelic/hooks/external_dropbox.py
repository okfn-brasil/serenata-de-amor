import newrelic.api.external_trace


def instrument(module):

    def url_request(rest_obj, method, url, *args, **kwargs):
        return url

    if hasattr(module, 'rest') and hasattr(module.rest, 'RESTClientObject'):
        newrelic.api.external_trace.wrap_external_trace(
                module, 'rest.RESTClientObject.request', 'dropbox',
                url_request)
