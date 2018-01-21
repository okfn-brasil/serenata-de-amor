from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


def _nr_endpoint_make_request_(wrapped, instance, args, kwargs):

    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _bind_params(operation_model, request_dict, *args, **kwargs):
        return request_dict

    # Get url and strip everything but scheme, hostname, and port.

    request_dict = _bind_params(*args, **kwargs)
    full_url = request_dict.get('url', '')
    parsed = urlparse.urlparse(full_url)
    url = '%s://%s' % (parsed.scheme, parsed.netloc)

    # Get HTTP verb as method
    method = request_dict.get('method', None)

    with ExternalTrace(transaction, library='botocore', url=url,
            method=method):
        return wrapped(*args, **kwargs)


def instrument_botocore_endpoint(module):
    wrap_function_wrapper(module, 'Endpoint.make_request',
            _nr_endpoint_make_request_)
