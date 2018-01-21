"""The stats engine is what collects the accumulated transactions metrics,
details of errors and slow transactions. There is one instance of the stats
engine per application. This will be cleared upon each successful harvest of
data whereby it is sent to the core application.

"""

import base64
import copy
import logging
import operator
import random
import zlib
import time
import sys

import newrelic.packages.six as six

from newrelic.core.attribute_filter import DST_ERROR_COLLECTOR
from newrelic.core.attribute import create_user_attributes

from newrelic.core.attribute import process_user_attribute
from newrelic.core.database_utils import explain_plan
from newrelic.core.error_collector import TracedError
from newrelic.core.metric import TimeMetric
from newrelic.core.stack_trace import exception_stack

from newrelic.api.settings import STRIP_EXCEPTION_MESSAGE
from newrelic.common.encoding_utils import json_encode

_logger = logging.getLogger(__name__)


def c2t(count=0, total=0.0, min=0.0, max=0.0, sum_of_squares=0.0):
    return (count, total, total, min, max, sum_of_squares)


class ApdexStats(list):

    """Bucket for accumulating apdex metrics.

    """

    # Is based on a list of length 6 as all metrics are sent to the core
    # application as that and list as base class means it encodes direct
    # to JSON as we need it. In this case only the first 3 entries are
    # strictly used for the metric. The 4th and 5th entries are set to
    # be the apdex_t value in use at the time.

    def __init__(self, satisfying=0, tolerating=0, frustrating=0, apdex_t=0.0):
        super(ApdexStats, self).__init__([satisfying, tolerating,
                frustrating, apdex_t, apdex_t, 0])

    satisfying = property(operator.itemgetter(0))
    tolerating = property(operator.itemgetter(1))
    frustrating = property(operator.itemgetter(2))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[0] += other[0]
        self[1] += other[1]
        self[2] += other[2]

        self[3] = ((self[0] or self[1] or self[2]) and
                min(self[3], other[3]) or other[3])
        self[4] = max(self[4], other[3])

    def merge_apdex_metric(self, metric):
        """Merge data from an apdex metric object."""

        self[0] += metric.satisfying
        self[1] += metric.tolerating
        self[2] += metric.frustrating

        self[3] = ((self[0] or self[1] or self[2]) and
                min(self[3], metric.apdex_t) or metric.apdex_t)
        self[4] = max(self[4], metric.apdex_t)


class TimeStats(list):

    """Bucket for accumulating time and value metrics.

    """

    # Is based on a list of length 6 as all metrics are sent to the core
    # application as that and list as base class means it encodes direct
    # to JSON as we need it.

    def __init__(self, call_count=0, total_call_time=0.0,
                total_exclusive_call_time=0.0, min_call_time=0.0,
                max_call_time=0.0, sum_of_squares=0.0):
        if total_exclusive_call_time is None:
            total_exclusive_call_time = total_call_time
        super(TimeStats, self).__init__([call_count, total_call_time,
                total_exclusive_call_time, min_call_time,
                max_call_time, sum_of_squares])

    call_count = property(operator.itemgetter(0))
    total_call_time = property(operator.itemgetter(1))
    total_exclusive_call_time = property(operator.itemgetter(2))
    min_call_time = property(operator.itemgetter(3))
    max_call_time = property(operator.itemgetter(4))
    sum_of_squares = property(operator.itemgetter(5))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[1] += other[1]
        self[2] += other[2]
        self[3] = self[0] and min(self[3], other[3]) or other[3]
        self[4] = max(self[4], other[4])
        self[5] += other[5]

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += other[0]

    def merge_raw_time_metric(self, duration, exclusive=None):
        """Merge time value."""

        if exclusive is None:
            exclusive = duration

        self[1] += duration
        self[2] += exclusive
        self[3] = self[0] and min(self[3], duration) or duration
        self[4] = max(self[4], duration)
        self[5] += duration ** 2

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += 1

    def merge_time_metric(self, metric):
        """Merge data from a time metric object."""

        self.merge_raw_time_metric(metric.duration, metric.exclusive)

    def merge_custom_metric(self, value):
        """Merge data value."""

        self.merge_raw_time_metric(value)


class CountStats(TimeStats):

    def merge_stats(self, other):
        self[0] += other[0]

    def merge_raw_time_metric(self, duration, exclusive=None):
        pass


class CustomMetrics(object):

    """Table for collection a set of value metrics.

    """

    def __init__(self):
        self.__stats_table = {}

    def __contains__(self, key):
        return key in self.__stats_table

    def record_custom_metric(self, name, value):
        """Record a single value metric, merging the data with any data
        from prior value metrics with the same name.

        """
        if isinstance(value, dict):
            if len(value) == 1 and 'count' in value:
                new_stats = CountStats(call_count=value['count'])
            else:
                new_stats = TimeStats(*c2t(**value))
        else:
            new_stats = TimeStats(1, value, value, value, value, value**2)

        stats = self.__stats_table.get(name)
        if stats is None:
            self.__stats_table[name] = new_stats
        else:
            stats.merge_stats(new_stats)

    def metrics(self):
        """Returns an iterator over the set of value metrics. The items
        returned are a tuple consisting of the metric name and accumulated
        stats for the metric.

        """

        return six.iteritems(self.__stats_table)

    def reset_metric_stats(self):
        """Resets the accumulated statistics back to initial state for
        metric data.

        """
        self.__stats_table = {}


class SlowSqlStats(list):

    def __init__(self):
        super(SlowSqlStats, self).__init__([0, 0, 0, 0, None])

    call_count = property(operator.itemgetter(0))
    total_call_time = property(operator.itemgetter(1))
    min_call_time = property(operator.itemgetter(2))
    max_call_time = property(operator.itemgetter(3))
    slow_sql_node = property(operator.itemgetter(4))

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self[1] += other[1]
        self[2] = self[0] and min(self[2], other[2]) or other[2]
        self[3] = max(self[3], other[3])

        if self[3] == other[3]:
            self[4] = other[4]

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += other[0]

    def merge_slow_sql_node(self, node):
        """Merge data from a slow sql node object."""

        duration = node.duration

        self[1] += duration
        self[2] = self[0] and min(self[2], duration) or duration
        self[3] = max(self[3], duration)

        if self[3] == duration:
            self[4] = node

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self[0] += 1


class SampledDataSet(object):

    def __init__(self, capacity=100):
        self.samples = []
        self.capacity = capacity
        self.num_seen = 0

    @property
    def num_samples(self):
        return len(self.samples)

    @property
    def sampling_info(self):
        return {
            'reservoir_size': self.capacity,
            'events_seen': self.num_seen
        }

    def reset(self):
        self.samples = []
        self.num_seen = 0

    def add(self, sample):
        if self.num_samples < self.capacity:
            self.samples.append(sample)
        else:
            index = random.randint(0, self.num_seen)
            if index < self.capacity:
                self.samples[index] = sample
        self.num_seen += 1

    def merge(self, other_data_set):
        for item in other_data_set.samples:
            self.add(item)

        # Make sure num_seen includes total items seen from merged set

        self.num_seen += other_data_set.num_seen - other_data_set.num_samples


class StatsEngine(object):

    """The stats engine object holds the accumulated transactions metrics,
    details of errors and slow transactions. There should be one instance
    of the stats engine per application. This will be cleared upon each
    successful harvest of data whereby it is sent to the core application.
    No data will however be accumulated while there is no associated
    settings object indicating that application has been successfully
    activated and server side settings received.

    All of the accumulated apdex, time and value metrics are mapped to from
    the same stats table. The key is comprised of a tuple (name, scope).
    For an apdex metric the scope is None. Time metrics should always have
    a string as the scope and it can be either empty or not. Value metrics
    technically overlap in same namespace as time metrics as the scope is
    always an empty string. There are however no checks against adding a
    value metric which clashes with an existing time metric or vice versa.
    If that is done then the results will simply be wrong. The name chose
    for a time or value metric should thus be chosen wisely so as not to
    clash.

    Note that there is no locking performed within the stats engine itself.
    It is assumed the holder and user of the instance performs adequate
    external locking to ensure that multiple threads do not try and update
    it at the same time.

    """

    def __init__(self):
        self.__settings = None
        self.__stats_table = {}
        self.__transaction_events = SampledDataSet()
        self.__error_events = SampledDataSet()
        self.__custom_events = SampledDataSet()
        self.__sql_stats_table = {}
        self.__slow_transaction = None
        self.__slow_transaction_map = {}
        self.__slow_transaction_old_duration = None
        self.__slow_transaction_dry_harvests = 0
        self.__transaction_errors = []
        self.__metric_ids = {}
        self.__synthetics_events = []
        self.__synthetics_transactions = []
        self.__xray_transactions = []
        self.xray_sessions = {}

    @property
    def settings(self):
        return self.__settings

    @property
    def stats_table(self):
        return self.__stats_table

    @property
    def metric_ids(self):
        """Returns a reference to the dictionary containing the mappings
        from metric (name, scope) to the integer identifier supplied
        back from the core application. These integer identifiers are
        used when sending data to the core application to cut down on
        the size of data being sent.

        """

        return self.__metric_ids

    @property
    def transaction_events(self):
        return self.__transaction_events

    @property
    def custom_events(self):
        return self.__custom_events

    @property
    def synthetics_events(self):
        return self.__synthetics_events

    @property
    def synthetics_transactions(self):
        return self.__synthetics_transactions

    @property
    def error_events(self):
        return self.__error_events

    def error_events_sampling_info(self):
        sampling_info = {
                'reservoir_size': self.error_events.capacity,
                'events_seen': self.error_events.num_seen
        }
        return sampling_info

    def update_metric_ids(self, metric_ids):
        """Updates the dictionary containing the mappings from metric
        (name, scope) to the integer identifier supplied back from the
        core application. The input should be an iterable returning a
        list of pairs where first is a dictionary with name and scope
        keys with corresponding values. The second should be the integer
        identifier. The dictionary is converted to a (name, scope) tuple
        for use as key into the internal dictionary containing the
        mappings.

        """

        for key, value in metric_ids:
            key = (key['name'], key['scope'])
            self.__metric_ids[key] = value

    def metrics_count(self):
        """Returns a count of the number of unique metrics currently
        recorded for apdex, time and value metrics.

        """

        return len(self.__stats_table)

    def record_apdex_metric(self, metric):
        """Record a single apdex metric, merging the data with any data
        from prior apdex metrics with the same name.

        """

        if not self.__settings:
            return

        # Note that because we are using a scope here of an empty string
        # we can potentially clash with an unscoped metric. Using None,
        # although it may help to keep them separate in the agent will
        # not make a difference to the data collector which treats None
        # as an empty string anyway.

        key = (metric.name, '')
        stats = self.__stats_table.get(key)
        if stats is None:
            stats = ApdexStats(apdex_t=metric.apdex_t)
            self.__stats_table[key] = stats
        stats.merge_apdex_metric(metric)

        return key

    def record_apdex_metrics(self, metrics):
        """Record the apdex metrics supplied by the iterable for a
        single transaction, merging the data with any data from prior
        apdex metrics with the same name.

        """

        if not self.__settings:
            return

        for metric in metrics:
            self.record_apdex_metric(metric)

    def record_time_metric(self, metric):
        """Record a single time metric, merging the data with any data
        from prior time metrics with the same name and scope.

        """

        if not self.__settings:
            return

        # Scope is forced to be empty string if None as
        # scope of None is reserved for apdex metrics.

        key = (metric.name, metric.scope or '')
        stats = self.__stats_table.get(key)
        if stats is None:
            stats = TimeStats(call_count=1,
                    total_call_time=metric.duration,
                    total_exclusive_call_time=metric.exclusive,
                    min_call_time=metric.duration,
                    max_call_time=metric.duration,
                    sum_of_squares=metric.duration ** 2)
            self.__stats_table[key] = stats
        else:
            stats.merge_time_metric(metric)

        return key

    def record_time_metrics(self, metrics):
        """Record the time metrics supplied by the iterable for a single
        transaction, merging the data with any data from prior time
        metrics with the same name and scope.

        """

        if not self.__settings:
            return

        for metric in metrics:
            self.record_time_metric(metric)

    def record_exception(self, exc=None, value=None, tb=None, params={},
            ignore_errors=[]):

        settings = self.__settings

        if not settings:
            return

        error_collector = settings.error_collector

        if not error_collector.enabled:
            return

        if not settings.collect_errors and not settings.collect_error_events:
            return

        # If no exception details provided, use current exception.

        if exc is None and value is None and tb is None:
            exc, value, tb = sys.exc_info()

        # Has to be an error to be logged.

        if exc is None or value is None or tb is None:
            return

        # Where ignore_errors is a callable it should return a
        # tri-state variable with the following behavior.
        #
        #   True - Ignore the error.
        #   False- Record the error.
        #   None - Use the default ignore rules.

        should_ignore = None

        if callable(ignore_errors):
            should_ignore = ignore_errors(exc, value, tb)
            if should_ignore:
                return

        module = value.__class__.__module__
        name = value.__class__.__name__

        if should_ignore is None:
            # We need to check for module.name and module:name.
            # Originally we used module.class but that was
            # inconsistent with everything else which used
            # module:name. So changed to use ':' as separator, but
            # for backward compatibility need to support '.' as
            # separator for time being. Check that with the ':'
            # last as we will use that name as the exception type.

            if module:
                fullname = '%s.%s' % (module, name)
            else:
                fullname = name

            if not callable(ignore_errors) and fullname in ignore_errors:
                return

            if fullname in error_collector.ignore_errors:
                return

            if module:
                fullname = '%s:%s' % (module, name)
            else:
                fullname = name

            if not callable(ignore_errors) and fullname in ignore_errors:
                return

            if fullname in error_collector.ignore_errors:
                return

        else:
            if module:
                fullname = '%s:%s' % (module, name)
            else:
                fullname = name

        # Only add params if High Security Mode is off.

        if settings.high_security:
            if params:
                _logger.debug('Cannot add custom parameters in '
                        'High Security Mode.')
            attributes = []
        else:
            custom_params = {}

            try:
                for k, v in params.items():
                    name, val = process_user_attribute(k, v)
                    if name:
                        custom_params[name] = val
            except Exception:
                _logger.debug('Parameters failed to validate for unknown '
                        'reason. Dropping parameters for error: %r. Check '
                        'traceback for clues.', fullname, exc_info=True)
                custom_params = {}

            attributes = create_user_attributes(custom_params,
                    settings.attribute_filter)

        # Check to see if we need to strip the message before recording it.

        if (settings.strip_exception_messages.enabled and
                fullname not in settings.strip_exception_messages.whitelist):
            message = STRIP_EXCEPTION_MESSAGE
        else:
            try:
                # Favor unicode in exception messages.

                message = six.text_type(value)

            except Exception:
                try:

                    # If exception cannot be represented in unicode, this means
                    # that it is a byte string encoded with an encoding
                    # that is not compatible with the default system encoding.
                    # So, just pass this byte string along.

                    message = str(value)

                except Exception:
                    message = '<unprintable %s object>' % type(value).__name__

        # Record the exception details.

        params = {}

        params["stack_trace"] = exception_stack(tb)

        # filter custom error specific params using attribute filter (user)
        params['userAttributes'] = {}
        for attr in attributes:
            if attr.destinations & DST_ERROR_COLLECTOR:
                params['userAttributes'][attr.name] = attr.value

        error_details = TracedError(
                start_time=time.time(),
                path='Exception',
                message=message,
                type=fullname,
                parameters=params)

        # Save this error as a trace and an event.

        if error_collector.capture_events and settings.collect_error_events:
            event = self._error_event(error_details)
            self.__error_events.add(event)

        if settings.collect_errors and (len(self.__transaction_errors) <
                settings.agent_limits.errors_per_harvest):
            self.__transaction_errors.append(error_details)

        # Regardless of whether we record the trace or the event we still
        # want to increment the metric Errors/all
        self.record_time_metric(TimeMetric(name='Errors/all', scope='',
                duration=0.0, exclusive=None))

    def _error_event(self, error):

        # This method is for recording error events outside of transactions,
        # don't let the poorly named 'type' attribute fool you.

        intrinsics = {
                'type': 'TransactionError',
                'error.class': error.type,
                'error.message': error.message,
                'timestamp': error.start_time,
                'transactionName': None,
        }

        # Leave agent attributes field blank since not a transaction

        error_event = [intrinsics, error.parameters['userAttributes'], {}]

        return error_event

    def record_custom_event(self, event):

        settings = self.__settings

        if not settings:
            return

        if (settings.collect_custom_events and
                settings.custom_insights_events.enabled):
            self.__custom_events.add(event)

    def record_custom_metric(self, name, value):
        """Record a single value metric, merging the data with any data
        from prior value metrics with the same name.

        """
        key = (name, '')

        if isinstance(value, dict):
            if len(value) == 1 and 'count' in value:
                new_stats = CountStats(call_count=value['count'])
            else:
                new_stats = TimeStats(*c2t(**value))
        else:
            new_stats = TimeStats(1, value, value, value, value, value**2)

        stats = self.__stats_table.get(key)
        if stats is None:
            self.__stats_table[key] = new_stats
        else:
            stats.merge_stats(new_stats)

        return key

    def record_custom_metrics(self, metrics):
        """Record the value metrics supplied by the iterable, merging
        the data with any data from prior value metrics with the same
        name.

        """

        if not self.__settings:
            return

        for name, value in metrics:
            self.record_custom_metric(name, value)

    def record_slow_sql_node(self, node):
        """Record a single sql metric, merging the data with any data
        from prior sql metrics for the same sql key.

        """

        if not self.__settings:
            return

        key = node.identifier
        stats = self.__sql_stats_table.get(key)
        if stats is None:
            # Only record slow SQL if not already over the limit on
            # how many can be collected in the harvest period.

            settings = self.__settings
            maximum = settings.agent_limits.slow_sql_data
            if len(self.__sql_stats_table) < maximum:
                stats = SlowSqlStats()
                self.__sql_stats_table[key] = stats

        if stats:
            stats.merge_slow_sql_node(node)

        return key

    def _update_xray_transaction(self, transaction):
        """Check if transaction is an x-ray transaction and save it to the
        __xray_transactions
        """

        settings = self.__settings

        # Nothing to do if we have reached the max limit of x-ray transactions
        # to send per harvest.

        maximum = settings.agent_limits.xray_transactions
        if len(self.__xray_transactions) >= maximum:
            return

        # If current transaction qualifies as an xray_transaction, set the
        # xray_id on the transaction object and save it in the
        # xray_transactions list.

        xray_session = self.xray_sessions.get(transaction.path)
        if xray_session:
            transaction.xray_id = xray_session.xray_id
            self.__xray_transactions.append(transaction)

    def _update_slow_transaction(self, transaction):
        """Check if transaction is the slowest transaction and update
        accordingly.
        """

        slowest = 0
        name = transaction.path

        if self.__slow_transaction:
            slowest = self.__slow_transaction.duration
        if name in self.__slow_transaction_map:
            slowest = max(self.__slow_transaction_map[name], slowest)

        if transaction.duration > slowest:
            # We are going to replace the prior slow transaction.
            # We need to be a bit tricky here. If we are overriding
            # an existing slow transaction for a different name,
            # then we need to restore in the transaction map what
            # the previous slowest duration was for that, or remove
            # it if there wasn't one. This is so we do not incorrectly
            # suppress it given that it was never actually reported
            # as the slowest transaction.

            if self.__slow_transaction:
                if self.__slow_transaction.path != name:
                    if self.__slow_transaction_old_duration:
                        self.__slow_transaction_map[
                                self.__slow_transaction.path] = (
                                self.__slow_transaction_old_duration)
                    else:
                        del self.__slow_transaction_map[
                                self.__slow_transaction.path]

            if name in self.__slow_transaction_map:
                self.__slow_transaction_old_duration = (
                        self.__slow_transaction_map[name])
            else:
                self.__slow_transaction_old_duration = None

            self.__slow_transaction = transaction
            self.__slow_transaction_map[name] = transaction.duration

    def _update_synthetics_transaction(self, transaction):
        """Check if transaction is a synthetics trace and save it to
        __synthetics_transactions.
        """

        settings = self.__settings

        if not transaction.synthetics_resource_id:
            return

        maximum = settings.agent_limits.synthetics_transactions
        if len(self.__synthetics_transactions) < maximum:
            self.__synthetics_transactions.append(transaction)

    def record_transaction(self, transaction):
        """Record any apdex and time metrics for the transaction as
        well as any errors which occurred for the transaction. If the
        transaction qualifies to become the slow transaction remember
        it for later.

        """

        if not self.__settings:
            return

        settings = self.__settings

        # Record the apdex, value and time metrics generated from the
        # transaction. Whether time metrics are reported as distinct
        # metrics or into a rollup is in part controlled via settings
        # for minimum number of unique metrics to be reported and thence
        # whether over a time threshold calculated as percentage of
        # overall request time, up to a maximum number of unique
        # metrics. This is intended to limit how many metrics are
        # reported for each transaction and try and cut down on an
        # explosion of unique metric names. The limits and thresholds
        # are applied after the metrics are reverse sorted based on
        # exclusive times for each metric. This ensures that the metrics
        # with greatest exclusive time are retained over those with
        # lesser time. Such metrics get reported into the performance
        # breakdown tab for specific web transactions.

        self.record_apdex_metrics(transaction.apdex_metrics(self))

        self.merge_custom_metrics(transaction.custom_metrics.metrics())

        self.record_time_metrics(transaction.time_metrics(self))

        # Capture any errors if error collection is enabled.
        # Only retain maximum number allowed per harvest.

        error_collector = settings.error_collector

        if (error_collector.enabled and settings.collect_errors and
                len(self.__transaction_errors) <
                settings.agent_limits.errors_per_harvest):
            self.__transaction_errors.extend(transaction.error_details())

            self.__transaction_errors = self.__transaction_errors[:
                    settings.agent_limits.errors_per_harvest]

        if (error_collector.capture_events and
                error_collector.enabled and
                settings.collect_error_events):
            events = transaction.error_events(self.__stats_table)
            for event in events:
                self.__error_events.add(event)

        # Capture any sql traces if transaction tracer enabled.

        if settings.slow_sql.enabled and settings.collect_traces:
            for node in transaction.slow_sql_nodes(self):
                self.record_slow_sql_node(node)

        # Remember as slowest transaction if transaction tracer
        # is enabled, it is over the threshold and slower than
        # any existing transaction seen for this period and in
        # the historical snapshot of slow transactions, plus
        # recording of transaction trace for this transaction
        # has not been suppressed.

        transaction_tracer = settings.transaction_tracer

        if (not transaction.suppress_transaction_trace and
                transaction_tracer.enabled and settings.collect_traces):

            # Transactions saved for x-ray session and Synthetics transactions
            # do not depend on the transaction threshold.

            self._update_xray_transaction(transaction)
            self._update_synthetics_transaction(transaction)

            threshold = transaction_tracer.transaction_threshold

            if threshold is None:
                threshold = transaction.apdex_t * 4

            if transaction.duration >= threshold:
                self._update_slow_transaction(transaction)

        # Create the transaction event and add it to the
        # appropriate "bucket." Synthetic requests are saved in one,
        # while transactions from regular requests are saved in another.

        if transaction.synthetics_resource_id:
            if (len(self.__synthetics_events) <
                    settings.agent_limits.synthetics_events):

                event = transaction.transaction_event(self.__stats_table)
                self.__synthetics_events.append(event)

        elif (settings.collect_analytics_events and
                settings.transaction_events.enabled):

            event = transaction.transaction_event(self.__stats_table)
            self.__transaction_events.add(event)

        # Merge in custom events

        if (settings.collect_custom_events and
                settings.custom_insights_events.enabled):
            self.custom_events.merge(transaction.custom_events)

    def metric_data(self, normalizer=None):
        """Returns a list containing the low level metric data for
        sending to the core application pertaining to the reporting
        period. This consists of tuple pairs where first is dictionary
        with name and scope keys with corresponding values, or integer
        identifier if metric had an entry in dictionary mapping metric
        (name, scope) as supplied from core application. The second is
        the list of accumulated metric data, the list always being of
        length 6.

        """

        if not self.__settings:
            return []

        result = []
        normalized_stats = {}

        # Metric Renaming and Re-Aggregation. After applying the metric
        # renaming rules, the metrics are re-aggregated to collapse the
        # metrics with same names after the renaming.

        if self.__settings.debug.log_raw_metric_data:
            _logger.info('Raw metric data for harvest of %r is %r.',
                    self.__settings.app_name,
                    list(six.iteritems(self.__stats_table)))

        if normalizer is not None:
            for key, value in six.iteritems(self.__stats_table):
                key = (normalizer(key[0])[0], key[1])
                stats = normalized_stats.get(key)
                if stats is None:
                    normalized_stats[key] = copy.copy(value)
                else:
                    stats.merge_stats(value)
        else:
            normalized_stats = self.__stats_table

        if self.__settings.debug.log_normalized_metric_data:
            _logger.info('Normalized metric data for harvest of %r is %r.',
                    self.__settings.app_name,
                    list(six.iteritems(normalized_stats)))

        for key, value in six.iteritems(normalized_stats):
            if key not in self.__metric_ids:
                key = dict(name=key[0], scope=key[1])
            else:
                key = self.__metric_ids[key]
            result.append((key, value))

        return result

    def metric_data_count(self):
        """Returns a count of the number of unique metrics.

        """

        if not self.__settings:
            return 0

        return len(self.__stats_table)

    def error_data(self):
        """Returns a to a list containing any errors collected during
        the reporting period.

        """

        if not self.__settings:
            return []

        return self.__transaction_errors

    def slow_sql_data(self, connections):

        _logger.debug('Generating slow SQL data.')

        if not self.__settings:
            return []

        if not self.__sql_stats_table:
            return []

        if not self.__settings.slow_sql.enabled:
            return []

        maximum = self.__settings.agent_limits.slow_sql_data

        slow_sql_nodes = sorted(six.itervalues(self.__sql_stats_table),
                key=lambda x: x.max_call_time)[-maximum:]

        result = []

        for stats_node in slow_sql_nodes:

            params = {}

            slow_sql_node = stats_node.slow_sql_node

            if slow_sql_node.stack_trace:
                params['backtrace'] = slow_sql_node.stack_trace

            explain_plan_data = explain_plan(connections,
                    slow_sql_node.statement,
                    slow_sql_node.connect_params,
                    slow_sql_node.cursor_params,
                    slow_sql_node.sql_parameters,
                    slow_sql_node.execute_params,
                    slow_sql_node.sql_format)

            if explain_plan_data:
                params['explain_plan'] = explain_plan_data

            # Only send datastore instance params if not empty.

            if slow_sql_node.host:
                params['host'] = slow_sql_node.host

            if slow_sql_node.port_path_or_id:
                params['port_path_or_id'] = slow_sql_node.port_path_or_id

            if slow_sql_node.database_name:
                params['database_name'] = slow_sql_node.database_name

            json_data = json_encode(params)

            level = self.__settings.agent_limits.data_compression_level
            level = level or zlib.Z_DEFAULT_COMPRESSION

            params_data = base64.standard_b64encode(
                    zlib.compress(six.b(json_data), level))

            if six.PY3:
                params_data = params_data.decode('Latin-1')

            # Limit the length of any SQL that is reported back.

            limit = self.__settings.agent_limits.sql_query_length_maximum

            sql = slow_sql_node.formatted[:limit]

            data = [slow_sql_node.path,
                    slow_sql_node.request_uri,
                    slow_sql_node.identifier,
                    sql,
                    slow_sql_node.metric,
                    stats_node.call_count,
                    stats_node.total_call_time * 1000,
                    stats_node.min_call_time * 1000,
                    stats_node.max_call_time * 1000,
                    params_data]

            result.append(data)

        return result

    def transaction_trace_data(self, connections):
        """Returns a list of slow transaction data collected
        during the reporting period.

        """

        _logger.debug('Generating transaction trace data.')

        if not self.__settings:
            return []

        # Create a set 'traces' that is a union of slow transaction,
        # xray_transactions, and Synthetics transactions.
        # This ensures we don't send duplicates of a transaction.

        traces = set()
        if self.__slow_transaction:
            traces.add(self.__slow_transaction)
        traces.update(self.__xray_transactions)
        traces.update(self.__synthetics_transactions)

        # Return an empty list if no transactions were captured.

        if not traces:
            return []

        # We want to limit the number of explain plans we do across
        # these. So work out what were the slowest and tag them.
        # Later the explain plan will only be run on those which are
        # tagged.

        agent_limits = self.__settings.agent_limits
        explain_plan_limit = agent_limits.sql_explain_plans_per_harvest
        maximum_nodes = agent_limits.transaction_traces_nodes

        database_nodes = []

        if explain_plan_limit != 0:
            for trace in traces:
                for node in trace.slow_sql:
                    # Make sure we clear any flag for explain plans on
                    # the nodes in case a transaction trace was merged
                    # in from previous harvest period.

                    node.generate_explain_plan = False

                    # Node should be excluded if not for an operation
                    # that we can't do an explain plan on. Also should
                    # not be one which would not be included in the
                    # transaction trace because limit was reached.

                    if (node.node_count < maximum_nodes and
                            node.connect_params and node.statement.operation in
                            node.statement.database.explain_stmts):
                        database_nodes.append(node)

            database_nodes = sorted(database_nodes,
                    key=lambda x: x.duration)[-explain_plan_limit:]

            for node in database_nodes:
                node.generate_explain_plan = True

        else:
            for trace in traces:
                for node in trace.slow_sql:
                    node.generate_explain_plan = True
                    database_nodes.append(node)

        # Now generate the transaction traces. We need to cap the
        # number of nodes capture to the specified limit.

        trace_data = []

        for trace in traces:
            transaction_trace = trace.transaction_trace(
                    self, maximum_nodes, connections)

            data = [transaction_trace,
                    list(trace.string_table.values())]

            if self.__settings.debug.log_transaction_trace_payload:
                _logger.debug('Encoding slow transaction data where '
                              'payload=%r.', data)

            json_data = json_encode(data)

            level = self.__settings.agent_limits.data_compression_level
            level = level or zlib.Z_DEFAULT_COMPRESSION

            zlib_data = zlib.compress(six.b(json_data), level)

            pack_data = base64.standard_b64encode(zlib_data)

            if six.PY3:
                pack_data = pack_data.decode('Latin-1')

            root = transaction_trace.root
            xray_id = getattr(trace, 'xray_id', None)

            if (xray_id or trace.record_tt):
                force_persist = True
            else:
                force_persist = False

            trace_data.append([transaction_trace.start_time,
                    root.end_time - root.start_time,
                    trace.path,
                    trace.request_uri,
                    pack_data,
                    trace.guid,
                    None,
                    force_persist,
                    xray_id,
                    trace.synthetics_resource_id, ])

        return trace_data

    def slow_transaction_data(self):
        """Returns a list containing any slow transaction data collected
        during the reporting period.

        NOTE Currently only the slowest transaction for the reporting
        period is retained.

        """

        # XXX This method no longer appears to be used. Being replaced
        # by the transaction_trace_data() method.

        if not self.__settings:
            return []

        if not self.__slow_transaction:
            return []

        maximum = self.__settings.agent_limits.transaction_traces_nodes

        transaction_trace = self.__slow_transaction.transaction_trace(
                self, maximum)

        data = [transaction_trace,
                list(self.__slow_transaction.string_table.values())]

        if self.__settings.debug.log_transaction_trace_payload:
            _logger.debug('Encoding slow transaction data where '
                    'payload=%r.', data)

        json_data = json_encode(data)

        level = self.__settings.agent_limits.data_compression_level
        level = level or zlib.Z_DEFAULT_COMPRESSION

        zlib_data = zlib.compress(six.b(json_data), level)

        pack_data = base64.standard_b64encode(zlib_data)

        if six.PY3:
            pack_data = pack_data.decode('Latin-1')

        root = transaction_trace.root

        trace_data = [[root.start_time,
                root.end_time - root.start_time,
                self.__slow_transaction.path,
                self.__slow_transaction.request_uri,
                pack_data]]

        return trace_data

    def reset_stats(self, settings):
        """Resets the accumulated statistics back to initial state and
        associates the application settings object with the stats
        engine. This should be called when application is first
        activated and combined application settings incorporating server
        side settings are available. Would also be called on any forced
        restart of agent or a reconnection due to loss of connection.

        """

        self.__settings = settings
        self.__stats_table = {}
        self.__sql_stats_table = {}
        self.__slow_transaction = None
        self.__slow_transaction_map = {}
        self.__slow_transaction_old_duration = None
        self.__transaction_errors = []
        self.__metric_ids = {}
        self.__synthetics_events = []
        self.__synthetics_transactions = []
        self.__xray_transactions = []
        self.xray_sessions = {}

        self.reset_transaction_events()
        self.reset_error_events()
        self.reset_custom_events()

    def reset_metric_stats(self):
        """Resets the accumulated statistics back to initial state for
        metric data.

        """

        self.__stats_table = {}

    def reset_transaction_events(self):
        """Resets the accumulated statistics back to initial state for
        sample analytics data.

        """

        if self.__settings is not None:
            self.__transaction_events = SampledDataSet(
                    self.__settings.transaction_events.max_samples_stored)
        else:
            self.__transaction_events = SampledDataSet()

    def reset_error_events(self):
        if self.__settings is not None:
            self.__error_events = SampledDataSet(
                    self.__settings.error_collector.max_event_samples_stored)
        else:
            self.__error_events = SampledDataSet()

    def reset_custom_events(self):
        if self.__settings is not None:
            self.__custom_events = SampledDataSet(
                    self.__settings.custom_insights_events.max_samples_stored)
        else:
            self.__custom_events = SampledDataSet()

    def reset_synthetics_events(self):
        """Resets the accumulated statistics back to initial state for
        Synthetics events data.

        """
        self.__synthetics_events = []

    def harvest_snapshot(self):
        """Creates a snapshot of the accumulated statistics, error
        details and slow transaction and returns it. This is a shallow
        copy, only copying the top level objects. The originals are then
        reset back to being empty, with the exception of the dictionary
        mapping metric (name, scope) to the integer identifiers received
        from the core application. The latter is retained as should
        carry forward to subsequent runs. This method would be called
        to snapshot the data when doing the harvest.

        """

        stats = copy.copy(self)

        # The slow transaction map is retained but we need to
        # perform some housework on each harvest snapshot. What
        # we do is add the slow transaction to the map of
        # transactions and if we reach the threshold for maximum
        # number we clear the table. Also clear the table if
        # have number of harvests where no slow transaction was
        # collected.

        if self.__settings is None:
            self.__slow_transaction_dry_harvests = 0
            self.__slow_transaction_map = {}
            self.__slow_transaction_old_duration = None

        elif self.__slow_transaction is None:
            self.__slow_transaction_dry_harvests += 1
            agent_limits = self.__settings.agent_limits
            dry_harvests = agent_limits.slow_transaction_dry_harvests
            if self.__slow_transaction_dry_harvests >= dry_harvests:
                self.__slow_transaction_dry_harvests = 0
                self.__slow_transaction_map = {}
                self.__slow_transaction_old_duration = None

        else:
            self.__slow_transaction_dry_harvests = 0
            name = self.__slow_transaction.path
            duration = self.__slow_transaction.duration
            self.__slow_transaction_map[name] = duration

            top_n = self.__settings.transaction_tracer.top_n
            if len(self.__slow_transaction_map) >= top_n:
                self.__slow_transaction_map = {}
                self.__slow_transaction_old_duration = None

        # We also retain the table of metric IDs. This should be
        # okay for continuing connection. If connection is lost
        # then reset_engine() above would be called and it would
        # be all thrown away so no chance of following through
        # with incorrect mappings. Everything else is reset to
        # initial values.

        self.__stats_table = {}
        self.__sql_stats_table = {}
        self.__slow_transaction = None
        self.__transaction_errors = []
        self.__xray_transactions = []
        self.__synthetics_events = []
        self.__synthetics_transactions = []

        self.reset_transaction_events()
        self.reset_error_events()
        self.reset_custom_events()

        return stats

    def create_workarea(self):
        """Creates and returns a new empty stats engine object. This would
        be used to distill stats from a single web transaction before then
        merging it back into the parent under a thread lock.

        """

        stats = StatsEngine()

        stats.__settings = self.__settings
        stats.xray_sessions = self.xray_sessions

        return stats

    def merge(self, snapshot):
        """Merges data from a single transaction. Snapshot is an instance of
        StatsEngine that contains stats for the single transaction.
        """

        if not self.__settings:
            return

        self.merge_metric_stats(snapshot)
        self._merge_transaction_events(snapshot)
        self._merge_synthetics_events(snapshot)
        self._merge_error_events(snapshot)
        self._merge_error_traces(snapshot)
        self._merge_custom_events(snapshot)
        self._merge_sql(snapshot)
        self._merge_traces(snapshot)

    def rollback(self, snapshot):
        """Performs a "rollback" merge after a failed harvest. Snapshot is a
        copy of the main StatsEngine data that we attempted to harvest, but
        failed. Not all types of data get merged during a rollback.
        """

        if not self.__settings:
            return

        _logger.debug('Performing rollback of data into '
                'subsequent harvest period. Metric data and transaction events'
                'will be preserved and rolled into next harvest')

        self.merge_metric_stats(snapshot)
        self._merge_transaction_events(snapshot, rollback=True)
        self._merge_synthetics_events(snapshot, rollback=True)
        self._merge_error_events(snapshot)
        self._merge_custom_events(snapshot, rollback=True)

    def merge_metric_stats(self, snapshot):
        """Merges metric data from a snapshot. This is used both when merging
        data from a single transaction into the main stats engine, and for
        performing a rollback merge. In either case, the merge is done the
        exact same way.
        """

        if not self.__settings:
            return

        for key, other in six.iteritems(snapshot.__stats_table):
            stats = self.__stats_table.get(key)
            if not stats:
                self.__stats_table[key] = other
            else:
                stats.merge_stats(other)

    def _merge_transaction_events(self, snapshot, rollback=False):

        # Merge in transaction events. In the normal case snapshot is a
        # StatsEngine from a single transaction, and should only have one
        # event. Just to avoid issues, if there is more than one, don't merge.

        # If this is a rollback, snapshot is a copy of a previous main
        # StatsEngine, and self is still the current main StatsEngine. Then
        # we are merging multiple events, but still using the reservoir
        # sampling that gives equal probability for keeping all events

        if rollback:
            for sample in snapshot.__transaction_events.samples:
                self.__transaction_events.add(sample)

        else:
            if snapshot.__transaction_events.num_samples == 1:
                self.__transaction_events.add(
                        snapshot.__transaction_events.samples[0])

    def _merge_synthetics_events(self, snapshot, rollback=False):

        # Merge Synthetic analytic events, appending to the list
        # that contains events from previous transactions. In the normal
        # case snapshot is a StatsEngine from a single transaction, and should
        # only have one event. Cap this list at a maximum, so that newer events
        # over the limit will be thrown out.

        # If this is a rollback, snapshot is a copy of a previous main
        # StatsEngine, and self is still the current main StatsEngine,
        # Thus, the events already existing in this object will be newer than
        # those in snapshot, and we favor the newer events.

        if rollback:
            self.__synthetics_events.extend(snapshot.__synthetics_events)
        else:
            if len(snapshot.__synthetics_events) == 1:
                self.__synthetics_events.append(
                    snapshot.__synthetics_events[0])

        maximum = self.__settings.agent_limits.synthetics_events
        self.__synthetics_events = self.__synthetics_events[:maximum]

    def _merge_error_events(self, snapshot):

        # Merge in error events. Since we are using reservoir sampling that
        # gives equal probability to keeping each event, merge is the same as
        # rollback. There may be multiple error events per transaction.

        self.__error_events.merge(snapshot.error_events)

    def _merge_custom_events(self, snapshot, rollback=False):

        self.__custom_events.merge(snapshot.custom_events)

    def _merge_error_traces(self, snapshot):

        # Append snapshot error details at end to maintain time
        # based order and then trim at maximum to be kept. snapshot will
        # always have newer data.

        maximum = self.__settings.agent_limits.errors_per_harvest
        self.__transaction_errors.extend(snapshot.__transaction_errors)
        self.__transaction_errors = self.__transaction_errors[:maximum]

    def _merge_sql(self, snapshot):

        # Add sql traces to the set of existing entries. If over
        # the limit of how many to collect, only merge in if already
        # seen the specific SQL.

        for key, slow_sql_stats in six.iteritems(snapshot.__sql_stats_table):
            stats = self.__sql_stats_table.get(key)
            if not stats:
                maximum = self.__settings.agent_limits.slow_sql_data
                if len(self.__sql_stats_table) < maximum:
                    self.__sql_stats_table[key] = copy.copy(slow_sql_stats)
            else:
                stats.merge_stats(slow_sql_stats)

    def _merge_traces(self, snapshot):

        # Limit number of x-ray traces to the limit.
        # Spill over traces after the limit should have no x-ray ids. This
        # qualifies the trace to be considered for slow transaction.

        maximum = self.__settings.agent_limits.xray_transactions
        self.__xray_transactions.extend(snapshot.__xray_transactions)
        for txn in self.__xray_transactions[maximum:]:
            txn.xray_id = None
        self.__xray_transactions = self.__xray_transactions[:maximum]

        # Limit number of Synthetics transactions

        maximum = self.__settings.agent_limits.synthetics_transactions
        self.__synthetics_transactions.extend(
                snapshot.__synthetics_transactions)
        synthetics_slice = self.__synthetics_transactions[:maximum]
        self.__synthetics_transactions = synthetics_slice

        transaction = snapshot.__slow_transaction

        # If the transaction has an xray_id then it does not qualify to
        # be considered for slow transaction.  This is because in the Core
        # app, there is logic to NOT show TTs with x-ray ids in the
        # WebTransactions tab. If a TT has xray_id it is only shown under
        # the x-ray page.

        xray_id = getattr(transaction, 'xray_id', None)
        if transaction and xray_id is None:

            # Restore original slow transaction if slower than any newer slow
            # transaction.

            self._update_slow_transaction(transaction)

    def merge_custom_metrics(self, metrics):
        """Merges in a set of custom metrics. The metrics should be
        provide as an iterable where each item is a tuple of the metric
        name and the accumulated stats for the metric.

        """

        if not self.__settings:
            return

        for name, other in metrics:
            key = (name, '')
            stats = self.__stats_table.get(key)
            if not stats:
                self.__stats_table[key] = other
            else:
                stats.merge_stats(other)
