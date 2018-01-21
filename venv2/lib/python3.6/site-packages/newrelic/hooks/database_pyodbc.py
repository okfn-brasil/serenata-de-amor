from newrelic.api.database_trace import register_database_client
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import ConnectionFactory

def instrument_pyodbc(module):
    register_database_client(module, database_product='ODBC',
            quoting_style='single')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
