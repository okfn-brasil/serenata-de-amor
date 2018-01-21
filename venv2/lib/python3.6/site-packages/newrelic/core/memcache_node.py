from collections import namedtuple

import newrelic.core.trace_node

from newrelic.core.metric import TimeMetric

_MemcacheNode = namedtuple('_MemcacheNode',
        ['command', 'children', 'start_time', 'end_time', 'duration',
        'exclusive', 'is_async'])



class MemcacheNode(_MemcacheNode):

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        memcache node as well as all the child nodes.

        """

        yield TimeMetric(name='Memcache/all', scope='',
                duration=self.duration, exclusive=self.exclusive)

        if root.type == 'WebTransaction':
            yield TimeMetric(name='Memcache/allWeb', scope='',
                    duration=self.duration, exclusive=self.exclusive)
        else:
            yield TimeMetric(name='Memcache/allOther', scope='',
                    duration=self.duration, exclusive=self.exclusive)

        name = 'Memcache/%s' % self.command

        yield TimeMetric(name=name, scope='', duration=self.duration,
                  exclusive=self.exclusive)

        yield TimeMetric(name=name, scope=root.path,
                duration=self.duration, exclusive=self.exclusive)

    def trace_node(self, stats, root, connections):

        name = 'Memcache/%s' % self.command

        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        children = []

        root.trace_node_count += 1

        params = {}
        params['exclusive_duration_millis'] = 1000.0 * self.exclusive

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=None)
