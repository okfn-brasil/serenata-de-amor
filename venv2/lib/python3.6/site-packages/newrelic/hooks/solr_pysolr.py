import newrelic.api.solr_trace

def instrument(module):

    if hasattr(module.Solr, 'search'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.search', 'pysolr', 'query')
    if hasattr(module.Solr, 'more_like_this'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.more_like_this', 'pysolr', 'query')
    if hasattr(module.Solr, 'suggest_terms'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.suggest_terms', 'pysolr', 'query')
    if hasattr(module.Solr, 'add'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.add', 'pysolr', 'add')
    if hasattr(module.Solr, 'delete'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.delete', 'pysolr', 'delete')
    if hasattr(module.Solr, 'commit'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.commit', 'pysolr', 'commit')
    if hasattr(module.Solr, 'optimize'):
        newrelic.api.solr_trace.wrap_solr_trace(
                module, 'Solr.optimize', 'pysolr', 'optimize')
