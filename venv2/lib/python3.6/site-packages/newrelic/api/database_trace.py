import functools
import logging

from newrelic.api.coroutine_trace import return_value_fn
from newrelic.api.time_trace import TimeTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import FunctionWrapper, wrap_object
from newrelic.core.database_node import DatabaseNode
from newrelic.core.stack_trace import current_stack

_logger = logging.getLogger(__name__)


def register_database_client(dbapi2_module, database_product,
        quoting_style='single', explain_query=None, explain_stmts=[],
        instance_info=None):

    _logger.debug('Registering database client module %r where database '
            'is %r, quoting style is %r, explain query statement is %r and '
            'the SQL statements on which explain plans can be run are %r.',
            dbapi2_module, database_product, quoting_style, explain_query,
            explain_stmts)

    dbapi2_module._nr_database_product = database_product
    dbapi2_module._nr_quoting_style = quoting_style
    dbapi2_module._nr_explain_query = explain_query
    dbapi2_module._nr_explain_stmts = explain_stmts
    dbapi2_module._nr_instance_info = instance_info
    dbapi2_module._nr_datastore_instance_feature_flag = False


def enable_datastore_instance_feature(dbapi2_module):
    dbapi2_module._nr_datastore_instance_feature_flag = True


class DatabaseTrace(TimeTrace):

    node = DatabaseNode

    __async_explain_plan_logged = False

    def __init__(self, transaction, sql, dbapi2_module=None,
                 connect_params=None, cursor_params=None,
                 sql_parameters=None, execute_params=None,
                 host=None, port_path_or_id=None, database_name=None):

        super(DatabaseTrace, self).__init__(transaction)

        if transaction:
            self.sql = transaction._intern_string(sql)
        else:
            self.sql = sql

        self.dbapi2_module = dbapi2_module

        self.connect_params = connect_params
        self.cursor_params = cursor_params
        self.sql_parameters = sql_parameters
        self.execute_params = execute_params
        self.host = host
        self.port_path_or_id = port_path_or_id
        self.database_name = database_name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, dict(
                sql=self.sql, dbapi2_module=self.dbapi2_module))

    @property
    def is_async_mode(self):
        # Check for `async=1` keyword argument in connect_params, which
        # indicates that psycopg2 driver is being used in async mode.

        try:
            _, kwargs = self.connect_params
        except TypeError:
            return False
        else:
            return 'async' in kwargs and kwargs['async']

    def _log_async_warning(self):
        # Only log the warning the first time.

        if not DatabaseTrace.__async_explain_plan_logged:
            DatabaseTrace.__async_explain_plan_logged = True
            _logger.warning('Explain plans are not supported for queries '
                    'made over database connections in asynchronous mode.')

    def finalize_data(self, transaction, exc=None, value=None, tb=None):
        self.stack_trace = None

        connect_params = None
        cursor_params = None
        sql_parameters = None
        execute_params = None
        host = None
        port_path_or_id = None
        database_name = None

        settings = transaction.settings
        tt = settings.transaction_tracer
        agent_limits = settings.agent_limits
        ds_tracer = settings.datastore_tracer

        # Check settings, so that we only call instance_info when needed.

        instance_enabled = ds_tracer.instance_reporting.enabled
        db_name_enabled = ds_tracer.database_name_reporting.enabled

        if instance_enabled or db_name_enabled:

            if (self.dbapi2_module and
                    self.connect_params and
                    self.dbapi2_module._nr_datastore_instance_feature_flag and
                    self.dbapi2_module._nr_instance_info is not None):

                instance_info = self.dbapi2_module._nr_instance_info(
                        *self.connect_params)

                if instance_enabled:
                    host, port_path_or_id, _ = instance_info

                if db_name_enabled:
                    _, _, database_name = instance_info

        if (tt.enabled and settings.collect_traces and
                tt.record_sql != 'off'):
            if self.duration >= tt.stack_trace_threshold:
                if (transaction._stack_trace_count <
                        agent_limits.slow_sql_stack_trace):
                    self.stack_trace = [transaction._intern_string(x) for
                                        x in current_stack(skip=2)]
                    transaction._stack_trace_count += 1

            if self.is_async_mode and tt.explain_enabled:
                self._log_async_warning()
            else:
                # Only remember all the params for the calls if know
                # there is a chance we will need to do an explain
                # plan. We never allow an explain plan to be done if
                # an exception occurred in doing the query in case
                # doing the explain plan with the same inputs could
                # cause further problems.

                if (exc is None and
                        not self.is_async_mode and
                        tt.explain_enabled and
                        self.duration >= tt.explain_threshold and
                        self.connect_params is not None):
                    if (transaction._explain_plan_count <
                           agent_limits.sql_explain_plans):
                        connect_params = self.connect_params
                        cursor_params = self.cursor_params
                        sql_parameters = self.sql_parameters
                        execute_params = self.execute_params
                        transaction._explain_plan_count += 1

        self.sql_format = tt.record_sql

        self.connect_params = connect_params
        self.cursor_params = cursor_params
        self.sql_parameters = sql_parameters
        self.execute_params = execute_params
        self.host = host
        self.port_path_or_id = port_path_or_id
        self.database_name = database_name

    def terminal_node(self):
        return True


def DatabaseTraceWrapper(wrapped, sql, dbapi2_module=None):

    return_value = return_value_fn(wrapped)

    def _nr_database_trace_wrapper_(wrapped, instance, args, kwargs):
        transaction = current_transaction()

        if transaction is None:
            return wrapped(*args, **kwargs)

        if callable(sql):
            if instance is not None:
                _sql = sql(instance, *args, **kwargs)
            else:
                _sql = sql(*args, **kwargs)
        else:
            _sql = sql

        trace = DatabaseTrace(transaction, _sql, dbapi2_module)
        return return_value(trace, lambda: wrapped(*args, **kwargs))

    return FunctionWrapper(wrapped, _nr_database_trace_wrapper_)


def database_trace(sql, dbapi2_module=None):
    return functools.partial(DatabaseTraceWrapper, sql=sql,
            dbapi2_module=dbapi2_module)


def wrap_database_trace(module, object_path, sql, dbapi2_module=None):
    wrap_object(module, object_path, DatabaseTraceWrapper,
            (sql, dbapi2_module))
