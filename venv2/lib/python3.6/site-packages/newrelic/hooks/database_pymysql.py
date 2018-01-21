from newrelic.api.database_trace import register_database_client
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_mysqldb import ConnectionFactory

def instance_info(args, kwargs):
    def _bind_params(host=None, user=None, passwd=None, db=None,
            port=None, *args, **kwargs):
        return host, port, db

    host, port, db = _bind_params(*args, **kwargs)

    return (host, port, db)

def instrument_pymysql(module):
    register_database_client(module, database_product='MySQL',
            quoting_style='single+double', explain_query='explain',
            explain_stmts=('select',), instance_info=instance_info)

    wrap_object(module, 'connect', ConnectionFactory, (module,))

    # The connect() function is actually aliased with Connect() and
    # Connection, the later actually being the Connection type object.
    # Instrument Connect(), but don't instrument Connection in case that
    # interferes with direct type usage. If people are using the
    # Connection object directly, they should really be using connect().

    if hasattr(module, 'Connect'):
        wrap_object(module, 'Connect', ConnectionFactory, (module,))
