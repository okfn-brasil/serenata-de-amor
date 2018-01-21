from newrelic.api.database_trace import register_database_client
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import (ConnectionWrapper as
        DBAPI2ConnectionWrapper, ConnectionFactory as DBAPI2ConnectionFactory)

class ConnectionWrapper(DBAPI2ConnectionWrapper):

    def __enter__(self):
        transaction = current_transaction()
        name = callable_name(self.__wrapped__.__enter__)
        with FunctionTrace(transaction, name):
            self.__wrapped__.__enter__()

        # Must return a reference to self as otherwise will be
        # returning the inner connection object. If 'as' is used
        # with the 'with' statement this will mean no longer
        # using the wrapped connection object and nothing will be
        # tracked.

        return self

    def __exit__(self, exc, value, tb):
        transaction = current_transaction()
        name = callable_name(self.__wrapped__.__exit__)
        with FunctionTrace(transaction, name):
            # XXX The pymssql client doesn't appear to to force a
            # commit or rollback from __exit__() explicitly. Need
            # to work out what its behaviour is around auto commit
            # and rollback.

            #if exc is None:
            #    with DatabaseTrace(transaction, 'COMMIT',
            #            self._nr_dbapi2_module):
            #        return self.__wrapped__.__exit__(exc, value, tb)
            #else:
            #    with DatabaseTrace(transaction, 'ROLLBACK',
            #            self._nr_dbapi2_module):
            #        return self.__wrapped__.__exit__(exc, value, tb)

            return self.__wrapped__.__exit__(exc, value, tb)

class ConnectionFactory(DBAPI2ConnectionFactory):

    __connection_wrapper__ = ConnectionWrapper

def instrument_pymssql(module):
    # XXX Don't believe MSSQL provides a simple means of doing an
    # explain plan using one SQL statement prefix, eg., 'EXPLAIN'.

    register_database_client(module, database_product='MSSQL',
            quoting_style='single')

    wrap_object(module, 'connect', ConnectionFactory, (module,))
