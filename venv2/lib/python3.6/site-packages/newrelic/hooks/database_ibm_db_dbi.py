from newrelic.common.object_wrapper import wrap_object
from newrelic.api.database_trace import register_database_client

from newrelic.hooks.database_dbapi2 import ConnectionFactory


def instrument_ibm_db_dbi(module):
    register_database_client(module, database_product='IBMDB2',
            quoting_style='single', explain_query='EXPLAIN',
            explain_stmts=('select', 'insert', 'update', 'delete'))

    wrap_object(module, 'connect', ConnectionFactory, (module,))
