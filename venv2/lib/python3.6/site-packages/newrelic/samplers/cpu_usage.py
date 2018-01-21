"""This module implements a data source for generating metrics about CPU
usage.

"""

import os
import time

from newrelic.common.system_info import logical_processor_count
from newrelic.common.stopwatch import start_timer

from newrelic.samplers.decorators import data_source_factory

@data_source_factory(name='CPU Usage')
class _CPUUsageDataSource(object):

    def __init__(self, settings, environ):
        self._timer = None
        self._times = None

    def start(self):
        self._timer = start_timer()
        try:
            self._times = os.times()
        except Exception:
            self._times = None

    def stop(self):
        self._timer = None
        self._times = None

    def __call__(self):
        if self._times is None:
            return

        new_times = os.times()
        user_time = new_times[0] - self._times[0]

        elapsed_time = self._timer.restart_timer()
        utilization = user_time / (elapsed_time*logical_processor_count())

        self._times = new_times

        yield ('CPU/User Time', user_time)
        yield ('CPU/User/Utilization', utilization)

cpu_usage_data_source = _CPUUsageDataSource
