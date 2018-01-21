from newrelic.api.database_trace import register_database_client, DatabaseTrace
from newrelic.api.function_trace import FunctionTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_names import callable_name
from newrelic.common.object_wrapper import wrap_object

from newrelic.hooks.database_dbapi2 import (CursorWrapper as
        DBAPI2CursorWrapper, ConnectionWrapper as DBAPI2ConnectionWrapper,
        ConnectionFactory as DBAPI2ConnectionFactory)

DEFAULT = object()


class CursorWrapper(DBAPI2CursorWrapper):

    def executescript(self, sql_script):
        transaction = current_transaction()
        with DatabaseTrace(transaction, sql_script, self._nr_dbapi2_module,
                self._nr_connect_params):
            return self.__wrapped__.executescript(sql_script)


class ConnectionWrapper(DBAPI2ConnectionWrapper):

    __cursor_wrapper__ = CursorWrapper

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
            if exc is None and value is None and tb is None:
                with DatabaseTrace(transaction, 'COMMIT',
                        self._nr_dbapi2_module, self._nr_connect_params):
                    return self.__wrapped__.__exit__(exc, value, tb)
            else:
                with DatabaseTrace(transaction, 'ROLLBACK',
                        self._nr_dbapi2_module, self._nr_connect_params):
                    return self.__wrapped__.__exit__(exc, value, tb)

    def execute(self, sql, parameters=DEFAULT):
        transaction = current_transaction()
        if parameters is not DEFAULT:
            with DatabaseTrace(transaction, sql, self._nr_dbapi2_module,
                    self._nr_connect_params, None, parameters):
                return self.__wrapped__.execute(sql, parameters)
        else:
            with DatabaseTrace(transaction, sql, self._nr_dbapi2_module,
                    self._nr_connect_params):
                return self.__wrapped__.execute(sql)

    def executemany(self, sql, seq_of_parameters):
        transaction = current_transaction()
        with DatabaseTrace(transaction, sql, self._nr_dbapi2_module,
                self._nr_connect_params, None, list(seq_of_parameters)[0]):
            return self.__wrapped__.executemany(sql, seq_of_parameters)

    def executescript(self, sql_script):
        transaction = current_transaction()
        with DatabaseTrace(transaction, sql_script, self._nr_dbapi2_module,
                self._nr_connect_params):
            return self.__wrapped__.executescript(sql_script)


class ConnectionFactory(DBAPI2ConnectionFactory):

    __connection_wrapper__ = ConnectionWrapper


def instance_info(args, kwargs):
    def _bind_params(database, *args, **kwargs):
        return database

    database = _bind_params(*args, **kwargs)
    host = 'localhost'
    port = None

    return (host, port, database)


def instrument_sqlite3_dbapi2(module):
    register_database_client(module, 'SQLite', quoting_style='single+double',
            instance_info=instance_info)

    wrap_object(module, 'connect', ConnectionFactory, (module,))


def instrument_sqlite3(module):
    # This case is to handle where the sqlite3 module was already
    # imported prior to agent initialization. In this situation, a
    # reference to the connect() method would already have been created
    # which referred to the uninstrumented version of the function
    # originally imported by sqlite3.dbapi2 before instrumentation could
    # be applied.

    if not isinstance(module.connect, ConnectionFactory):
        register_database_client(module, 'SQLite',
                quoting_style='single+double', instance_info=instance_info)

        wrap_object(module, 'connect', ConnectionFactory, (module,))
