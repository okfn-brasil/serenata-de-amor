from collections import namedtuple

import newrelic.core.trace_node

from newrelic.common import system_info
from newrelic.core.database_utils import sql_statement, explain_plan
from newrelic.core.metric import TimeMetric


_SlowSqlNode = namedtuple('_SlowSqlNode',
        ['duration', 'path', 'request_uri', 'sql', 'sql_format',
        'metric', 'dbapi2_module', 'stack_trace', 'connect_params',
        'cursor_params', 'sql_parameters', 'execute_params',
        'host', 'port_path_or_id', 'database_name'])


class SlowSqlNode(_SlowSqlNode):

    def __new__(cls, *args, **kwargs):
        node = _SlowSqlNode.__new__(cls, *args, **kwargs)
        node.statement = sql_statement(node.sql, node.dbapi2_module)
        return node

    @property
    def formatted(self):
        return self.statement.formatted(self.sql_format)

    @property
    def identifier(self):
        return self.statement.identifier


_DatabaseNode = namedtuple('_DatabaseNode',
        ['dbapi2_module', 'sql', 'children', 'start_time', 'end_time',
        'duration', 'exclusive', 'stack_trace', 'sql_format',
        'connect_params', 'cursor_params', 'sql_parameters',
        'execute_params', 'host', 'port_path_or_id', 'database_name',
        'is_async'])


class DatabaseNode(_DatabaseNode):

    def __new__(cls, *args, **kwargs):
        node = _DatabaseNode.__new__(cls, *args, **kwargs)
        node.statement = sql_statement(node.sql, node.dbapi2_module)
        return node

    @property
    def product(self):
        return self.dbapi2_module and self.dbapi2_module._nr_database_product

    @property
    def instance_hostname(self):
        if self.host in system_info.LOCALHOST_EQUIVALENTS:
            hostname = system_info.gethostname()
        else:
            hostname = self.host
        return hostname

    @property
    def operation(self):
        return self.statement.operation

    @property
    def target(self):
        return self.statement.target

    @property
    def formatted(self):
        return self.statement.formatted(self.sql_format)

    def explain_plan(self, connections):
        return explain_plan(connections, self.statement, self.connect_params,
                self.cursor_params, self.sql_parameters, self.execute_params,
                self.sql_format)

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        database node as well as all the child nodes.

        """

        product = self.product
        operation = self.operation or 'other'
        target = self.target

        # Determine the scoped metric

        statement_metric_name = 'Datastore/statement/%s/%s/%s' % (product,
                target, operation)

        operation_metric_name = 'Datastore/operation/%s/%s' % (product,
                operation)

        if target:
            scoped_metric_name = statement_metric_name
        else:
            scoped_metric_name = operation_metric_name

        yield TimeMetric(name=scoped_metric_name, scope=root.path,
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped rollup metrics

        yield TimeMetric(name='Datastore/all', scope='',
                duration=self.duration, exclusive=self.exclusive)

        yield TimeMetric(name='Datastore/%s/all' % product, scope='',
                duration=self.duration, exclusive=self.exclusive)

        if root.type == 'WebTransaction':
            yield TimeMetric(name='Datastore/allWeb', scope='',
                    duration=self.duration, exclusive=self.exclusive)

            yield TimeMetric(name='Datastore/%s/allWeb' % product, scope='',
                    duration=self.duration, exclusive=self.exclusive)
        else:
            yield TimeMetric(name='Datastore/allOther', scope='',
                    duration=self.duration, exclusive=self.exclusive)

            yield TimeMetric(name='Datastore/%s/allOther' % product, scope='',
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped operation metric

        yield TimeMetric(name=operation_metric_name, scope='',
                duration=self.duration, exclusive=self.exclusive)

        # Unscoped statement metric

        if target:
            yield TimeMetric(name=statement_metric_name, scope='',
                    duration=self.duration, exclusive=self.exclusive)

        # Unscoped instance Metric

        if self.instance_hostname and self.port_path_or_id:

            instance_metric_name = 'Datastore/instance/%s/%s/%s' % (product,
                    self.instance_hostname, self.port_path_or_id)

            yield TimeMetric(name=instance_metric_name, scope='',
                    duration=self.duration, exclusive=self.exclusive)

    def slow_sql_node(self, stats, root):
        product = self.product
        operation = self.operation or 'other'
        target = self.target

        if target:
            name = 'Datastore/statement/%s/%s/%s' % (product, target,
                    operation)
        else:
            name = 'Datastore/operation/%s/%s' % (product, operation)

        request_uri = ''
        if root.type == 'WebTransaction':
            request_uri = root.request_uri

        # Note that we do not limit the length of the SQL at this
        # point as we will need the whole SQL query when doing an
        # explain plan. Only limit the length when sending the
        # formatted SQL up to the data collector.

        return SlowSqlNode(duration=self.duration, path=root.path,
                request_uri=request_uri, sql=self.sql,
                sql_format=self.sql_format, metric=name,
                dbapi2_module=self.dbapi2_module,
                stack_trace=self.stack_trace,
                connect_params=self.connect_params,
                cursor_params=self.cursor_params,
                sql_parameters=self.sql_parameters,
                execute_params=self.execute_params,
                host=self.instance_hostname,
                port_path_or_id=self.port_path_or_id,
                database_name=self.database_name)

    def trace_node(self, stats, root, connections):
        product = self.product
        operation = self.operation or 'other'
        target = self.target

        if target:
            name = 'Datastore/statement/%s/%s/%s' % (product, target,
                    operation)
        else:
            name = 'Datastore/operation/%s/%s' % (product, operation)

        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        children = []

        root.trace_node_count += 1

        params = {}
        params['exclusive_duration_millis'] = 1000.0 * self.exclusive

        # Only send datastore instance params if not empty.

        if self.host:
            params['host'] = self.instance_hostname

        if self.port_path_or_id:
            params['port_path_or_id'] = self.port_path_or_id

        if self.database_name:
            params['database_name'] = self.database_name

        sql = self.formatted

        if sql:
            # Limit the length of any SQL that is reported back.

            limit = root.settings.agent_limits.sql_query_length_maximum

            params['sql'] = root.string_table.cache(sql[:limit])

            if self.stack_trace:
                params['backtrace'] = [root.string_table.cache(x) for x in
                        self.stack_trace]

            # Only perform an explain plan if this node ended up being
            # flagged to have an explain plan. This is applied when cap
            # on number of explain plans for whole harvest period is
            # applied across all transaction traces just prior to the
            # transaction traces being generated.

            if getattr(self, 'generate_explain_plan', None):
                explain_plan_data = self.explain_plan(connections)
                if explain_plan_data:
                    params['explain_plan'] = explain_plan_data

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)
