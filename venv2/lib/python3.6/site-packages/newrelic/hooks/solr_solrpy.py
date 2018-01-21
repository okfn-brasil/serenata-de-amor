import newrelic.api.solr_trace

def instrument(module):

    if hasattr(module.Solr, 'delete'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.delete', 'solrpy', 'delete')
    if hasattr(module.Solr, 'delete_many'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.delete_many', 'solrpy', 'delete')
    if hasattr(module.Solr, 'delete_query'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.delete_query', 'solrpy', 'delete')
    if hasattr(module.Solr, 'add'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.add', 'solrpy', 'add')
    if hasattr(module.Solr, 'add_many'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.add_many', 'solrpy', 'add')
    if hasattr(module.Solr, 'commit'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.commit', 'solrpy', 'commit')
    if hasattr(module.Solr, 'optimize'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.optimize', 'solrpy', 'optimize')

    if hasattr(module.SolrConnection, 'query'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'SolrConnection.query', 'solrpy', 'query')
    if hasattr(module.SolrConnection, 'raw_query'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'SolrConnection.raw_query', 'solrpy', 'query')

    if hasattr(module, 'SearchHandler'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'SearchHandler.__call__', 'solrpy', 'query')
