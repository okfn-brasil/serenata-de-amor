from newrelic.api.datastore_trace import wrap_datastore_trace

_memcache_client_methods = ('set', 'set_many', 'add', 'replace', 'append',
    'prepend', 'cas', 'get', 'get_many', 'gets', 'gets_many', 'delete',
    'delete_many', 'incr', 'decr', 'touch', 'stats', 'flush_all', 'quit')

def instrument_pymemcache_client(module):
    for name in _memcache_client_methods:
        if hasattr(module.Client, name):
            wrap_datastore_trace(module.Client, name,
                    product='Memcached', target=None, operation=name)
