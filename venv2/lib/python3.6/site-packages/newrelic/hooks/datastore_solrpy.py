from newrelic.api.datastore_trace import wrap_datastore_trace

_solrpy_client_methods = ('query', 'add', 'add_many', 'delete', 'delete_many',
'delete_query', 'commit', 'optimize', 'raw_query')

def instrument_solrpy(module):
    for name in _solrpy_client_methods:
        if hasattr(module.SolrConnection, name):
            wrap_datastore_trace(module.SolrConnection, name,
                    product='Solr', target=None, operation=name)
