import newrelic.api.memcache_trace

def instrument(module):

    if hasattr(module.Client, 'add'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.add', 'add')
    if hasattr(module.Client, 'append'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.append', 'replace')
    if hasattr(module.Client, 'cas'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.cas', 'replace')
    if hasattr(module.Client, 'decr'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.decr', 'decr')
    if hasattr(module.Client, 'delete'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.delete', 'delete')
    if hasattr(module.Client, 'delete_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.delete_multi', 'delete')
    if hasattr(module.Client, 'get'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.get', 'get')
    if hasattr(module.Client, 'gets'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.gets', 'get')
    if hasattr(module.Client, 'get_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.get_multi', 'get')
    if hasattr(module.Client, 'incr'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.incr', 'incr')
    if hasattr(module.Client, 'prepend'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.prepend', 'replace')
    if hasattr(module.Client, 'replace'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.replace', 'replace')
    if hasattr(module.Client, 'set'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.set', 'set')
    if hasattr(module.Client, 'set_multi'):
        newrelic.api.memcache_trace.wrap_memcache_trace(
                module, 'Client.set_multi', 'set')
