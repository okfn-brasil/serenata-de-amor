from newrelic.api.datastore_trace import wrap_datastore_trace

_memcache_client_methods = ('get', 'gets', 'set', 'replace', 'add',
    'prepend', 'append', 'cas', 'delete', 'incr', 'decr', 'incr_multi',
    'get_multi', 'set_multi', 'add_multi', 'delete_multi', 'get_stats',
    'flush_all', 'touch')

def instrument_pylibmc_client(module):
    for name in _memcache_client_methods:
        if hasattr(module.Client, name):
            wrap_datastore_trace(module.Client, name,
                    product='Memcached', target=None, operation=name)
