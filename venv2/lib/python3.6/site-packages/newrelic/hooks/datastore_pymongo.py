from newrelic.api.datastore_trace import wrap_datastore_trace
from newrelic.api.function_trace import wrap_function_trace

_pymongo_client_methods = ('save', 'insert', 'update', 'drop', 'remove',
    'find_one', 'find', 'count', 'create_index', 'ensure_index',
    'drop_indexes', 'drop_index', 'reindex', 'index_information',
    'options', 'group', 'rename', 'distinct', 'map_reduce',
    'inline_map_reduce', 'find_and_modify')

def instrument_pymongo_connection(module):
    # Must name function explicitly as pymongo overrides the
    # __getattr__() method in a way that breaks introspection.

    rollup = ('Datastore/all', 'Datastore/MongoDB/all')

    wrap_function_trace(module, 'Connection.__init__',
            name='%s:Connection.__init__' % module.__name__,
            terminal=True, rollup=rollup)

def instrument_pymongo_mongo_client(module):
    # Must name function explicitly as pymongo overrides the
    # __getattr__() method in a way that breaks introspection.

    rollup = ('Datastore/all', 'Datastore/MongoDB/all')

    wrap_function_trace(module, 'MongoClient.__init__',
            name='%s:MongoClient.__init__' % module.__name__,
            terminal=True, rollup=rollup)

def instrument_pymongo_collection(module):
    def _collection_name(collection, *args, **kwargs):
        return collection.name

    for name in _pymongo_client_methods:
        if hasattr(module.Collection, name):
            wrap_datastore_trace(module.Collection, name, product='MongoDB',
                    target=_collection_name, operation=name)
