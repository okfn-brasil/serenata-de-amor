from newrelic.api.database_trace import register_database_client
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import ConnectionFactory


def instrument_cx_oracle(module):
    register_database_client(module, database_product='Oracle',
            quoting_style='single+oracle')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
