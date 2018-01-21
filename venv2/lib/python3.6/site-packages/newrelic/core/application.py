"""This module implements data recording and reporting for an application.

"""

import logging
import sys
import threading
import time
import os
import traceback
import imp

from functools import partial

import newrelic.packages.six as six

from newrelic.samplers.data_sampler import DataSampler

from newrelic.core.config import global_settings_dump, global_settings
from newrelic.core.custom_event import create_custom_event
from newrelic.core.data_collector import create_session
from newrelic.network.exceptions import (ForceAgentRestart,
        ForceAgentDisconnect, DiscardDataForRequest, RetryDataForRequest)
from newrelic.core.environment import environment_settings
from newrelic.core.rules_engine import RulesEngine, SegmentCollapseEngine
from newrelic.core.stats_engine import StatsEngine, CustomMetrics
from newrelic.core.internal_metrics import (InternalTrace,
        InternalTraceContext, internal_metric, internal_count_metric)
from newrelic.core.xray_session import XraySession
from newrelic.core.profile_sessions import profile_session_manager

from newrelic.core.database_utils import SQLConnections
from newrelic.common.object_names import callable_name

_logger = logging.getLogger(__name__)


class Application(object):

    """Class which maintains recorded data for a single application.

    """

    def __init__(self, app_name, linked_applications=[]):
        _logger.debug('Initializing application with name %r and '
                'linked applications of %r.', app_name, linked_applications)

        self._creation_time = time.time()

        self._app_name = app_name
        self._linked_applications = sorted(set(linked_applications))

        self._process_id = None

        self._period_start = 0.0

        self._active_session = None
        self._harvest_enabled = False

        self._transaction_count = 0
        self._last_transaction = 0.0

        self._global_events_account = 0

        self._harvest_count = 0

        self._merge_count = 0
        self._discard_count = 0

        self._agent_restart = 0
        self._pending_shutdown = False
        self._agent_shutdown = False

        self._connected_event = threading.Event()

        self._detect_deadlock = False
        self._deadlock_event = threading.Event()

        self._stats_lock = threading.RLock()
        self._stats_engine = StatsEngine()

        self._stats_custom_lock = threading.RLock()
        self._stats_custom_engine = StatsEngine()

        self._agent_commands_lock = threading.Lock()
        self._data_samplers_lock = threading.Lock()
        self._data_samplers_started = False

        # We setup empty rules engines here even though they will be
        # replaced when application first registered. This is done to
        # avoid a race condition in setting it later. Otherwise we have
        # to use unnecessary locking to protect access.

        self._rules_engine = {'url': RulesEngine([]),
                'transaction': RulesEngine([]),
                'metric': RulesEngine([]),
                'segment': SegmentCollapseEngine([])}

        self._data_samplers = []

        # Thread profiler and state of whether active or not.

        # self._thread_profiler = None
        # self._profiler_started = False
        # self._send_profile_data = False

        # self._xray_profiler = None
        self.xray_session_running = False

        self.profile_manager = profile_session_manager()

        # This holds a dictionary of currently active xray sessions.
        # key = xray_id
        # value = XraySession object

        self._active_xrays = {}

    @property
    def name(self):
        return self._app_name

    @property
    def linked_applications(self):
        return self._linked_applications

    @property
    def configuration(self):
        return self._active_session and self._active_session.configuration

    @property
    def active(self):
        return self.configuration is not None

    def dump(self, file):
        """Dumps details about the application to the file object."""

        print >> file, 'Time Created: %s' % (
                time.asctime(time.localtime(self._creation_time)))
        print >> file, 'Linked Applications: %r' % (
                self._linked_applications)
        print >> file, 'Registration PID: %s' % (
                self._process_id)
        print >> file, 'Harvest Count: %d' % (
                self._harvest_count)
        print >> file, 'Agent Restart: %d' % (
                self._agent_restart)
        print >> file, 'Forced Shutdown: %s' % (
                self._agent_shutdown)

        active_session = self._active_session

        if active_session:
            print >> file, 'Collector URL: %s' % (
                    active_session.collector_url)
            print >> file, 'Agent Run ID: %d' % (
                    active_session.agent_run_id)
            print >> file, 'URL Normalization Rules: %r' % (
                    self._rules_engine['url'].rules)
            print >> file, 'Metric Normalization Rules: %r' % (
                    self._rules_engine['metric'].rules)
            print >> file, 'Transaction Normalization Rules: %r' % (
                    self._rules_engine['transaction'].rules)
            print >> file, 'Transaction Segment Whitelist Rules: %r' % (
                    self._rules_engine['segment'].rules)
            print >> file, 'Harvest Period Start: %s' % (
                    time.asctime(time.localtime(self._period_start)))
            print >> file, 'Transaction Count: %d' % (
                    self._transaction_count)
            print >> file, 'Last Transaction: %s' % (
                    time.asctime(time.localtime(self._last_transaction)))
            print >> file, 'Global Events Count: %d' % (
                    self._global_events_account)
            print >> file, 'Harvest Metrics Count: %d' % (
                    self._stats_engine.metrics_count())
            print >> file, 'Harvest Merge Count: %d' % (
                    self._merge_count)
            print >> file, 'Harvest Discard Count: %d' % (
                    self._discard_count)

    def activate_session(self, timeout=0.0):
        """Creates a background thread to initiate registration of the
        application with the data collector if no active session already
        exists. Will wait up to the timeout specified for the session
        to be activated.

        """

        if self._agent_shutdown:
            return

        if self._pending_shutdown:
            return

        if self._active_session:
            return

        self._process_id = os.getpid()

        self._connected_event.clear()
        self._deadlock_event.clear()

        # If the session is activated when the Python global import lock
        # has been acquired by the parent thread then the parent thread
        # can potentially deadlock due to lazy imports in code being run
        # to activate the session for the application. The deadlock will
        # only be broken when the timeout completes at which point the
        # activation process will resume. We want to avoid blocking the
        # activation process and the parent thread for no good reason,
        # so we use an extra event object to try and detect a potential
        # deadlock. This works by having the activation thread try and
        # explicitly lock the global module import lock. When it can it
        # will set the event. If this doesn't occur within our hard
        # wired timeout value, we will bail out on assumption that
        # timeout has likely occurred.

        deadlock_timeout = 0.1

        if timeout >= deadlock_timeout:
            self._detect_deadlock = True

        thread = threading.Thread(target=self.connect_to_data_collector,
                name='NR-Activate-Session/%s' % self.name)
        thread.setDaemon(True)
        thread.start()

        if not timeout:
            return True

        if self._detect_deadlock:
            self._deadlock_event.wait(deadlock_timeout)

            if not self._deadlock_event.isSet():
                _logger.warning('Detected potential deadlock while waiting '
                        'for activation of session for application %r. '
                        'Returning after %0.2f seconds rather than waiting. '
                        'If this problem occurs on every process restart, '
                        'see the API documentation for proper usage of '
                        'the newrelic.agent.register_application() function '
                        'or if necessary report this problem to New Relic '
                        'support for further investigation.', self._app_name,
                        deadlock_timeout)
                return False

        self._connected_event.wait(timeout)

        if not self._connected_event.isSet():
            _logger.debug('Timeout waiting for activation of session for '
                    'application %r where timeout was %.02f seconds.',
                    self._app_name, timeout)
            return False

        return True

    def connect_to_data_collector(self):
        """Performs the actual registration of the application with the
        data collector if no current active session.

        """

        if self._agent_shutdown:
            return

        if self._pending_shutdown:
            return

        if self._active_session:
            return

        # Remember when we started attempt to connect so can record a
        # metric of how long it actually took.

        connect_start = time.time()

        # We perform a short sleep here to ensure that this thread is
        # suspended and the main thread gets to run. This is necessary
        # for greenlet based systems else this thread would run until
        # some other condition occurs which would cause it to yield. If
        # that is allowed, then the first request which triggered
        # activation of the application would be unduly delayed. A value
        # of 10ms seems to work best. If it is made shorter at around
        # 1ms, then it doesn't seem to cause a yield and still get a
        # delay. So needs to be long enough to ensure a yield but not
        # too long to hold off this thread either.

        time.sleep(0.01)

        # Acquire the Python module import lock and set a flag when we
        # have it. This is done to detect the potential for a deadlock
        # on the import lock where the code which activated the
        # application held an import lock at the time of activation and
        # is waiting for registration to complete. This short circuits
        # the timeout so the caller isn't blocked for the full wait time
        # if this thread was in a deadlock state that prevented it from
        # running. Such a deadlock state could occur where subsequent
        # code run from this thread performs a deferred module import.

        if self._detect_deadlock:
            imp.acquire_lock()
            self._deadlock_event.set()
            imp.release_lock()

        # Register the application with the data collector. Any errors
        # that occur will be dealt with by create_session(). The result
        # will either be a session object or None. In the event of a
        # failure to register we will try again, gradually backing off
        # for longer and longer periods as we retry. The retry interval
        # will be capped at 300 seconds.

        active_session = None

        retries = [(15, False, False), (15, False, False),
                   (30, False, False), (60, True, False),
                   (120, False, False), (300, False, True), ]

        connect_attempts = 0

        try:
            while not active_session:

                if self._agent_shutdown:
                    return

                if self._pending_shutdown:
                    return

                connect_attempts += 1

                internal_metrics = CustomMetrics()

                with InternalTraceContext(internal_metrics):
                    active_session = create_session(None, self._app_name,
                            self.linked_applications, environment_settings(),
                            global_settings_dump())

                # We were successful, but first need to make sure we do
                # not have any problems with the agent normalization
                # rules provided by the data collector. These could blow
                # up when being compiled if the patterns are broken or
                # use text which conflicts with extensions in Python's
                # regular expression syntax.

                if active_session:
                    configuration = active_session.configuration

                    try:
                        settings = global_settings()

                        if settings.debug.log_normalization_rules:
                            _logger.info('The URL normalization rules for '
                                    '%r are %r.', self._app_name,
                                     configuration.url_rules)
                            _logger.info('The metric normalization rules '
                                    'for %r are %r.', self._app_name,
                                     configuration.metric_name_rules)
                            _logger.info('The transaction normalization '
                                    'rules for %r are %r.', self._app_name,
                                     configuration.transaction_name_rules)

                        self._rules_engine['url'] = RulesEngine(
                                configuration.url_rules)
                        self._rules_engine['metric'] = RulesEngine(
                                configuration.metric_name_rules)
                        self._rules_engine['transaction'] = RulesEngine(
                                configuration.transaction_name_rules)
                        self._rules_engine['segment'] = SegmentCollapseEngine(
                                configuration.transaction_segment_terms)

                    except Exception:
                        _logger.exception('The agent normalization rules '
                                'received from the data collector could not '
                                'be compiled properly by the agent due to a '
                                'syntactical error or other problem. Please '
                                'report this to New Relic support for '
                                'investigation.')

                        # For good measure, in this situation we explicitly
                        # shutdown the session as then the data collector
                        # will record this. Ignore any error from this. Then
                        # we discard the session so we go into a retry loop
                        # on presumption that issue with the URL rules will
                        # be fixed.

                        try:
                            active_session.shutdown_session()
                        except Exception:
                            pass

                        active_session = None

                # Were we successful. If not we will sleep for a bit and
                # then go back and try again. Log warnings or errors as
                # per schedule associated with the retry intervals.

                if not active_session:
                    if retries:
                        timeout, warning, error = retries.pop(0)

                        if warning:
                            _logger.warning('Registration of the application '
                                    '%r with the data collector failed after '
                                    'multiple attempts. Check the prior log '
                                    'entries and remedy any issue as '
                                    'necessary, or if the problem persists, '
                                    'report this problem to New Relic '
                                    'support for further investigation.',
                                    self._app_name)

                        elif error:
                            _logger.error('Registration of the application '
                                    '%r with the data collector failed after '
                                    'further additional attempts. Please '
                                    'report this problem to New Relic support '
                                    'for further investigation.',
                                    self._app_name)

                    else:
                        timeout = 300

                    _logger.debug('Retrying registration of the application '
                            '%r with the data collector after a further %d '
                            'seconds.', self._app_name, timeout)

                    time.sleep(timeout)

            # We were successful. Ensure we have cleared out any cached
            # data from a prior agent run for this application.

            configuration = active_session.configuration

            with self._stats_lock:
                self._stats_engine.reset_stats(configuration)

            with self._stats_custom_lock:
                self._stats_custom_engine.reset_stats(configuration)

            # Record an initial start time for the reporting period and
            # clear record of last transaction processed.

            self._period_start = time.time()

            self._transaction_count = 0
            self._last_transaction = 0.0

            self._global_events_account = 0

            # Clear any prior count of harvest merges due to failures.

            self._merge_count = 0

            # Record metrics for how long it took us to connect and how
            # many attempts we made. Also record metrics for the final
            # successful attempt. If we went through multiple attempts,
            # individual details of errors before the final one that
            # worked are not recorded as recording them all in the
            # initial harvest would possibly skew first harvest metrics
            # and cause confusion as we cannot properly mark the time over
            # which they were recorded. Make sure we do this before we
            # mark the session active so we don't have to grab a lock on
            # merging the internal metrics.

            with InternalTraceContext(internal_metrics):
                internal_metric('Supportability/Python/Application/'
                        'Registration/Duration',
                        self._period_start - connect_start)
                internal_metric('Supportability/Python/Application/'
                        'Registration/Attempts',
                        connect_attempts)

            self._stats_engine.merge_custom_metrics(
                    internal_metrics.metrics())

            # Update the active session in this object. This will the
            # recording of transactions to start.

            self._active_session = active_session

            # Enable the ability to perform a harvest. This is okay to
            # do at this point as the processing of agent commands and
            # starting of data samplers are protected by their own locks.

            self._harvest_enabled = True

            # Flag that the session activation has completed to
            # anyone who has been waiting through calling the
            # wait_for_session_activation() method.

            self._connected_event.set()

            # Immediately fetch any agent commands now even before start
            # recording any transactions so running of any X-Ray
            # sessions is not delayed. This could fail due to issues
            # talking to the data collector or if we get back bad data.
            # We need to make sure we ignore such errors and still allow
            # the registration to be finalised so that agent still
            # start up and collect metrics. Any X-Ray sessions will be
            # picked up in subsequent harvest.

            try:
                self.process_agent_commands()

            except RetryDataForRequest:
                # Ignore any error connecting to the data collector at
                # this point as trying to get agent commands at this
                # point is an optimisation and not a big issue if it fails.
                # Transient issues with the data collector for this will
                # just cause noise in the agent logs and worry users. An
                # ongoing connection issue will be picked properly with
                # the subsequent data harvest.

                pass

            except Exception:
                if not self._agent_shutdown and not self._pending_shutdown:
                    _logger.exception('Unexpected exception when processing '
                            'agent commands when registering agent with the '
                            'data collector. If this problem persists, please '
                            'report this problem to New Relic support for '
                            'further investigation.')
                else:
                    raise

            # Start any data samplers so they are aware of the start of
            # the harvest period.

            self.start_data_samplers()

        except Exception:
            # If an exception occurs after agent has been flagged to be
            # shutdown then we ignore the error. This is because all
            # sorts of wierd errors could occur when main thread start
            # destroying objects and this background thread to register
            # the application is still running.

            if not self._agent_shutdown and not self._pending_shutdown:
                _logger.exception('Unexpected exception when registering '
                        'agent with the data collector. If this problem '
                        'persists, please report this problem to New Relic '
                        'support for further investigation.')

        try:
            self._active_session.close_connection()
        except:
            pass

    def validate_process(self):
        """Logs a warning message if called in a process different to
        where the application was registered. Only logs a message the
        first time this is detected for current active session.

        """

        process_id = os.getpid()

        # Detect where potentially trying to record any data in a
        # process different to where the harvest thread was created.
        # Note that this only works for the case where a section had
        # been activated prior to the process being forked.

        if self._process_id and process_id != self._process_id:
            _logger.warning('Attempt to reactivate application or record '
                    'transactions in a process different to where the '
                    'agent was already registered for application %r. No '
                    'data will be reported for this process with pid of '
                    '%d. Registration of the agent for this application '
                    'occurred in process with pid %d. If no data at all '
                    'is being reported for your application, then please '
                    'report this problem to New Relic support for further '
                    'investigation.', self._app_name, process_id,
                    self._process_id)

            settings = global_settings()

            if settings.debug.log_agent_initialization:
                _logger.info('Process validation check was triggered '
                        'from: %r', ''.join(traceback.format_stack()[:-1]))
            else:
                _logger.debug('Process validation check was triggered '
                        'from: %r', ''.join(traceback.format_stack()[:-1]))

            # We now zero out the process ID so we know we have already
            # generated a warning message.

            self._process_id = 0

    def normalize_name(self, name, rule_type):
        """Applies the agent normalization rules of the the specified
        rule type to the supplied name.

        """

        if not self._active_session:
            return name, False

        try:
            return self._rules_engine[rule_type].normalize(name)

        except Exception:
            # In the event that the rules engine blows up because of a
            # problem in the rules supplied by the data collector, we
            # log the exception and otherwise return the original.
            #
            # NOTE This has the potential to cause metric grouping
            # issues, but we should not be getting broken rules to begin
            # with if they are validated properly when entered or
            # generated. We could perhaps instead flag that the
            # transaction be ignored and thus not reported.

            _logger.exception('The application of the normalization '
                    'rules for %r has failed. This can indicate '
                    'a problem with the agent rules supplied by the '
                    'data collector. Please report this problem to New '
                    'Relic support for further investigation.', name)

            return name, False

    def register_data_source(self, source, name, settings, **properties):
        """Create a data sampler corresponding to the data source
        for this application.

        """

        _logger.debug('Register data source %r against application where '
                'application=%r, name=%r, settings=%r and properties=%r.',
                source, self._app_name, name, settings, properties)

        self._data_samplers.append(DataSampler(self._app_name, source,
                name, settings, **properties))

    def start_data_samplers(self):
        """Starts any data samplers. This will be called when the
        application has been successfully registered and monitoring of
        transactions commences.

        """
        with self._data_samplers_lock:
            _logger.debug('Starting data samplers for application %r.',
                    self._app_name)

            for data_sampler in self._data_samplers:
                try:
                    _logger.debug('Starting data sampler for %r in '
                            'application %r.', data_sampler.name,
                            self._app_name)

                    data_sampler.start()
                except Exception:
                    _logger.exception('Unexpected exception when starting '
                            'data source %r. Custom metrics from this data '
                            'source may not be subsequently available. If '
                            'this problem persists, please report this '
                            'problem to the provider of the data source.',
                            data_sampler.name)

            self._data_samplers_started = True

    def stop_data_samplers(self):
        """Stop any data samplers. This will be called when the active
        session is terminated due to a harvest reporting error or process
        shutdown.

        """

        with self._data_samplers_lock:
            _logger.debug('Stopping data samplers for application %r.',
                    self._app_name)

            for data_sampler in self._data_samplers:
                try:
                    _logger.debug('Stopping data sampler for %r in '
                            'application %r.', data_sampler.name,
                            self._app_name)

                    data_sampler.stop()
                except Exception:
                    _logger.exception('Unexpected exception when stopping '
                            'data source %r Custom metrics from this data '
                            'source may not be subsequently available. If '
                            'this problem persists, please report this '
                            'problem to the provider of the data source.',
                            data_sampler.name)

    def remove_data_source(self, name):
        with self._data_samplers_lock:

            data_sampler = [x for x in self._data_samplers if x.name == name]

            if len(data_sampler) > 0:

                # Should be at most one data sampler for a given name.

                data_sampler = data_sampler[0]

                try:
                    _logger.debug('Removing/Stopping data sampler for %r in '
                             'application %r.', data_sampler.name,
                             self._app_name)

                    data_sampler.stop()

                except Exception:

                    # If sampler has not started yet, it may throw an error.

                    _logger.debug('Exception when stopping '
                             'data source %r when attempting to remove it.',
                             data_sampler.name)

                self._data_samplers.remove(data_sampler)

    def record_exception(self, exc=None, value=None, tb=None, params={},
            ignore_errors=[]):

        """Record a global exception against the application independent
        of a specific transaction.

        """

        if not self._active_session:
            return

        with self._stats_lock:
            # It may still actually be rejected if no exception
            # supplied or if was in the ignored list. For now
            # always attempt anyway and also increment the events
            # count still so that short harvest is extended.

            self._global_events_account += 1
            self._stats_engine.record_exception(exc, value, tb,
                    params, ignore_errors)

    def record_custom_metric(self, name, value):
        """Record a custom metric against the application independent
        of a specific transaction.

        NOTE that this will require locking of the stats engine for
        custom metrics and so under heavy use will have performance
        issues. It is better to record the custom metric against an
        active transaction as they will then be aggregated at the end of
        the transaction when all other metrics are aggregated and so no
        additional locking will be required.

        """

        if not self._active_session:
            return

        with self._stats_custom_lock:
            self._global_events_account += 1
            self._stats_custom_engine.record_custom_metric(name, value)

    def record_custom_metrics(self, metrics):
        """Record a set of custom metrics against the application
        independent of a specific transaction.

        NOTE that this will require locking of the stats engine for
        custom metrics and so under heavy use will have performance
        issues. It is better to record the custom metric against an
        active transaction as they will then be aggregated at the end of
        the transaction when all other metrics are aggregated and so no
        additional locking will be required.

        """

        if not self._active_session:
            return

        with self._stats_custom_lock:
            for name, value in metrics:
                self._global_events_account += 1
                self._stats_custom_engine.record_custom_metric(name, value)

    def record_custom_event(self, event_type, params):
        if not self._active_session:
            return

        settings = self._stats_engine.settings

        if settings is None or not settings.custom_insights_events.enabled:
            return

        event = create_custom_event(event_type, params)

        if event:
            with self._stats_custom_lock:
                self._global_events_account += 1
                self._stats_engine.record_custom_event(event)

    def record_transaction(self, data, profile_samples=None):
        """Record a single transaction against this application."""

        if not self._active_session:
            return

        settings = self._stats_engine.settings

        if settings is None:
            return

        # Validate that the transaction was started against the same
        # agent run ID as we are now recording data for. They might be
        # different where a long running transaction covered multiple
        # agent runs due to a server side configuration change.

        if settings.agent_run_id != data.settings.agent_run_id:
            _logger.debug('Discard transaction for application %r as '
                    'runs over multiple agent runs. Initial agent run ID '
                    'is %r and the current agent run ID is %r.',
                    self._app_name, data.settings.agent_run_id,
                    settings.agent_run_id)
            return

        # Do checks to see whether trying to record a transaction in a
        # different process to that the application was activated in.

        self.validate_process()

        internal_metrics = CustomMetrics()

        with InternalTraceContext(internal_metrics):
            try:
                # We accumulate stats into a workarea and only then merge it
                # into the main one under a thread lock. Do this to ensure
                # that the process of generating the metrics into the stats
                # don't unecessarily lock out another thread.

                stats = self._stats_engine.create_workarea()
                stats.record_transaction(data)

            except Exception:
                _logger.exception('The generation of transaction data has '
                        'failed. This would indicate some sort of internal '
                        'implementation issue with the agent. Please report '
                        'this problem to New Relic support for further '
                        'investigation.')

                if settings.debug.record_transaction_failure:
                    raise

            if (profile_samples and (data.path in
                    self._stats_engine.xray_sessions or
                    'WebTransaction/Agent/__profiler__' in
                    self._stats_engine.xray_sessions)):

                try:
                    background_task, samples = profile_samples

                    tr_type = 'BACKGROUND' if background_task else 'REQUEST'

                    if data.path in self._stats_engine.xray_sessions:
                        self.profile_manager.add_stack_traces(self._app_name,
                                data.path, tr_type, samples)

                    if ('WebTransaction/Agent/__profiler__' in
                            self._stats_engine.xray_sessions):
                        self.profile_manager.add_stack_traces(self._app_name,
                                'WebTransaction/Agent/__profiler__', tr_type,
                                samples)

                except Exception:
                    _logger.exception('Building xray profile tree has failed.'
                            'This would indicate some sort of internal '
                            'implementation issue with the agent. Please '
                            'report this problem to New Relic support for '
                            'further investigation.')

                    if settings.debug.record_transaction_failure:
                        raise

            with self._stats_lock:
                try:
                    self._transaction_count += 1
                    self._last_transaction = data.end_time

                    self._stats_engine.merge(stats)

                    # We merge the internal statistics here as well even
                    # though have popped out of the context where we are
                    # recording. This is okay so long as don't record
                    # anything else after this point. If we do then that
                    # data will not be recorded.

                    self._stats_engine.merge_custom_metrics(
                            internal_metrics.metrics())

                except Exception:
                    _logger.exception('The merging of transaction data has '
                            'failed. This would indicate some sort of '
                            'internal implementation issue with the agent. '
                            'Please report this problem to New Relic support '
                            'for further investigation.')

                    if settings.debug.record_transaction_failure:
                        raise

    def start_xray(self, command_id=0, **kwargs):
        """Handler for agent command 'start_xray_session'. """

        if not self._active_session.configuration.xray_session.enabled:
            _logger.warning('An xray session was requested '
                    'for %r but xray sessions are disabled by the current '
                    'agent configuration. Enable "xray_session.enabled" '
                    'in the agent configuration.', self._app_name)
            return {command_id: {'error': 'The xray sessions are disabled'}}

        try:
            xray_id = kwargs['x_ray_id']
            name = kwargs['key_transaction_name']
            duration_s = kwargs.get('duration', 864000)  # 86400s = 24hrs
            max_traces = kwargs.get('requested_trace_count', 100)
            sample_period_s = kwargs.get('sample_period', 0.1)
            run_profiler = kwargs.get('run_profiler', True)
        except KeyError:

            # A KeyError can happen if an xray id was present in
            # active_xray_sessions but it was cancelled by the user before the
            # agent could get it's metadata.

            _logger.warning('An xray session was requested but appropriate '
                    'parameters were not provided. Report this error '
                    'to New Relic support for further investigation. '
                    'Provided Params: %r', kwargs)
            return {command_id: {'error': 'The xray sessions error'}}

        stop_time_s = self._period_start + duration_s

        # Check whether we are already running an xray session for this
        # xray id and ignore the subsequent request if we are.

        if self._active_xrays.get(xray_id) is not None:
            _logger.warning('An xray session was requested for %r but '
                      'an xray session for the requested key transaction '
                      '%r with ID of %r is already in progress. Ignoring '
                      'the subsequent request. This can happen, but if it '
                      'keeps occurring on a regular basis, please report '
                      'this problem to New Relic support for further '
                      'investigation.', self._app_name, name, xray_id)

            return {command_id: {'error': 'Xray session already running.'}}

        # Check whether we have an xray session running for the same key
        # transaction, we should only ever have one. If already have one
        # and the existing one has an ID which indicates it is older, then
        # stop the existing one so we can replace it with the newer one.
        # Otherwise allow the existing one to stand and ignore the new one.

        xs = self._stats_engine.xray_sessions.get(name)

        if xs:
            if xs.xray_id < xray_id:
                _logger.warning('An xray session was requested for %r but '
                        'an xray session with id %r for the requested key '
                        'transaction %r is already in progress. Replacing '
                        'the existing older xray session with the newer xray '
                        'session with id %r. This can happen occassionally. '
                        'But if it keeps occurring on a regular basis, '
                        'please report this problem to New Relic support '
                        'for further  investigation.', self._app_name,
                        xs.xray_id, name, xray_id)

                self.stop_xray(x_ray_id=xs.xray_id,
                        key_transaction_name=xs.key_txn)

            else:
                _logger.warning('An xray session was requested for %r but '
                        'a newer xray session with id %r for the requested '
                        'key transaction %r is already in progress. Ignoring '
                        'the older xray session request with id %r. This can '
                        'happen occassionally. But if it keeps occurring '
                        'on a regular basis, please report this problem '
                        'to New Relic support for further  investigation.',
                        self._app_name, xs.xray_id, name, xray_id)

                return {command_id: {'error': 'Xray session already running.'}}

        xs = XraySession(xray_id, name, stop_time_s, max_traces,
                sample_period_s)

        # Add it to the currently active xrays.

        self._active_xrays[xray_id] = xs

        # Add it to the stats engine to start recording Xray TTs.

        self._stats_engine.xray_sessions[name] = xs

        # Start the xray profiler only if requested by collector.

        if run_profiler:
            profiler_status = self.profile_manager.start_profile_session(
                    self._app_name, -1, stop_time_s, sample_period_s, False,
                    name, xray_id)

            if not profiler_status:
                _logger.warning('Unable to start profile session for '
                        'application %s', self._app_name)

        _logger.info('Starting an xray session for %r. '
                'duration:%d mins name:%s xray_id:%d', self._app_name,
                duration_s / 60, name, xray_id)

        return {command_id: {}}

    def stop_xray(self, command_id=0, **kwargs):
        """Handler for agent command 'stop_xray_session'. This command
        is sent by collector under two conditions:

        1. When there are enough traces for the xray session.
        2. When the user cancels an xray session in progress.

        """
        try:
            xray_id = kwargs['x_ray_id']
            name = kwargs['key_transaction_name']
        except KeyError:
            _logger.warning('A stop xray was requested but appropriate '
                    'parameters were not provided. Report this error '
                    'to New Relic support for further investigation. '
                    'Provided Params: %r', kwargs)
            return {command_id: {'error': 'Xray session stop error.'}}

        # An xray session is deemed as already_running if the xray_id is
        # already present in the self._active_xrays or the key txn is already
        # tracked in the stats_engine.xray_sessions.

        already_running = self._active_xrays.get(xray_id) is not None
        already_running |= (self._stats_engine.xray_sessions.get(name) is not
                None)
        if not already_running:
            _logger.warning('A request was received to stop xray '
                    'session %d for %r, but the xray session is not running. '
                    'If this keeps occurring on a regular basis, please '
                    'report this problem to New Relic support for further '
                    'investigation.', xray_id, self._app_name)

            return {command_id: {'error': 'Xray session not running.'}}

        try:
            xs = self._active_xrays.pop(xray_id)
            self._stats_engine.xray_sessions.pop(xs.key_txn)
        except KeyError:
            pass

        # We are deliberately ignoring the return value from
        # stop_profile_session because there is a chance that the profiler has
        # stopped automatically after the alloted duration has elapsed before
        # the collector got a chance to issue the stop_xray command. We don't
        # want to raise an alarm for that scenario.

        _logger.info('Stopping xray session %d for %r', xray_id,
                self._app_name)

        self.profile_manager.stop_profile_session(self._app_name, xs.key_txn)

        return {command_id: {}}

    def cmd_active_xray_sessions(self, command_id=0, **kwargs):
        """Receives  a list of xray_ids that are currently active in the
        datacollector.

        """

        # If xray_sessions are disabled in the config file, just ignore the
        # active_xray_sessions command and proceed.
        #
        # This can happen if one of the hosts has the xrays disabled but the
        # other hosts are running x-rays.

        if not self._active_session.configuration.xray_session.enabled:
            return None

        # Create a set from the xray_ids received from the collector.

        collector_xray_ids = set(kwargs['xray_ids'])

        _logger.debug('X Ray sessions expected to be running for %r are '
                '%r.', self._app_name, collector_xray_ids)

        # Create a set from the xray_ids currently active in the agent.

        agent_xray_ids = set(self._active_xrays)

        _logger.debug('X Ray sessions actually running for %r are '
                '%r.', self._app_name, agent_xray_ids)

        # Result of the (agent_xray_ids - collector_xray_ids) will be
        # the ids that are not active in collector but are still active
        # in the agent. These xray sessions must be stopped.

        stopped_xrays = agent_xray_ids - collector_xray_ids

        _logger.debug('X Ray sessions to be stopped for %r are '
                '%r.', self._app_name, stopped_xrays)

        for xray_id in stopped_xrays:
            xs = self._active_xrays.get(xray_id)
            self.stop_xray(x_ray_id=xs.xray_id,
                    key_transaction_name=xs.key_txn)

        # Result of the (collector_xray_ids - agent_xray_ids) will be
        # the ids that are new xray sessions created in the collector
        # but are not yet activated in the agent. Agent will contact the
        # collector with each xray_id and ask for it's metadata, then
        # start the corresponding xray_sessions. Note that we sort the
        # list of IDs and give precedence to larger value, which should
        # be newer. Do this just in case the data collector is tardy
        # in flushing out a complete one and UI has allowed a new one
        # to be created and so have multiple for same key transaction.

        new_xrays = sorted(collector_xray_ids - agent_xray_ids, reverse=True)

        _logger.debug('X Ray sessions to be started for %r are '
                '%r.', self._app_name, new_xrays)

        for xray_id in new_xrays:
            metadata = self._active_session.get_xray_metadata(xray_id)
            if not metadata:
                # We may get empty meta data if the xray session had
                # completed or been deleted just prior to requesting
                # the meta data.

                _logger.debug('Meta data for xray session with id %r '
                        'of %r is empty, ignore it.', xray_id, self._app_name)
            else:
                self.start_xray(0, **metadata[0])

        # Note that 'active_xray_sessions' does NOT need to send an
        # acknowledgement back to the collector

        return None

    def cmd_start_profiler(self, command_id=0, **kwargs):
        """Triggered by the start_profiler agent command to start a
        thread profiling session.

        """

        if not self._active_session.configuration.thread_profiler.enabled:
            _logger.warning('A thread profiling session was requested '
                    'for %r but thread profiling is disabled by the current '
                    'agent configuration. Enable "thread_profiler.enabled" '
                    'in the agent configuration.', self._app_name)
            return {command_id: {'error': 'The profiler service is disabled'}}

        profile_id = kwargs['profile_id']
        sample_period = kwargs['sample_period']
        duration_s = kwargs['duration']
        profile_agent_code = kwargs['profile_agent_code']

        stop_time_s = self._period_start + duration_s

        if not hasattr(sys, '_current_frames'):
            _logger.warning('A thread profiling session was requested for '
                    '%r but thread profiling is not supported for the '
                    'Python interpreter being used. Contact New Relic '
                    'support for additional information about supported '
                    'platforms for the thread profiling feature.',
                    self._app_name)
            return {command_id: {'error': 'Profiler not supported'}}

        # ProfilerManager will only allow one generic thread profiler to be
        # active at any given time. So if a user has multiple applications and
        # tries to start an thread profiler from both of them, then it will
        # fail and log an error message. The thread profiler will report on all
        # threads in the process and not just those handling transactions
        # related to the specific application.

        success = self.profile_manager.start_profile_session(self._app_name,
                profile_id, stop_time_s, sample_period, profile_agent_code)

        if not success:
            _logger.warning('A thread profiling session was requested for '
                    '%r but a thread profiling session is already in '
                    'progress. Ignoring the subsequent request. '
                    'If this keeps occurring on a regular basis, please '
                    'report this problem to New Relic support for further '
                    'investigation.', self._app_name)
            return {command_id: {'error': 'Profiler already running'}}

        _logger.info('Starting thread profiling session for %r.',
                self._app_name)

        return {command_id: {}}

    def cmd_stop_profiler(self, command_id=0, **kwargs):
        """Triggered by the stop_profiler agent command to forcibly stop
        a thread profiling session prior to it having completed normally.

        """

        fps = self.profile_manager.full_profile_session

        if fps is None:
            _logger.warning('A request was received to stop a thread '
                    'profiling session for %r, but a thread profiling '
                    'session is not running. If this keeps occurring on '
                    'a regular basis, please report this problem to New '
                    'Relic support for further investigation.',
                    self._app_name)
            return {command_id: {'error': 'Profiler not running.'}}

        elif kwargs['profile_id'] != fps.profile_id:
            _logger.warning('A request was received to stop a thread '
                    'profiling session for %r, but the ID %r for '
                    'the current thread profiling session does not '
                    'match the provided ID of %r. If this keeps occurring on '
                    'a regular basis, please report this problem to New '
                    'Relic support for further investigation.',
                    self._app_name, fps.profile_id,
                    kwargs['profile_id'])
            return {command_id: {'error': 'Profiler not running.'}}

        _logger.info('Stopping thread profiler session for %r.',
                self._app_name)

        # To ensure that the thread profiling session stops, we wait for
        # its completion. If we don't need to send back the data from
        # the thread profiling session, we discard the thread profiler
        # immediately.

        self.profile_manager.stop_profile_session(self._app_name)

        return {command_id: {}}

    def harvest(self, shutdown=False):
        """Performs a harvest, reporting aggregated data for the current
        reporting period to the data collector.

        """

        if self._agent_shutdown:
            return

        if shutdown:
            self._pending_shutdown = True

        if not self._active_session or not self._harvest_enabled:
            _logger.debug('Cannot perform a data harvest for %r as '
                    'there is no active session.', self._app_name)

            return

        internal_metrics = CustomMetrics()

        with InternalTraceContext(internal_metrics):
            with InternalTrace('Supportability/Python/Harvest/Calls/harvest'):

                self._harvest_count += 1

                start = time.time()

                _logger.debug('Commencing data harvest of %r.',
                        self._app_name)

                # Create a snapshot of the transaction stats and
                # application specific custom metrics stats, then merge
                # them together. The originals will be reset at the time
                # this is done so that any new metrics that come in from
                # this point onwards will be accumulated in a fresh
                # bucket.

                _logger.debug('Snapshotting metrics for harvest of %r.',
                        self._app_name)

                transaction_count = self._transaction_count
                global_events_account = self._global_events_account

                with self._stats_lock:
                    self._transaction_count = 0
                    self._last_transaction = 0.0

                    stats = self._stats_engine.harvest_snapshot()

                with self._stats_custom_lock:
                    self._global_events_account = 0

                    stats_custom = self._stats_custom_engine.harvest_snapshot()

                # stats_custom should only contain metric stats, no
                # transactions

                stats.merge_metric_stats(stats_custom)

                # Now merge in any metrics from the data samplers
                # associated with this application.
                #
                # NOTE If a data sampler has problems then what data was
                # collected up to that point is retained. The data
                # collector itself is still retained and would be used
                # again on future harvest. If it is a persistent problem
                # with the data sampler the issue would then reoccur
                # with every harvest. If data sampler is a user provided
                # data sampler, then should perhaps deregister it if it
                # keeps having problems.

                _logger.debug('Fetching metrics from data sources for '
                        'harvest of %r.', self._app_name)

                for data_sampler in self._data_samplers:
                    try:
                        for sample in data_sampler.metrics():
                            try:
                                name, value = sample
                                stats.record_custom_metric(name, value)
                            except Exception:
                                _logger.exception('The merging of custom '
                                        'metric sample %r from data source %r '
                                        'has failed. Validate the format of '
                                        'the sample. If this issue persists '
                                        'then please report this problem to '
                                        'the data source provider or New '
                                        'Relic support for further '
                                        'investigation.', sample,
                                        data_sampler.name)
                                break

                    except Exception:
                        _logger.exception('The merging of custom metric '
                                'samples from data source %r has failed. '
                                'Validate that the data source is producing '
                                'samples correctly. If this issue persists '
                                'then please report this problem to the data '
                                'source provider or New Relic support for '
                                'further investigation.', data_sampler.name)

                # Add a metric we can use to track how many harvest
                # periods have occurred.

                stats.record_custom_metric('Instance/Reporting', 0)

                # Create our time stamp as to when this reporting period
                # ends and start reporting the data.

                period_end = time.time()

                # If this harvest is being forcibly triggered on process
                # shutdown, there are transactions recorded, and the
                # duration of the harvest period is less than 1 second,
                # then artificially push out the end time of the harvest
                # period. This is done so that the harvest period is not
                # less than 1 second, otherwise the data collector will
                # throw the data away. This is desirable for case where
                # trying to monitor scripts which perform a one off task
                # and then immediately exit. Also useful when running
                # test scripts.

                if shutdown and (transaction_count or global_events_account):
                    if period_end - self._period_start < 1.0:
                        _logger.debug('Stretching harvest duration for '
                                'forced harvest on shutdown.')
                        period_end = self._period_start + 1.001

                try:
                    # Send the transaction and custom metric data.

                    configuration = self._active_session.configuration

                    # Send data set for analytics, which is a combination
                    # of Synthetic analytic events, and the sampled data
                    # set of regular requests.

                    all_analytic_events = []

                    if len(stats.synthetics_events):
                        all_analytic_events.extend(stats.synthetics_events)

                    if (configuration.collect_analytics_events and
                            configuration.transaction_events.enabled):

                        samples = stats.transaction_events.samples
                        all_analytic_events.extend(samples)

                    if len(all_analytic_events):
                        _logger.debug('Sending analytics event data '
                                'for harvest of %r.', self._app_name)

                        self._active_session.send_transaction_events(
                                all_analytic_events)

                    # Report internal metrics about sample data set
                    # for analytics.

                    if (configuration.collect_analytics_events and
                            configuration.transaction_events.enabled):

                        transaction_events = stats.transaction_events

                        # As per spec
                        internal_metric('Supportability/Python/'
                                'RequestSampler/requests',
                                transaction_events.num_seen)
                        internal_metric('Supportability/Python/'
                                'RequestSampler/samples',
                                transaction_events.num_samples)

                    stats.reset_transaction_events()
                    stats.reset_synthetics_events()

                    # Send error events

                    if (configuration.collect_error_events and
                            configuration.error_collector.capture_events and
                            configuration.error_collector.enabled):

                        num_error_samples = stats.error_events.num_samples
                        error_events = stats.error_events
                        if num_error_samples > 0:
                            _logger.debug('Sending error event data '
                                    'for harvest of %r.', self._app_name)

                            samp_info = stats.error_events_sampling_info()
                            self._active_session.send_error_events(samp_info,
                                    error_events.samples)

                        # As per spec
                        internal_count_metric('Supportability/Events/'
                                'TransactionError/Seen', error_events.num_seen)
                        internal_count_metric('Supportability/Events/'
                                'TransactionError/Sent', num_error_samples)

                    stats.reset_error_events()

                    # Send custom events

                    if (configuration.collect_custom_events and
                            configuration.custom_insights_events.enabled):

                        customs = stats.custom_events

                        if customs.num_samples > 0:
                            _logger.debug('Sending custom event data '
                                    'for harvest of %r.', self._app_name)

                            self._active_session.send_custom_events(
                                    customs.sampling_info, customs.samples)

                        # As per spec
                        internal_count_metric('Supportability/Events/'
                                'Customer/Seen', customs.num_seen)
                        internal_count_metric('Supportability/Events/'
                                'Customer/Sent', customs.num_samples)

                    stats.reset_custom_events()

                    # Send the accumulated error data.

                    if configuration.collect_errors:
                        error_data = stats.error_data()

                        if error_data:
                            _logger.debug('Sending error data for harvest '
                                    'of %r.', self._app_name)

                            self._active_session.send_errors(error_data)

                    if configuration.collect_traces:
                        connections = SQLConnections(
                                configuration.agent_limits.max_sql_connections)

                        with connections:
                            if configuration.slow_sql.enabled:
                                _logger.debug('Processing slow SQL data '
                                        'for harvest of %r.', self._app_name)

                                slow_sql_data = stats.slow_sql_data(
                                        connections)

                                if slow_sql_data:
                                    _logger.debug('Sending slow SQL data for '
                                            'harvest of %r.', self._app_name)

                                    self._active_session.send_sql_traces(
                                            slow_sql_data)

                            slow_transaction_data = (
                                    stats.transaction_trace_data(
                                    connections))

                            if slow_transaction_data:
                                _logger.debug('Sending slow transaction '
                                        'data for harvest of %r.',
                                        self._app_name)

                                self._active_session.send_transaction_traces(
                                        slow_transaction_data)

                    # Create a metric_normalizer based on normalize_name
                    # If metric rename rules are empty, set normalizer
                    # to None and the stats engine will skip steps as
                    # appropriate.

                    if self._rules_engine['metric'].rules:
                        metric_normalizer = partial(self.normalize_name,
                                rule_type='metric')
                    else:
                        metric_normalizer = None

                    # Merge all ready internal metrics
                    stats.merge_custom_metrics(internal_metrics.metrics())

                    # Clear sent internal metrics
                    internal_metrics.reset_metric_stats()

                    # Pass the metric_normalizer to stats.metric_data to
                    # do metric renaming.

                    _logger.debug('Normalizing metrics for harvest of %r.',
                            self._app_name)

                    metric_data = stats.metric_data(metric_normalizer)

                    _logger.debug('Sending metric data for harvest of %r.',
                            self._app_name)

                    # Send metrics
                    metric_ids = self._active_session.send_metric_data(
                            self._period_start, period_end, metric_data)

                    _logger.debug('Done sending data for harvest of '
                            '%r.', self._app_name)

                    stats.reset_metric_stats()

                    # Successful, so we update the stats engine with the
                    # new metric IDs and reset the reporting period
                    # start time. If an error occurs after this point,
                    # any remaining data for the period being reported
                    # on will be thrown away. We reset the count of
                    # number of merges we have done due to failures as
                    # only really want to count errors in being able to
                    # report the main transaction metrics.

                    self._merge_count = 0
                    self._period_start = period_end
                    self._stats_engine.update_metric_ids(metric_ids)

                    # Fetch agent commands sent from the data collector
                    # and process them.

                    _logger.debug('Process agent commands during '
                            'harvest of %r.', self._app_name)
                    self.process_agent_commands()

                    # Send the accumulated profile data back to the data
                    # collector. Note that this come after we process
                    # the agent commands as we might receive an agent
                    # command to stop the profiling session, but still
                    # send the data back.  Having the sending of the
                    # results last ensures we send back that data from
                    # the stopped profiling session immediately.

                    _logger.debug('Send profiling data for harvest of '
                            '%r.', self._app_name)

                    self.report_profile_data()

                    # If this is a final forced harvest for the process
                    # then attempt to shutdown the session.

                    if shutdown:
                        self.internal_agent_shutdown(restart=False)

                except ForceAgentRestart:
                    # The data collector has indicated that we need to
                    # perform an internal agent restart. We attempt to
                    # properly shutdown the session and then initiate a
                    # new session.

                    self.internal_agent_shutdown(restart=True)

                except ForceAgentDisconnect:
                    # The data collector has indicated that we need to
                    # force disconnect and stop reporting. We attempt to
                    # properly shutdown the session, but don't start a
                    # new one and flag ourselves as shutdown. This
                    # notification is presumably sent when a specific
                    # application is behaving so badly that it needs to
                    # be stopped entirely. It would require a complete
                    # process start to be able to attempt to connect
                    # again and if the server side kill switch is still
                    # enabled it would be told to disconnect once more.

                    self.internal_agent_shutdown(restart=False)

                except RetryDataForRequest:
                    # A potentially recoverable error occurred. We merge
                    # the stats back into that for the current period
                    # and abort the current harvest if the problem
                    # occurred when initially reporting the main
                    # transaction metrics. If the problem occurred when
                    # reporting other information then that and any
                    # other non reported information is thrown away.
                    #
                    # In order to prevent memory growth will we only
                    # merge data up to a set maximum number of
                    # successive times. When this occurs we throw away
                    # all the metric data and start over. We also only
                    # merge main metric data and discard errors, slow
                    # SQL and transaction traces from older harvest
                    # period.

                    exc_type = sys.exc_info()[0]

                    internal_metric('Supportability/Python/Harvest/'
                            'Exception/%s' % callable_name(exc_type), 1)

                    if self._period_start != period_end:

                        self._merge_count += 1

                        agent_limits = configuration.agent_limits
                        maximum = agent_limits.merge_stats_maximum

                        if self._merge_count <= maximum:

                            self._stats_engine.rollback(stats)

                        else:
                            _logger.error('Unable to report main transaction '
                                    'metrics after %r successive attempts. '
                                    'Check the log messages and if necessary '
                                    'please report this problem to New Relic '
                                    'support for further investigation.',
                                    maximum)

                            self._discard_count += self._merge_count

                            self._merge_count = 0

                            # Force an agent restart ourselves.

                            _logger.debug('Abandoning agent run and forcing '
                                    'a reconnect of the agent.')

                            self.internal_agent_shutdown(restart=True)

                except DiscardDataForRequest:
                    # An issue must have occurred in reporting the data
                    # but if we retry with same data the same error is
                    # likely to occur again so we just throw any data
                    # not sent away for this reporting period.

                    exc_type = sys.exc_info()[0]

                    internal_metric('Supportability/Python/Harvest/'
                            'Exception/%s' % callable_name(exc_type), 1)

                    self._discard_count += 1

                except Exception:
                    # An unexpected error, likely some sort of internal
                    # agent implementation issue.

                    exc_type = sys.exc_info()[0]

                    internal_metric('Supportability/Python/Harvest/'
                            'Exception/%s' % callable_name(exc_type), 1)

                    _logger.exception('Unexpected exception when attempting '
                            'to harvest the metric data and send it to the '
                            'data collector. Please report this problem to '
                            'New Relic support for further investigation.')

                duration = time.time() - start

                _logger.debug('Completed harvest for %r in %.2f seconds.',
                        self._app_name, duration)

                # Force close the socket connection which has been
                # created for this harvest if session still exists.
                # New connection will be create automatically on the
                # next harvest.

                if self._active_session:
                    self._active_session.close_connection()

        # Merge back in statistics recorded about the last harvest
        # and communication with the data collector. This will be
        # part of the data for the next harvest period.

        with self._stats_lock:
            self._stats_engine.merge_custom_metrics(internal_metrics.metrics())

    def report_profile_data(self):
        """Report back any profile data. This may be partial thread
        profile data for X-Ray sessions, or final thread profile data
        for a full profiling session.

        """

        for profile_data in self.profile_manager.profile_data(self._app_name):
            if profile_data:
                _logger.debug('Reporting thread profiling session data '
                        'for %r.', self._app_name)
                self._active_session.send_profile_data(profile_data)

    def internal_agent_shutdown(self, restart=False):
        """Terminates the active agent session for this application and
        optionally triggers activation of a new session.

        """

        # We need to stop any thread profiler session related to this
        # application. This may be a full thread profiling session or
        # one run in relation to active X-Ray sessions. We also need to
        # throw away any X-Ray sessions. These will be restarted as
        # necessary after a reconnect if done.

        self.profile_manager.shutdown(self._app_name)

        self._active_xrays = {}

        # Attempt to report back any profile data which was left when
        # all profiling was shutdown due to the agent shutdown for this
        # application.

        try:
            self.report_profile_data()
        except Exception:
            pass

        # Stop any data samplers which are running. These can be internal
        # data samplers or user provided custom metric data sources.

        self.stop_data_samplers()

        # Now shutdown the actual agent session.

        try:
            self._active_session.shutdown_session()
        except Exception:
            pass

        self._active_session.close_connection()

        self._active_session = None
        self._harvest_enabled = False

        # Initiate a new session if required, otherwise mark the agent
        # as shutdown.

        if restart:
            self._agent_restart += 1
            self.activate_session()

        else:
            self._agent_shutdown = True

    def process_agent_commands(self):
        """Fetches agents commands from data collector and process them.

        """

        # We use a lock around this as this will be called just after
        # having registered the agent, as well as during the normal
        # harvest period. We want to avoid a problem if the process is
        # being shutdown and a forced harvest was triggered while still
        # doing the initial attempt to get the agent commands.

        with self._agent_commands_lock:
            # Get agent commands from the data collector.

            _logger.debug('Process agent commands for %r.', self._app_name)

            # Any exception on get agent commands shouldn't interrupt the
            # harvest cycle
            try:
                agent_commands = self._active_session.get_agent_commands()
            except:
                return

            # Extract the command names from the agent_commands. This is
            # used to check for the presence of active_xray_sessions command
            # in the list.

            cmd_names = [x[1]['name'] for x in agent_commands]

            no_xray_cmds = 'active_xray_sessions' not in cmd_names

            # If there are active xray sessions running but the agent
            # commands doesn't have any active_xray_session ids then all the
            # active xray sessions must be stopped.

            if self._active_xrays and no_xray_cmds:
                _logger.debug('Stopping all X Ray sessions for %r. '
                    'Current sessions running are %r.', self._app_name,
                    list(six.iterkeys(self._active_xrays)))

                for xs in list(six.itervalues(self._active_xrays)):
                    self.stop_xray(x_ray_id=xs.xray_id,
                            key_transaction_name=xs.key_txn)

            # For each agent command received, call the appropiate agent
            # command handler. Reply to the data collector with the
            # acknowledgement of the agent command.

            for command in agent_commands:
                cmd_id = command[0]
                cmd_name = command[1]['name']
                cmd_args = command[1]['arguments']

                # An agent command is mapped to a method of this class. If
                # we don't know about a specific agent command we just
                # ignore it.

                func_name = 'cmd_%s' % cmd_name

                cmd_handler = getattr(self, func_name, None)

                if cmd_handler is None:
                    _logger.debug('Received unknown agent command '
                            '%r from the data collector for %r.',
                            cmd_name, self._app_name)
                    continue

                _logger.debug('Process agent command %r from the data '
                        'collector for %r.', cmd_name, self._app_name)

                cmd_res = cmd_handler(cmd_id, **cmd_args)

                # Send back any result for the agent command.

                if cmd_res:
                    self._active_session.send_agent_command_results(cmd_res)
