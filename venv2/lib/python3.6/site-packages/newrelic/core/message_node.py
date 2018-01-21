from collections import namedtuple

import newrelic.core.trace_node

from newrelic.core.metric import TimeMetric

_MessageNode = namedtuple('_MessageNode',
        ['library', 'operation', 'children', 'start_time',
        'end_time', 'duration', 'exclusive', 'destination_name',
        'destination_type', 'params', 'is_async'])


class MessageNode(_MessageNode):

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        messagebroker node as well as all the child nodes.

        """
        name = 'MessageBroker/%s/%s/%s/Named/%s' % (self.library,
                self.destination_type, self.operation, self.destination_name)

        # Unscoped metric

        yield TimeMetric(name=name, scope='',
                duration=self.duration, exclusive=self.exclusive)

        # Scoped metric

        yield TimeMetric(name=name, scope=root.path,
                duration=self.duration, exclusive=self.exclusive)

    def trace_node(self, stats, root, connections):
        name = 'MessageBroker/%s/%s/%s/Named/%s' % (self.library,
                self.destination_type, self.operation, self.destination_name)
        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        children = []

        root.trace_node_count += 1

        params = self.params or {}
        params['exclusive_duration_millis'] = 1000.0 * self.exclusive

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)
