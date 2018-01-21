from collections import namedtuple

Metric = namedtuple('Metric', ['name', 'scope'])

ApdexMetric = namedtuple('ApdexMetric',
        ['name', 'satisfying', 'tolerating', 'frustrating', 'apdex_t'])

TimeMetric = namedtuple('TimeMetric',
        ['name', 'scope', 'duration', 'exclusive'])
