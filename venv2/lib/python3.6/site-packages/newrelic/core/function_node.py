from collections import namedtuple

import newrelic.core.trace_node

from newrelic.core.metric import TimeMetric

from newrelic.packages import six

_FunctionNode = namedtuple('_FunctionNode',
        ['group', 'name', 'children', 'start_time', 'end_time',
        'duration', 'exclusive', 'label', 'params', 'rollup',
        'is_async'])



class FunctionNode(_FunctionNode):

    def time_metrics(self, stats, root, parent):
        """Return a generator yielding the timed metrics for this
        function node as well as all the child nodes.

        """

        name = '%s/%s' % (self.group, self.name)

        yield TimeMetric(name=name, scope='', duration=self.duration,
                exclusive=self.exclusive)

        yield TimeMetric(name=name, scope=root.path,
                duration=self.duration, exclusive=self.exclusive)

        # Generate one or more rollup metric if any have been specified.
        # We can actually get a single string value or a list of strings
        # if more than one.
        #
        # We actually implement two cases here. If the rollup name ends
        # with /all, then we implement the old style, which is to
        # generate an unscoped /all metric, plus if a web transaction
        # then /allWeb. For non web transaction also generate /allOther.
        #
        # If not the old style, but new style, the rollup metric
        # has scope corresponding to the transaction type.
        #
        # For the old style it must match one of the existing rollup
        # categories recognised by the UI. For the new, we can add our
        # own rollup categories.

        if self.rollup:
            if isinstance(self.rollup, six.string_types):
                rollups = [self.rollup]
            else:
                rollups = self.rollup

            for rollup in rollups:
                if rollup.endswith('/all'):
                    yield TimeMetric(name=rollup, scope='',
                            duration=self.duration, exclusive=None)

                    if root.type == 'WebTransaction':
                        yield TimeMetric(name=rollup + 'Web', scope='',
                                duration=self.duration, exclusive=None)
                    else:
                        yield TimeMetric(name=rollup + 'Other', scope='',
                                duration=self.duration, exclusive=None)

                else:
                    yield TimeMetric(name=rollup, scope=root.type,
                            duration=self.duration, exclusive=None)

        # Now for the children.

        for child in self.children:
            for metric in child.time_metrics(stats, root, self):
                yield metric

    def trace_node(self, stats, root, connections):

        name = '%s/%s' % (self.group, self.name)

        name = root.string_table.cache(name)

        start_time = newrelic.core.trace_node.node_start_time(root, self)
        end_time = newrelic.core.trace_node.node_end_time(root, self)

        root.trace_node_count += 1

        children = []

        for child in self.children:
            if root.trace_node_count > root.trace_node_limit:
                break
            children.append(child.trace_node(stats, root, connections))

        params = self.params or {}
        params['exclusive_duration_millis'] = 1000.0 * self.exclusive

        return newrelic.core.trace_node.TraceNode(start_time=start_time,
                end_time=end_time, name=name, params=params, children=children,
                label=self.label)
