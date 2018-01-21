from newrelic.api.datastore_trace import wrap_datastore_trace

_pysolr_client_methods = ('search', 'more_like_this', 'suggest_terms', 'add',
'delete', 'commit', 'optimize', 'extract')

_pysolr_admin_methods = ('status', 'create', 'reload', 'rename', 'swap',
    'unload', 'load')

def instrument_pysolr(module):
    for name in _pysolr_client_methods:
        if hasattr(module.Solr, name):
            wrap_datastore_trace(module.Solr, name,
                    product='Solr', target=None, operation=name)

    if hasattr(module, 'SolrCoreAdmin'):
        for name in _pysolr_admin_methods:
            if hasattr(module.SolrCoreAdmin, name):
                wrap_datastore_trace(module.SolrCoreAdmin, name,
                        product='Solr', target=None,
                        operation='admin.%s' % name)
