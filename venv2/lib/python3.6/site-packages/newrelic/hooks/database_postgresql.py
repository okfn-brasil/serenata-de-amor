from newrelic.common.object_wrapper import wrap_object
from newrelic.api.database_trace import register_database_client

from newrelic.hooks.database_psycopg2 import instance_info


def instrument_postgresql_driver_dbapi20(module):
    register_database_client(module, database_product='Postgres',
            quoting_style='single+dollar', explain_query='explain',
            explain_stmts=('select', 'insert', 'update', 'delete'),
            instance_info=instance_info)

    from newrelic.hooks.database_psycopg2 import ConnectionFactory

    wrap_object(module, 'connect', ConnectionFactory, (module,))


def instrument_postgresql_interface_proboscis_dbapi2(module):
    register_database_client(module, database_product='Postgres',
            quoting_style='single+dollar', explain_query='explain',
            explain_stmts=('select', 'insert', 'update', 'delete'),
            instance_info=instance_info)

    from newrelic.hooks.database_dbapi2 import ConnectionFactory

    wrap_object(module, 'connect', ConnectionFactory, (module,))
