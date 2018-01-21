import os
import sys
import time
import threading
import traceback
import logging
import warnings
import itertools
import random

from collections import deque

import newrelic.packages.six as six

import newrelic.core.transaction_node
import newrelic.core.database_node
import newrelic.core.error_node

from newrelic.core.stats_engine import CustomMetrics, SampledDataSet
from newrelic.core.transaction_cache import transaction_cache
from newrelic.core.thread_utilization import utilization_tracker

from newrelic.core.attribute import (create_attributes,
        create_agent_attributes, create_user_attributes,
        process_user_attribute, MAX_NUM_USER_ATTRIBUTES)
from newrelic.core.attribute_filter import (DST_NONE, DST_ERROR_COLLECTOR,
        DST_TRANSACTION_TRACER)
from newrelic.core.config import DEFAULT_RESERVOIR_SIZE
from newrelic.core.custom_event import create_custom_event
from newrelic.core.stack_trace import exception_stack
from newrelic.common.encoding_utils import (generate_path_hash, obfuscate,
        deobfuscate, json_encode, json_decode, base64_decode,
        convert_to_cat_metadata_value)

from newrelic.api.settings import STRIP_EXCEPTION_MESSAGE
from newrelic.api.time_trace import TimeTrace

_logger = logging.getLogger(__name__)


class Sentinel(TimeTrace):
    def __init__(self):
        super(Sentinel, self).__init__(None)


class Transaction(object):

    STATE_PENDING = 0
    STATE_RUNNING = 1
    STATE_STOPPED = 2

    def __init__(self, application, enabled=None):

        self._application = application

        self.thread_id = transaction_cache().current_thread_id()

        self._transaction_id = id(self)
        self._transaction_lock = threading.Lock()

        self._dead = False

        self._state = self.STATE_PENDING
        self._settings = None

        self._priority = 0
        self._group = None
        self._name = None

        self._frameworks = set()

        self._frozen_path = None

        self.current_node = None

        self._request_uri = None
        self._port = None

        self.queue_start = 0.0

        self.start_time = 0.0
        self.end_time = 0.0
        self.last_byte_time = 0.0

        self.total_time = None

        self.stopped = False

        self._trace_node_count = 0

        self._errors = []
        self._slow_sql = []
        self._custom_events = SampledDataSet(capacity=DEFAULT_RESERVOIR_SIZE)

        self._stack_trace_count = 0
        self._explain_plan_count = 0

        self._string_cache = {}

        self._custom_params = {}
        self._request_params = {}

        self._utilization_tracker = None

        self._thread_utilization_start = None
        self._thread_utilization_end = None
        self._thread_utilization_value = None

        self._cpu_user_time_start = None
        self._cpu_user_time_end = None
        self._cpu_user_time_value = 0.0

        self._read_length = None

        self._read_start = None
        self._read_end = None

        self._sent_start = None
        self._sent_end = None

        self._bytes_read = 0
        self._bytes_sent = 0

        self._calls_read = 0
        self._calls_readline = 0
        self._calls_readlines = 0

        self._calls_write = 0
        self._calls_yield = 0

        self._request_environment = {}
        self._response_properties = {}
        self._transaction_metrics = {}

        self.background_task = False

        self.enabled = False
        self.autorum_disabled = False

        self.ignore_transaction = False
        self.suppress_apdex = False
        self.suppress_transaction_trace = False

        self.capture_params = None

        self.response_code = 0

        self.apdex = 0

        self.rum_token = None

        # 16-digit random hex. Padded with zeros in the front.
        self.guid = '%016x' % random.getrandbits(64)

        self.client_cross_process_id = None
        self.client_account_id = None
        self.client_application_id = None
        self.referring_transaction_guid = None
        self.record_tt = False
        self._trip_id = None
        self._referring_path_hash = None
        self._alternate_path_hashes = {}
        self.is_part_of_cat = False

        self.synthetics_resource_id = None
        self.synthetics_job_id = None
        self.synthetics_monitor_id = None
        self.synthetics_header = None

        self._custom_metrics = CustomMetrics()

        self._profile_samples = deque()
        self._profile_frames = {}
        self._profile_skip = 1
        self._profile_count = 0

        global_settings = application.global_settings

        if global_settings.enabled:
            if enabled or (enabled is None and application.enabled):
                self._settings = application.settings
                if not self._settings:
                    application.activate()

                    # We see again if the settings is now valid
                    # in case startup timeout had been specified
                    # and registration had been started and
                    # completed within the timeout.

                    self._settings = application.settings

                if self._settings:
                    self.enabled = True

    def __del__(self):
        self._dead = True
        if self._state == self.STATE_RUNNING:
            self.__exit__(None, None, None)

    def save_transaction(self):
        transaction_cache().save_transaction(self)

    def drop_transaction(self):
        transaction_cache().drop_transaction(self)

    def __enter__(self):

        assert(self._state == self.STATE_PENDING)

        # Bail out if the transaction is not enabled.

        if not self.enabled:
            return self

        # Mark transaction as active and update state
        # used to validate correct usage of class.

        self._state = self.STATE_RUNNING

        # Cache transaction in thread/coroutine local
        # storage so that it can be accessed from
        # anywhere in the context of the transaction.

        try:
            self.save_transaction()
        except:  # Catch all
            self._state = self.STATE_PENDING
            self.enabled = False
            raise

        # Record the start time for transaction.

        self.start_time = time.time()

        # Record initial CPU user time.

        self._cpu_user_time_start = os.times()[0]

        # Calculate initial thread utilisation factor.
        # For now we only do this if we know it is an
        # actual thread and not a greenlet.

        if (not hasattr(sys, '_current_frames') or
                self.thread_id in sys._current_frames()):
            thread_instance = threading.currentThread()
            self._utilization_tracker = utilization_tracker(
                    self.application.name)
            if self._utilization_tracker:
                self._utilization_tracker.enter_transaction(thread_instance)
                self._thread_utilization_start = \
                        self._utilization_tracker.utilization_count()

        # We need to push an object onto the top of the
        # node stack so that children can reach back and
        # add themselves as children to the parent. We
        # can't use ourself though as we then end up
        # with a reference count cycle which will cause
        # the destructor to never be called if the
        # __exit__() function is never called. We
        # instead push on to the top of the node stack a
        # dummy time trace object and when done we will
        # just grab what we need from that.

        self.current_node = Sentinel()

        return self

    def __exit__(self, exc, value, tb):

        # Bail out if the transaction is not enabled.

        if not self.enabled:
            return

        if self._transaction_id != id(self):
            return

        if not self._settings:
            return

        # Ensure that we are actually back at the top of
        # transaction call stack. Assume that it is an
        # instrumentation error and return with hope that
        # will recover later.

        for _ in range(self._settings.agent_limits.max_outstanding_traces):
            if isinstance(self.current_node, Sentinel):
                break
            self.current_node.__exit__(None, None, None)
        else:
            _logger.error('Transaction ended but current_node is not Sentinel.'
                    ' Current node is %r. Report this issue to New Relic '
                    'support.\n%s', self.current_node, ''.join(
                    traceback.format_stack()[:-1]))
            return

        # Mark as stopped and drop the transaction from
        # thread/coroutine local storage.
        #
        # Note that we validate the saved transaction ID
        # against that for the current transaction object
        # to protect against situations where a copy was
        # made of the transaction object for some reason.
        # Such a copy when garbage collected could trigger
        # this function and cause a deadlock if it occurs
        # while original transaction was being recorded.

        self._state = self.STATE_STOPPED

        if not self._dead:
            try:
                self.drop_transaction()
            except:  # Catch all
                _logger.exception('Unable to drop transaction.')
                raise

        # Record error if one was registered.

        if exc is not None and value is not None and tb is not None:
            self.record_exception(exc, value, tb)

        # Record the end time for transaction and then
        # calculate the duration.

        if not self.stopped:
            self.end_time = time.time()

        # Calculate transaction duration

        duration = self.end_time - self.start_time

        # Calculate response time. Calculation depends on whether
        # a web response was sent back.

        if self.last_byte_time == 0.0:
            response_time = duration
        else:
            response_time = self.last_byte_time - self.start_time

        # Calculate overall user time.

        if not self._cpu_user_time_end:
            self._cpu_user_time_end = os.times()[0]

        if duration and self._cpu_user_time_end:
            self._cpu_user_time_value = (self._cpu_user_time_end -
                    self._cpu_user_time_start)

        # Calculate thread utilisation factor. Note that even if
        # we are tracking thread utilization we skip calculation
        # if duration is zero. Under normal circumstances this
        # should not occur but may if the system clock is wound
        # backwards and duration was squashed to zero due to the
        # request appearing to finish before it started. It may
        # also occur if true response time came in under the
        # resolution of the clock being used, but that is highly
        # unlikely as the overhead of the agent itself should
        # always ensure that that is hard to achieve.

        if self._utilization_tracker:
            self._utilization_tracker.exit_transaction()
            if self._thread_utilization_start is not None and duration > 0.0:
                if not self._thread_utilization_end:
                    self._thread_utilization_end = (
                            self._utilization_tracker.utilization_count())
                self._thread_utilization_value = (
                        self._thread_utilization_end -
                        self._thread_utilization_start) / duration

        # Derive generated values from the raw data. The
        # dummy root node has exclusive time of children
        # as negative number. Add our own duration to get
        # our own exclusive time.

        root = self.current_node
        children = root.children

        exclusive = duration + root.exclusive

        # Calculate total time.
        #
        # Because we do not track activity on threads, and we currently
        # don't allocate waiting time in the IOLoop to separate segments
        # (like External or Datastore), for right now, our total_time is
        # equal to the duration of the transaction.

        self.total_time = duration

        # Construct final root node of transaction trace.
        # Freeze path in case not already done. This will
        # construct out path.

        self._freeze_path()

        if self.background_task:
            transaction_type = 'OtherTransaction'
        else:
            transaction_type = 'WebTransaction'

        group = self._group

        if group is None:
            if self.background_task:
                group = 'Python'
            else:
                group = 'Uri'

        if self.response_code != 0:
            self._response_properties['STATUS'] = str(self.response_code)

        # _sent_end should already be set by this point, but in case it
        # isn't, set it now before we record the custom metrics.

        if self._sent_start:
            if not self._sent_end:
                self._sent_end = time.time()

        if not self.background_task:
            self.record_custom_metric('Python/WSGI/Input/Bytes',
                               self._bytes_read)
            self.record_custom_metric('Python/WSGI/Input/Time',
                               self.read_duration)
            self.record_custom_metric('Python/WSGI/Input/Calls/read',
                               self._calls_read)
            self.record_custom_metric('Python/WSGI/Input/Calls/readline',
                               self._calls_readline)
            self.record_custom_metric('Python/WSGI/Input/Calls/readlines',
                               self._calls_readlines)

            self.record_custom_metric('Python/WSGI/Output/Bytes',
                               self._bytes_sent)
            self.record_custom_metric('Python/WSGI/Output/Time',
                               self.sent_duration)
            self.record_custom_metric('Python/WSGI/Output/Calls/yield',
                               self._calls_yield)
            self.record_custom_metric('Python/WSGI/Output/Calls/write',
                               self._calls_write)

        if self.client_cross_process_id is not None:
            metric_name = 'ClientApplication/%s/all' % (
                    self.client_cross_process_id)
            self.record_custom_metric(metric_name, duration)

        # Record supportability metrics for api calls

        for key, value in six.iteritems(self._transaction_metrics):
            self.record_custom_metric(key, {'count': value})

        if self._frameworks:
            for framework, version in self._frameworks:
                self.record_custom_metric('Python/Framework/%s/%s' %
                    (framework, version), 1)

        node = newrelic.core.transaction_node.TransactionNode(
                settings=self._settings,
                path=self.path,
                type=transaction_type,
                group=group,
                base_name=self._name,
                name_for_metric=self.name_for_metric,
                port=self._port,
                request_uri=self._request_uri,
                response_code=self.response_code,
                queue_start=self.queue_start,
                start_time=self.start_time,
                end_time=self.end_time,
                last_byte_time=self.last_byte_time,
                total_time=self.total_time,
                response_time=response_time,
                duration=duration,
                exclusive=exclusive,
                children=tuple(children),
                errors=tuple(self._errors),
                slow_sql=tuple(self._slow_sql),
                custom_events=self._custom_events,
                apdex_t=self.apdex,
                suppress_apdex=self.suppress_apdex,
                custom_metrics=self._custom_metrics,
                guid=self.guid,
                cpu_time=self._cpu_user_time_value,
                suppress_transaction_trace=self.suppress_transaction_trace,
                client_cross_process_id=self.client_cross_process_id,
                referring_transaction_guid=self.referring_transaction_guid,
                record_tt=self.record_tt,
                synthetics_resource_id=self.synthetics_resource_id,
                synthetics_job_id=self.synthetics_job_id,
                synthetics_monitor_id=self.synthetics_monitor_id,
                synthetics_header=self.synthetics_header,
                is_part_of_cat=self.is_part_of_cat,
                trip_id=self.trip_id,
                path_hash=self.path_hash,
                referring_path_hash=self._referring_path_hash,
                alternate_path_hashes=self.alternate_path_hashes,
                trace_intrinsics=self.trace_intrinsics,
                agent_attributes=self.agent_attributes,
                user_attributes=self.user_attributes,
        )

        # Clear settings as we are all done and don't need it
        # anymore.

        self._settings = None
        self.enabled = False

        # Unless we are ignoring the transaction, record it. We
        # need to lock the profile samples and replace it with
        # an empty list just in case the thread profiler kicks
        # in just as we are trying to record the transaction.
        # If we don't, when processing the samples, addition of
        # new samples can cause an error.

        if not self.ignore_transaction:
            profile_samples = []

            if self._profile_samples:
                with self._transaction_lock:
                    profile_samples = self._profile_samples
                    self._profile_samples = deque()

            self._application.record_transaction(node,
                    (self.background_task, profile_samples))

    @property
    def state(self):
        return self._state

    @property
    def settings(self):
        return self._settings

    @property
    def application(self):
        return self._application

    @property
    def type(self):
        if self.background_task:
            transaction_type = 'OtherTransaction'
        else:
            transaction_type = 'WebTransaction'
        return transaction_type

    @property
    def name(self):
        return self._name

    @property
    def group(self):
        return self._group

    @property
    def name_for_metric(self):
        """Combine group and name for use as transaction name in metrics."""

        group = self._group

        if group is None:
            if self.background_task:
                group = 'Python'
            else:
                group = 'Uri'

        transaction_name = self._name

        if transaction_name is None:
            transaction_name = '<undefined>'

        # Stripping the leading slash on the request URL held by
        # transaction_name when type is 'Uri' is to keep compatibility
        # with PHP agent and also possibly other agents. Leading
        # slash it not deleted for other category groups as the
        # leading slash may be significant in that situation.

        if (group in ('Uri', 'NormalizedUri') and
                transaction_name.startswith('/')):
            name = '%s%s' % (group, transaction_name)
        else:
            name = '%s/%s' % (group, transaction_name)

        return name

    @property
    def path(self):
        if self._frozen_path:
            return self._frozen_path

        return '%s/%s' % (self.type, self.name_for_metric)

    @property
    def profile_sample(self):
        return self._profile_samples

    @property
    def trip_id(self):
        return self._trip_id or self.guid

    @property
    def alternate_path_hashes(self):
        """Return the alternate path hashes but not including the current path
        hash.

        """
        return sorted(set(self._alternate_path_hashes.values()) -
                set([self.path_hash]))

    @property
    def path_hash(self):
        """Path hash is a 32-bit digest of the string "appname;txn_name"
        XORed with the referring_path_hash. Since the txn_name can change
        during the course of a transaction, up to 10 path_hashes are stored
        in _alternate_path_hashes. Before generating the path hash, check the
        _alternate_path_hashes to determine if we've seen this identifier and
        return the value.

        """

        if not self.is_part_of_cat:
            return None

        identifier = '%s;%s' % (self.application.name, self.path)

        # Check if identifier is already part of the _alternate_path_hashes and
        # return the value if available.

        if self._alternate_path_hashes.get(identifier):
            return self._alternate_path_hashes[identifier]

        # If the referring_path_hash is unavailable then we use '0' as the
        # seed.

        try:
            seed = int((self._referring_path_hash or '0'), base=16)
        except Exception:
            seed = 0

        path_hash = generate_path_hash(identifier, seed)

        # Only store upto 10 alternate path hashes.

        if len(self._alternate_path_hashes) < 10:
            self._alternate_path_hashes[identifier] = path_hash

        return path_hash

    @property
    def attribute_filter(self):
        return self._settings.attribute_filter

    @property
    def read_duration(self):
        read_duration = 0
        if self._read_start and self._read_end:
            read_duration = self._read_end - self._read_start
        return read_duration

    @property
    def sent_duration(self):
        sent_duration = 0
        if self._sent_start and self._sent_end:
            sent_duration = self._sent_end - self._sent_start
        return sent_duration

    @property
    def queue_wait(self):
        queue_wait = 0
        if self.queue_start:
            queue_wait = self.start_time - self.queue_start
            if queue_wait < 0:
                queue_wait = 0
        return queue_wait

    @property
    def should_record_segment_params(self):
        # Only record parameters when it is safe to do so
        return (self.settings and
                not self.settings.high_security)

    @property
    def trace_intrinsics(self):
        """Intrinsic attributes for transaction traces and error traces"""
        i_attrs = {}

        if self.referring_transaction_guid:
            i_attrs['referring_transaction_guid'] = \
                    self.referring_transaction_guid
        if self.client_cross_process_id:
            i_attrs['client_cross_process_id'] = self.client_cross_process_id
        if self.trip_id:
            i_attrs['trip_id'] = self.trip_id
        if self.path_hash:
            i_attrs['path_hash'] = self.path_hash
        if self.synthetics_resource_id:
            i_attrs['synthetics_resource_id'] = self.synthetics_resource_id
        if self.synthetics_job_id:
            i_attrs['synthetics_job_id'] = self.synthetics_job_id
        if self.synthetics_monitor_id:
            i_attrs['synthetics_monitor_id'] = self.synthetics_monitor_id
        if self.total_time:
            i_attrs['totalTime'] = self.total_time

        # Add in special CPU time value for UI to display CPU burn.

        # XXX Disable cpu time value for CPU burn as was
        # previously reporting incorrect value and we need to
        # fix it, at least on Linux to report just the CPU time
        # for the executing thread.

        # if self._cpu_user_time_value:
        #     i_attrs['cpu_time'] = self._cpu_user_time_value

        return i_attrs

    @property
    def request_parameters_attributes(self):
        # Request parameters are a special case of agent attributes, so
        # they must be added on to agent_attributes separately

        # There are 3 cases we need to handle:
        #
        # 1. LEGACY: capture_params = False
        #
        #    Don't add request parameters at all, which means they will not
        #    go through the AttributeFilter.
        #
        # 2. LEGACY: capture_params = True
        #
        #    Filter request parameters through the AttributeFilter, but
        #    set the destinations to `TRANSACTION_TRACER | ERROR_COLLECTOR`.
        #
        #    If the user does not add any additional attribute filtering
        #    rules, this will result in the same outcome as the old
        #    capture_params = True behavior. They will be added to transaction
        #    traces and error traces.
        #
        # 3. CURRENT: capture_params is None
        #
        #    Filter request parameters through the AttributeFilter, but set
        #    the destinations to NONE.
        #
        #    That means by default, request parameters won't get included in
        #    any destination. But, it will allow user added include/exclude
        #    attribute filtering rules to be applied to the request parameters.

        attributes_request = []

        if (self.capture_params is None) or self.capture_params:

            if self._request_params:

                r_attrs = {}

                for k, v in self._request_params.items():
                    new_key = 'request.parameters.%s' % k
                    new_val = ",".join(v)

                    final_key, final_val = process_user_attribute(new_key,
                            new_val)

                    if final_key:
                        r_attrs[final_key] = final_val

                if self.capture_params is None:
                    attributes_request = create_attributes(r_attrs,
                            DST_NONE, self.attribute_filter)
                elif self.capture_params:
                    attributes_request = create_attributes(r_attrs,
                            DST_ERROR_COLLECTOR | DST_TRANSACTION_TRACER,
                            self.attribute_filter)

        return attributes_request

    @property
    def agent_attributes(self):
        a_attrs = {}
        settings = self._settings
        req_env = self._request_environment

        if req_env.get('HTTP_ACCEPT', None):
            a_attrs['request.headers.accept'] = req_env['HTTP_ACCEPT']
        if req_env.get('CONTENT_LENGTH', None):
            a_attrs['request.headers.contentLength'] = \
                    req_env['CONTENT_LENGTH']
        if req_env.get('CONTENT_TYPE', None):
            a_attrs['request.headers.contentType'] = req_env['CONTENT_TYPE']
        if req_env.get('HTTP_HOST', None):
            a_attrs['request.headers.host'] = req_env['HTTP_HOST']
        if req_env.get('HTTP_REFERER', None):
            a_attrs['request.headers.referer'] = req_env['HTTP_REFERER']
        if req_env.get('HTTP_USER_AGENT', None):
            a_attrs['request.headers.userAgent'] = req_env['HTTP_USER_AGENT']
        if req_env.get('REQUEST_METHOD', None):
            a_attrs['request.method'] = req_env['REQUEST_METHOD']

        resp_props = self._response_properties

        if resp_props.get('CONTENT_LENGTH', None):
            a_attrs['response.headers.contentLength'] = \
                    resp_props['CONTENT_LENGTH']
        if resp_props.get('CONTENT_TYPE', None):
            a_attrs['response.headers.contentType'] = \
                    resp_props['CONTENT_TYPE']
        if resp_props.get('STATUS', None):
            a_attrs['response.status'] = resp_props['STATUS']

        if self.read_duration != 0:
            a_attrs['wsgi.input.seconds'] = self.read_duration
        if self._bytes_read != 0:
            a_attrs['wsgi.input.bytes'] = self._bytes_read
        if self._calls_read != 0:
            a_attrs['wsgi.input.calls.read'] = self._calls_read
        if self._calls_readline != 0:
            a_attrs['wsgi.input.calls.readline'] = self._calls_readline
        if self._calls_readlines != 0:
            a_attrs['wsgi.input.calls.readlines'] = self._calls_readlines

        if self.sent_duration != 0:
            a_attrs['wsgi.output.seconds'] = self.sent_duration
        if self._bytes_sent != 0:
            a_attrs['wsgi.output.bytes'] = self._bytes_sent
        if self._calls_write != 0:
            a_attrs['wsgi.output.calls.write'] = self._calls_write
        if self._calls_yield != 0:
            a_attrs['wsgi.output.calls.yield'] = self._calls_yield

        if self._settings.process_host.display_name:
            a_attrs['host.displayName'] = settings.process_host.display_name
        if self._thread_utilization_value:
            a_attrs['thread.concurrency'] = self._thread_utilization_value
        if self.queue_wait != 0:
            a_attrs['webfrontend.queue.seconds'] = self.queue_wait

        agent_attributes = create_agent_attributes(a_attrs,
                self.attribute_filter)

        # Include request parameters in agent attributes

        agent_attributes.extend(self.request_parameters_attributes)

        return agent_attributes

    @property
    def user_attributes(self):
        return create_user_attributes(self._custom_params,
                self.attribute_filter)

    def add_profile_sample(self, stack_trace):
        if self._state != self.STATE_RUNNING:
            return

        self._profile_count += 1

        if self._profile_count < self._profile_skip:
            return

        self._profile_count = 0

        with self._transaction_lock:
            new_stack_trace = tuple(self._profile_frames.setdefault(
                    frame, frame) for frame in stack_trace)
            self._profile_samples.append(new_stack_trace)

            agent_limits = self._application.global_settings.agent_limits
            profile_maximum = agent_limits.xray_profile_maximum

            if len(self._profile_samples) >= profile_maximum:
                self._profile_samples = deque(itertools.islice(
                        self._profile_samples, 0,
                        len(self._profile_samples), 2))
                self._profile_skip = 2 * self._profile_skip

    def _freeze_path(self):
        if self._frozen_path is None:
            self._priority = None

            if self._group == 'Uri' and self._name != '/':
                # Apply URL normalization rules. We would only have raw
                # URLs where we were not specifically naming the web
                # transactions for a specific web framework to be a code
                # handler or otherwise.

                name, ignore = self._application.normalize_name(
                        self._name, 'url')

                if self._name != name:
                    self._group = 'NormalizedUri'
                    self._name = name

                self.ignore_transaction = self.ignore_transaction or ignore

            # Apply transaction rules on the full transaction name.

            path, ignore = self._application.normalize_name(
                    self.path, 'transaction')

            self.ignore_transaction = self.ignore_transaction or ignore

            # Apply segment whitelist rule to the segments on the full
            # transaction name. The path is frozen at this point and cannot be
            # further changed.

            self._frozen_path, ignore = self._application.normalize_name(
                    path, 'segment')

            self.ignore_transaction = self.ignore_transaction or ignore

            # Look up the apdex from the table of key transactions. If
            # current transaction is not a key transaction then use the
            # default apdex from settings. The path used at this point
            # is the frozen path.

            self.apdex = (self._settings.web_transactions_apdex.get(
                self.path) or self._settings.apdex_t)

    def _process_incoming_cat_headers(self, encoded_cross_process_id,
            encoded_txn_header):
        settings = self._settings

        if not self.enabled:
            return

        if not (settings.cross_application_tracer.enabled and
                settings.cross_process_id and settings.trusted_account_ids and
                settings.encoding_key):
            return

        if encoded_cross_process_id is None:
            return

        try:
            client_cross_process_id = deobfuscate(
                    encoded_cross_process_id, settings.encoding_key)

            # The cross process ID consists of the client
            # account ID and the ID of the specific application
            # the client is recording requests against. We need
            # to validate that the client account ID is in the
            # list of trusted account IDs and ignore it if it
            # isn't. The trusted account IDs list has the
            # account IDs as integers, so save the client ones
            # away as integers here so easier to compare later.

            client_account_id, client_application_id = \
                    map(int, client_cross_process_id.split('#'))

            if client_account_id not in settings.trusted_account_ids:
                return

            self.client_cross_process_id = client_cross_process_id
            self.client_account_id = client_account_id
            self.client_application_id = client_application_id

            txn_header = json_decode(deobfuscate(
                    encoded_txn_header,
                    settings.encoding_key))

            if txn_header:
                self.is_part_of_cat = True
                self.referring_transaction_guid = txn_header[0]

                # Incoming record_tt is OR'd with existing
                # record_tt. In the scenario where we make multiple
                # ext request, this will ensure we don't set the
                # record_tt to False by a later request if it was
                # set to True by an earlier request.

                self.record_tt = (self.record_tt or
                        txn_header[1])

                if isinstance(txn_header[2], six.string_types):
                    self._trip_id = txn_header[2]
                if isinstance(txn_header[3], six.string_types):
                    self._referring_path_hash = txn_header[3]
        except Exception:
            pass

    def _generate_response_headers(self):
        nr_headers = []

        # Generate metrics and response headers for inbound cross
        # process web external calls.

        if self.client_cross_process_id is not None:

            # Need to work out queueing time and duration up to this
            # point for inclusion in metrics and response header. If the
            # recording of the transaction had been prematurely stopped
            # via an API call, only return time up until that call was
            # made so it will match what is reported as duration for the
            # transaction.

            if self.queue_start:
                queue_time = self.start_time - self.queue_start
            else:
                queue_time = 0

            if self.end_time:
                duration = self.end_time - self.start_time
            else:
                duration = time.time() - self.start_time

            # Generate the additional response headers which provide
            # information back to the caller. We need to freeze the
            # transaction name before adding to the header.

            self._freeze_path()

            payload = (self._settings.cross_process_id, self.path, queue_time,
                    duration, self._read_length, self.guid, self.record_tt)
            app_data = json_encode(payload)

            nr_headers.append(('X-NewRelic-App-Data', obfuscate(
                    app_data, self._settings.encoding_key)))

        return nr_headers

    def get_response_metadata(self):
        nr_headers = dict(self._generate_response_headers())
        return convert_to_cat_metadata_value(nr_headers)

    def process_request_metadata(self, cat_linking_value):
        try:
            payload = base64_decode(cat_linking_value)
        except:
            # `cat_linking_value` should always be able to be base64_decoded.
            # If this is encountered, the data being sent is corrupt. No
            # exception should be raised.
            return

        nr_headers = json_decode(payload)
        # TODO: All the external CAT APIs really need to
        # be refactored into the transaction class.
        encoded_cross_process_id = nr_headers.get('X-NewRelic-ID')
        encoded_txn_header = nr_headers.get('X-NewRelic-Transaction')
        return self._process_incoming_cat_headers(encoded_cross_process_id,
                encoded_txn_header)

    def set_transaction_name(self, name, group=None, priority=None):

        # Always perform this operation even if the transaction
        # is not active at the time as will be called from
        # constructor. If path has been frozen do not allow
        # name/group to be overridden. New priority then must be
        # same or greater than existing priority. If no priority
        # always override the existing name/group if not frozen.

        if self._priority is None:
            return

        if priority is not None and priority < self._priority:
            return

        if priority is not None:
            self._priority = priority

        # The name can be a URL for the default case. URLs are
        # supposed to be ASCII but can get a URL with illegal
        # non ASCII characters. As the rule patterns and
        # replacements are Unicode then can get Unicode
        # conversion warnings or errors when URL is converted to
        # Unicode and default encoding is ASCII. Thus need to
        # convert URL to Unicode as Latin-1 explicitly to avoid
        # problems with illegal characters.

        if isinstance(name, bytes):
            name = name.decode('Latin-1')

        # Deal with users who use group wrongly and add a leading
        # slash on it. This will cause an empty segment which we
        # want to avoid. In that case insert back in Function as
        # the leading segment.

        group = group or 'Function'

        if group.startswith('/'):
            group = 'Function' + group

        self._group = group
        self._name = name

    def name_transaction(self, name, group=None, priority=None):
        return self.set_transaction_name(name, group, priority)

    def record_exception(self, exc=None, value=None, tb=None,
                         params={}, ignore_errors=[]):

        # Bail out if the transaction is not active or
        # collection of errors not enabled.

        if not self._settings:
            return

        settings = self._settings
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

        # Only remember up to limit of what can be caught for a
        # single transaction. This could be trimmed further
        # later if there are already recorded errors and would
        # go over the harvest limit.

        if len(self._errors) >= settings.agent_limits.errors_per_transaction:
            return

        # Only add params if High Security Mode is off.

        custom_params = {}

        if settings.high_security:
            if params:
                _logger.debug('Cannot add custom parameters in '
                        'High Security Mode.')
        else:
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

        # Check that we have not recorded this exception
        # previously for this transaction due to multiple
        # error traces triggering. This is not going to be
        # exact but the UI hides exceptions of same type
        # anyway. Better that we under count exceptions of
        # same type and message rather than count same one
        # multiple times.

        for error in self._errors:
            if error.type == fullname and error.message == message:
                return

        node = newrelic.core.error_node.ErrorNode(
                timestamp=time.time(),
                type=fullname,
                message=message,
                stack_trace=exception_stack(tb),
                custom_params=custom_params,
                file_name=None,
                line_number=None,
                source=None)

        # TODO Errors are recorded in time order. If
        # there are two exceptions of same type and
        # different message, the UI displays the first
        # one. In the PHP agent it was recording the
        # errors in reverse time order and so the UI
        # displayed the last one. What is the the
        # official order in which they should be sent.

        self._errors.append(node)

    def notice_error(self, exc, value, tb, params={}, ignore_errors=[]):
        warnings.warn('Internal API change. Use record_exception() '
                'instead of notice_error().', DeprecationWarning,
                stacklevel=2)

        self.record_exception(exc, value, tb, params, ignore_errors)

    def record_custom_metric(self, name, value):
        self._custom_metrics.record_custom_metric(name, value)

    def record_custom_metrics(self, metrics):
        for name, value in metrics:
            self._custom_metrics.record_custom_metric(name, value)

    def record_custom_event(self, event_type, params):
        settings = self._settings

        if not settings:
            return

        if not settings.custom_insights_events.enabled:
            return

        event = create_custom_event(event_type, params)
        if event:
            self._custom_events.add(event)

    def record_metric(self, name, value):
        warnings.warn('Internal API change. Use record_custom_metric() '
                'instead of record_metric().', DeprecationWarning,
                stacklevel=2)

        return self.record_custom_metric(name, value)

    def active_node(self):
        return self.current_node

    def _intern_string(self, value):
        return self._string_cache.setdefault(value, value)

    def _push_current(self, node):
        self.current_node = node

    def _pop_current(self, node):
        parent = node.parent
        self.current_node = parent

        return parent

    def _process_node(self, node):
        self._trace_node_count += 1
        node.node_count = self._trace_node_count

        if type(node) is newrelic.core.database_node.DatabaseNode:
            settings = self._settings
            if not settings.collect_traces:
                return
            if (not settings.slow_sql.enabled and
                    not settings.transaction_tracer.explain_enabled):
                return
            if settings.transaction_tracer.record_sql == 'off':
                return
            if node.duration < settings.transaction_tracer.explain_threshold:
                return
            self._slow_sql.append(node)

    def stop_recording(self):
        if not self.enabled:
            return

        if self.stopped:
            return

        if self.end_time:
            return

        self.end_time = time.time()
        self.stopped = True

        if self._utilization_tracker:
            if self._thread_utilization_start:
                if not self._thread_utilization_end:
                    self._thread_utilization_end = (
                            self._utilization_tracker.utilization_count())

        self._cpu_user_time_end = os.times()[0]

    def add_custom_parameter(self, name, value):
        if not self._settings:
            return False

        if self._settings.high_security:
            _logger.debug('Cannot add custom parameter in High Security Mode.')
            return False

        if len(self._custom_params) >= MAX_NUM_USER_ATTRIBUTES:
            _logger.debug('Maximum number of custom attributes already '
                    'added. Dropping attribute: %r=%r', name, value)
            return False

        key, val = process_user_attribute(name, value)

        if key is None:
            return False
        else:
            self._custom_params[key] = val
            return True

    def add_custom_parameters(self, items):
        # items is a list of (name, value) tuples.
        for name, value in items:
            self.add_custom_parameter(name, value)

    def add_user_attribute(self, name, value):
        self.add_custom_parameter(name, value)

    def add_user_attributes(self, items):
        self.add_custom_parameters(items)

    def add_framework_info(self, name, version=None):
        if name:
            self._frameworks.add((name, version))

    def dump(self, file):
        """Dumps details about the transaction to the file object."""

        print >> file, 'Application: %s' % (
                self.application.name)
        print >> file, 'Time Started: %s' % (
                time.asctime(time.localtime(self.start_time)))
        print >> file, 'Thread Id: %r' % (
                self.thread_id,)
        print >> file, 'Current Status: %d' % (
                self._state)
        print >> file, 'Recording Enabled: %s' % (
                self.enabled)
        print >> file, 'Ignore Transaction: %s' % (
                self.ignore_transaction)
        print >> file, 'Transaction Dead: %s' % (
                self._dead)
        print >> file, 'Transaction Stopped: %s' % (
                self.stopped)
        print >> file, 'Background Task: %s' % (
                self.background_task)
        print >> file, 'Request URI: %s' % (
                self._request_uri)
        print >> file, 'Transaction Group: %s' % (
                self._group)
        print >> file, 'Transaction Name: %s' % (
                self._name)
        print >> file, 'Name Priority: %r' % (
                self._priority)
        print >> file, 'Frozen Path: %s' % (
                self._frozen_path)
        print >> file, 'AutoRUM Disabled: %s' % (
                self.autorum_disabled)
        print >> file, 'Supress Apdex: %s' % (
                self.suppress_apdex)
        print >> file, 'Current Node: %s' % (
                self.current_node)


def current_transaction(active_only=True):
    current = transaction_cache().current_transaction()
    if active_only:
        if current and (current.ignore_transaction or current.stopped):
            return None
    return current


def transaction():
    warnings.warn('Internal API change. Use current_transaction() '
            'instead of transaction().', DeprecationWarning, stacklevel=2)

    return current_transaction()


def set_transaction_name(name, group=None, priority=None):
    transaction = current_transaction()
    if transaction:
        transaction.set_transaction_name(name, group, priority)


def name_transaction(name, group=None, priority=None):
    warnings.warn('API change. Use set_transaction_name() instead of '
            'name_transaction().', DeprecationWarning, stacklevel=2)
    transaction = current_transaction()
    if transaction:
        transaction.set_transaction_name(name, group, priority)


def end_of_transaction():
    transaction = current_transaction()
    if transaction:
        transaction.stop_recording()


def set_background_task(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.background_task = flag


def ignore_transaction(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.ignore_transaction = flag


def suppress_apdex_metric(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.suppress_apdex = flag


def capture_request_params(flag=True):
    transaction = current_transaction()
    if transaction and transaction.settings:
        if transaction.settings.high_security:
            _logger.warn("Cannot modify capture_params in High Security Mode.")
        else:
            transaction.capture_params = flag


def add_custom_parameter(key, value):
    transaction = current_transaction()
    if transaction:
        return transaction.add_custom_parameter(key, value)
    else:
        return False


def add_user_attribute(key, value):
    return add_custom_parameter(key, value)


def add_framework_info(name, version=None):
    transaction = current_transaction()
    if transaction:
        transaction.add_framework_info(name, version)


def record_exception(exc=None, value=None, tb=None, params={},
        ignore_errors=[], application=None):
    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_exception(exc, value, tb, params,
                    ignore_errors)
    else:
        if application.enabled:
            application.record_exception(exc, value, tb, params,
                    ignore_errors)


def get_browser_timing_header():
    transaction = current_transaction()
    if transaction and hasattr(transaction, 'browser_timing_header'):
        return transaction.browser_timing_header()
    return ''


def get_browser_timing_footer():
    transaction = current_transaction()
    if transaction and hasattr(transaction, 'browser_timing_footer'):
        return transaction.browser_timing_footer()
    return ''


def disable_browser_autorum(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.autorum_disabled = flag


def suppress_transaction_trace(flag=True):
    transaction = current_transaction()
    if transaction:
        transaction.suppress_transaction_trace = flag


def record_custom_metric(name, value, application=None):
    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_metric(name, value)
    else:
        if application.enabled:
            application.record_custom_metric(name, value)


def record_custom_metrics(metrics, application=None):
    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_metrics(metrics)
    else:
        if application.enabled:
            application.record_custom_metrics(metrics)


def record_custom_event(event_type, params, application=None):
    """Record a custom event.

    Args:
        event_type (str): The type (name) of the custom event.
        params (dict): Attributes to add to the event.
        application (newrelic.api.Application): Application instance.

    """

    if application is None:
        transaction = current_transaction()
        if transaction:
            transaction.record_custom_event(event_type, params)
    else:
        if application.enabled:
            application.record_custom_event(event_type, params)
