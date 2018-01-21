from collections import namedtuple

import newrelic.core.trace_node

from newrelic.common import system_info
from newrelic.core.metric import TimeMetric

_DatastoreNode = namedtuple('_DatastoreNode',
        ['product', 'target', 'operation', 'children', 'start_time',
        'end_time', 'duration', 'exclusive', 'host', 'port_path_or_id',
        'database_name', 'is_async'])



class DatastoreNode(_DatastoreNode):

    @property
    def instance_hostname(self):
        if self.host in system_info.LOCALHOST_EQUIVALENTS:
            hostname = system_info.gethostname()
        else:
            hostname = self.host
        return hostname

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        database node as well as all the child nodes.

        """

        product = self.product
        target = self.target
        operation = self.operation or 'other'

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

        ds_tracer_settings = stats.settings.datastore_tracer

        if (self.instance_hostname and
                self.port_path_or_id and
                ds_tracer_settings.instance_reporting.enabled):

            instance_metric_name = 'Datastore/instance/%s/%s/%s' % (product,
                    self.instance_hostname, self.port_path_or_id)

            yield TimeMetric(name=instance_metric_name, scope='',
                    duration=self.duration, exclusive=self.exclusive)

    def trace_node(self, stats, root, connections):
        product = self.product
        target = self.target
        operation = self.operation or 'other'

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

        ds_tracer_settings = stats.settings.datastore_tracer
        instance_enabled = ds_tracer_settings.instance_reporting.enabled
        db_name_enabled = ds_tracer_settings.database_name_reporting.enabled

        if instance_enabled:
            if self.instance_hostname:
                params['host'] = self.instance_hostname

            if self.port_path_or_id:
                params['port_path_or_id'] = self.port_path_or_id

        if db_name_enabled:
            if self.database_name:
                params['database_name'] = self.database_name

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)
