try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import newrelic.packages.six as six

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper

def _nr_wrapper_opener_director_open_(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _bind_params(fullurl, *args, **kwargs):
        if isinstance(fullurl, six.string_types):
            return fullurl
        else:
            return fullurl.get_full_url()

    url = _bind_params(*args, **kwargs)

    details = urlparse.urlparse(url)

    if details.hostname is None:
        return wrapped(*args, **kwargs)

    with ExternalTrace(transaction, 'urllib2', url):
        return wrapped(*args, **kwargs)

def instrument(module):

    if hasattr(module, 'OpenerDirector'):
        wrap_function_wrapper(module, 'OpenerDirector.open',
            _nr_wrapper_opener_director_open_)
