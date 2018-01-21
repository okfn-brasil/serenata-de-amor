"""This module holds the Agent class which is the primary interface for
interacting with the agent core.

"""

import os
import sys
import time
import logging
import threading
import atexit
import warnings
import traceback

import newrelic
import newrelic.core.config
import newrelic.core.application

import newrelic.packages.six as six

from newrelic.common.log_file import initialize_logging
from newrelic.samplers.cpu_usage import cpu_usage_data_source
from newrelic.samplers.memory_usage import memory_usage_data_source

from newrelic.core.thread_utilization import thread_utilization_data_source

_logger = logging.getLogger(__name__)

def check_environment():
    # If running under uWSGI, then must be version 1.2.6 or newer. Must
    # also be run with '--enable-threads' option.

    if 'uwsgi' in sys.modules:
        import uwsgi

        if not hasattr(uwsgi, 'version_info'):
            _logger.warning('The New Relic Python Agent requires version '
                    '1.2.6 or newer of uWSGI. The newer '
                    'version is required because older versions of uWSGI '
                    'have a bug whereby it is not compliant with the WSGI '
                    '(PEP 333) specification. This bug in uWSGI will result '
                    'in data being reported incorrectly. For more details see '
                    'https://newrelic.com/docs/python/python-agent-and-uwsgi.')
        elif ((hasattr(uwsgi, 'version_info') and
                  uwsgi.version_info[:3] < (1, 2, 6))):
            _logger.warning('The New Relic Python Agent requires version '
                    '1.2.6 or newer of uWSGI, you are using %r. The newer '
                    'version is required because older versions of uWSGI '
                    'have a bug whereby it is not compliant with the WSGI '
                    '(PEP 333) specification. This bug in uWSGI will result '
                    'in data being reported incorrectly. For more details see '
                    'https://newrelic.com/docs/python/python-agent-and-uwsgi.',
                    '.'.join(map(str, uwsgi.version_info[:3])))

        if not uwsgi.opt.get('enable-threads'):
            _logger.warning('The New Relic Python Agent requires that when '
                    'using uWSGI that the enable-threads option be given '
                    'to uwsgi when it is run. If the option is not supplied '
                    'then threading will not be enabled and you will see no '
                    'data being reported by the agent. For more details see '
                    'https://newrelic.com/docs/python/python-agent-and-uwsgi.')

class Agent(object):

    """Only one instance of the agent should ever exist and that can be
    obtained using the agent_instance() function.

    The licence key information, network connection details for the
    collector, plus whether SSL should be used is obtained directly from
    the global configuration settings. If a proxy has to be used, details
    for that will similarly come from the global configuration settings.

    The global configuration settings would normally be setup from the
    agent configuration file or could also be set explicitly. Direct access
    to global configuration setings prior to the agent instance being
    created needs to be via the 'newrelic.core.config' module.

    After the network connection details have been set, and the agent
    object created and accessed using the agent_instance() function, each
    individual reporting application can be activated using the
    activate_application() method of the agent. The name of the primary
    application and an optional list of linked applications to which metric
    data should also be reported needs to be supplied.

    Once an application has been activated and communications established
    with the core application, the application specific settings, which
    consists of the global default configuration settings overlaid with the
    server side configuration settings can be obtained using the
    application_settings() method. That a valid settings object rather than
    None is returned is the indicator that the application has been
    successfully activated. The application settings object can be
    associated with a transaction so that settings are available for the
    life of the transaction, but should not be cached and used across
    transactions. Instead the application settings object should be
    requested on each transaction to ensure that it is detected whether
    application is still active or not due to a server side triggered
    restart. When such a restart occurs, the application settings could
    change and thus why application settings cannot be cached beyond the
    lifetime of a single transaction.

    """

    _instance_lock = threading.Lock()
    _instance = None
    _startup_callables = []
    _registration_callables = {}

    @staticmethod
    def run_on_startup(callable):
        Agent._startup_callables.append(callable)

    @staticmethod
    def run_on_registration(application, callable):
        callables = Agent._registration_callables.setdefault(application, [])
        callables.append(callable)

    @staticmethod
    def agent_singleton():
        """Used by the agent_instance() function to access/create the
        single agent object instance.

        """

        if Agent._instance:
            return Agent._instance

        settings = newrelic.core.config.global_settings()

        # Just in case that the main initialisation function
        # wasn't called to read in a configuration file and as
        # such the logging system was not initialised already,
        # we trigger initialisation again here.

        initialize_logging(settings.log_file, settings.log_level)

        _logger.info('New Relic Python Agent (%s)' % newrelic.version)

        check_environment()

        if 'NEW_RELIC_ADMIN_COMMAND' in os.environ:
            if settings.debug.log_agent_initialization:
                _logger.info('Monitored application started using the '
                        'newrelic-admin command with command line of %s.',
                        os.environ['NEW_RELIC_ADMIN_COMMAND'])
            else:
                _logger.debug('Monitored application started using the '
                        'newrelic-admin command with command line of %s.',
                        os.environ['NEW_RELIC_ADMIN_COMMAND'])

        instance = None

        with Agent._instance_lock:
            if not Agent._instance:
                if settings.debug.log_agent_initialization:
                    _logger.info('Creating instance of Python agent in '
                            'process %d.', os.getpid())
                    _logger.info('Agent was initialized from: %r',
                            ''.join(traceback.format_stack()[:-1]))
                else:
                    _logger.debug('Creating instance of Python agent in '
                            'process %d.', os.getpid())
                    _logger.debug('Agent was initialized from: %r',
                            ''.join(traceback.format_stack()[:-1]))

                instance = Agent(settings)

                Agent._instance = instance

            if instance:
                _logger.debug('Activating agent instance.')

                instance.activate_agent()

                _logger.debug('Registering builtin data sources.')

                instance.register_data_source(cpu_usage_data_source)
                instance.register_data_source(memory_usage_data_source)
                instance.register_data_source(thread_utilization_data_source)

                for callable in Agent._startup_callables:
                    callable()

        return Agent._instance

    def __init__(self, config):
        """Initialises the agent and attempt to establish a connection
        to the core application. Will start the harvest loop running but
        will not activate any applications.

        """

        _logger.debug('Initializing Python agent.')

        self._creation_time = time.time()
        self._process_id = os.getpid()

        self._applications = {}
        self._config = config

        self._harvest_thread = threading.Thread(target=self._harvest_loop,
                name='NR-Harvest-Thread')
        self._harvest_thread.setDaemon(True)
        self._harvest_shutdown = threading.Event()

        self._harvest_count = 0
        self._last_harvest = 0.0
        self._harvest_duration = 0.0
        self._next_harvest = 0.0

        self._process_shutdown = False

        self._lock = threading.Lock()

        if self._config.enabled:
            atexit.register(self._atexit_shutdown)

            # Register an atexit hook for uwsgi to facilitate the graceful
            # reload of workers. This is necessary for uwsgi with gevent
            # workers, since the graceful reload waits for all greenlets to
            # join, but our NR background greenlet will never join since it has
            # to stay alive indefinitely. But if we register our agent shutdown
            # to the uwsgi's atexit hook, then the reload will trigger the
            # atexit hook, thus shutting down our agent thread. We should
            # append our atexit hook to any pre-existing ones to prevent
            # overwriting them.

            if 'uwsgi' in sys.modules:
                import uwsgi
                uwsgi_original_atexit_callback = getattr(uwsgi, 'atexit', None)

                def uwsgi_atexit_callback():
                    self._atexit_shutdown()
                    if uwsgi_original_atexit_callback:
                        uwsgi_original_atexit_callback()

                uwsgi.atexit = uwsgi_atexit_callback

        self._data_sources = {}

    def dump(self, file):
        """Dumps details about the agent to the file object."""

        print >> file, 'Time Created: %s' % (
                time.asctime(time.localtime(self._creation_time)))
        print >> file, 'Initialization PID: %s' % (
                self._process_id)
        print >> file, 'Harvest Count: %d' % (
                self._harvest_count)
        print >> file, 'Last Harvest: %s' % (
                time.asctime(time.localtime(self._last_harvest)))
        print >> file, 'Harvest Duration: %.2f' % (
                self._harvest_duration)
        print >> file, 'Next Harvest: %s' % (
                time.asctime(time.localtime(self._next_harvest)))
        print >> file, 'Agent Shutdown: %s' % (
                self._harvest_shutdown.isSet())
        print >> file, 'Applications: %r' % (
                sorted(self._applications.keys()))

    def global_settings(self):
        """Returns the global default settings object. If access is
        needed to this prior to initialising the agent, use the
        'newrelic.core.config' module directly.

        """

        return newrelic.core.config.global_settings()

    def application_settings(self, app_name):
        """Returns the application specific settings object. This only
        returns a valid settings object once a connection has been
        established to the core application and the application server
        side settings have been obtained. If this returns None then
        activate_application() should be used to force activation for
        the agent in case that hasn't been done previously.

        """

        application = self._applications.get(app_name)

        if application:
            return application.configuration

    def application_attribute_filter(self, app_name):
        """Returns the attribute filter for the application."""

        application = self._applications.get(app_name)
        if application:
            return application.attribute_filter

    def activate_application(self, app_name, linked_applications=[],
                             timeout=None):
        """Initiates activation for the named application if this has
        not been done previously. If an attempt to trigger the
        activation of the application has already been performed,
        whether or not that has completed, calling this again will
        have no affect.

        The list of linked applications is the additional applications
        to which data should also be reported in addition to the primary
        application.

        The timeout is how long to wait for the initial connection. The
        timeout only applies the first time a specific named application
        is being activated. The timeout would be used by test harnesses
        and can't really be used by activation of application for first
        request because it could take a second or more for initial
        handshake to get back configuration settings for application.

        """

        if not self._config.enabled:
            return

        # If timeout not supplied then use default from the global
        # configuration. Note that the timeout only applies on the first
        # call to activate the application.

        settings = newrelic.core.config.global_settings()

        if timeout is None:
            timeout = settings.startup_timeout

        activate_session = False

        with self._lock:
            application = self._applications.get(app_name, None)
            if not application:
                if settings.debug.log_agent_initialization:
                    _logger.info('Creating application instance for %r '
                            'in process %d.', app_name, os.getpid())
                    _logger.info('Application was activated from: %r',
                            ''.join(traceback.format_stack()[:-1]))
                else:
                    _logger.debug('Creating application instance for %r '
                            'in process %d.', app_name, os.getpid())
                    _logger.debug('Application was activated from: %r',
                            ''.join(traceback.format_stack()[:-1]))

                linked_applications = sorted(set(linked_applications))
                application = newrelic.core.application.Application(
                        app_name, linked_applications)
                self._applications[app_name] = application
                activate_session = True

                # Register any data sources with the application.

                for source, name, settings, properties in \
                        self._data_sources.get(None, []):
                    application.register_data_source(source, name,
                            settings, **properties)

                for source, name, settings, properties in \
                        self._data_sources.get(app_name, []):
                    application.register_data_source(source, name,
                            settings, **properties)

            else:
                # Do some checks to see whether try to reactivate the
                # application in a different process to what it was
                # originally activated in.

                application.validate_process()

        # Activate the session if application was just created and wait
        # for session activation if a timeout was specified. This may
        # bail out early if is detected that a deadlock may occur for
        # the period of the timeout.

        if activate_session:
            application.activate_session(timeout)

    @property
    def applications(self):
        """Returns a dictionary of the internal application objects
        corresponding to the applications for which activation has already
        been requested. This does not reflect whether activation has been
        successful or not. To determine if application is currently in an
        activated state use application_settings() method to see if a valid
        application settings objects is available or query the application
        object directly.

        """

        return self._applications

    def application(self, app_name):
        """Returns the internal application object for the named
        application or None if not created. When an application object
        is returned, it does not relect whether activation has been
        successful or not. To determine if application is currently in an
        activated state use application_settings() method to see if a valid
        application settings objects is available or query the application
        object directly.

        """

        return self._applications.get(app_name, None)

    def register_data_source(self, source, application=None,
                name=None, settings=None, **properties):
        """Registers the specified data source.

        """

        _logger.debug('Register data source with agent %r.',
                (source, application, name, settings, properties))

        with self._lock:
            # Remember the data sources in case we need them later.

            self._data_sources.setdefault(application, []).append(
                    (source, name, settings, properties))

            if application is None:
                # Bind to any applications that already exist.

                for application in list(six.itervalues(self._applications)):
                    application.register_data_source(source, name,
                            settings, **properties)

            else:
                # Bind to specific application if it exists.

                instance = self._applications.get(application)

                if instance is not None:
                    instance.register_data_source(source, name,
                            settings, **properties)

    def remove_thread_utilization(self):

        _logger.debug('Removing thread utilization data source from all '
                'applications')

        source_name = thread_utilization_data_source.__name__
        factory_name = 'Thread Utilization'

        with self._lock:
            source_names = [s[0].__name__ for s in self._data_sources[None]]
            if source_name in source_names:
                idx = source_names.index(source_name)
                self._data_sources[None].pop(idx)

            # Clear out the data samplers that add thread utilization custom
            # metrics every harvest (for each application)

            for application in self._applications.values():
                application.remove_data_source(factory_name)

        # The thread utilization data source may have been started, so we
        # must clear out the list of trackers that transactions will use to add
        # thread.concurrency attributes

        from newrelic.core.thread_utilization import _utilization_trackers
        _utilization_trackers.clear()

    def record_exception(self, app_name, exc=None, value=None, tb=None,
            params={}, ignore_errors=[]):

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_exception(exc, value, tb, params, ignore_errors)

    def record_custom_metric(self, app_name, name, value):
        """Records a basic metric for the named application. If there has
        been no prior request to activate the application, the metric is
        discarded.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_metric(name, value)

    def record_metric(self, app_name, name, value):
        warnings.warn('Internal API change. Use record_custom_metric() '
                'instead of record_metric().', DeprecationWarning,
                stacklevel=2)

        return self.record_custom_metric(app_name, name, value)

    def record_custom_metrics(self, app_name, metrics):
        """Records the metrics for the named application. If there has
        been no prior request to activate the application, the metric is
        discarded. The metrics should be an iterable yielding tuples
        consisting of the name and value.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_metrics(metrics)

    def record_custom_event(self, app_name, event_type, params):
        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_custom_event(event_type, params)

    def record_metrics(self, app_name, metrics):
        warnings.warn('Internal API change. Use record_custom_metrics() '
                'instead of record_metrics().', DeprecationWarning,
                stacklevel=2)

        return self.record_custom_metrics(app_name, metrics)

    def record_transaction(self, app_name, data, profile_samples=None):
        """Processes the raw transaction data, generating and recording
        appropriate metrics against the named application. If there has
        been no prior request to activate the application, the metric is
        discarded.

        """

        application = self._applications.get(app_name, None)
        if application is None or not application.active:
            return

        application.record_transaction(data, profile_samples)

    def normalize_name(self, app_name, name, rule_type='url'):
        application = self._applications.get(app_name, None)
        if application is None:
            return name, False

        return application.normalize_name(name, rule_type)

    def _harvest_loop(self):
        _logger.debug('Entering harvest loop.')

        settings = newrelic.core.config.global_settings()

        self._next_harvest = time.time()

        try:
            while True:
                if self._harvest_shutdown.isSet():
                    # NOTE We would have just finished a harvest or only
                    # just started the agent, so we could skip doing a
                    # forced harvest, or at least if most recent harvest
                    # was started within in certain period of time. The
                    # chances of it occuring are probably slim enough
                    # that is not an issue.

                    self._run_harvest(shutdown=True)

                    return

                # We are either going into the loop the first time, or
                # something really went wrong here and we are overdue
                # already for next harvest. This can happen when we have
                # a large number of applications. Can also happen if
                # clock is changed significantly. Skip it and wait until
                # the next harvest time instead.
                #
                # NOTE This does mean that we aren't going to report on
                # 1 minute intervals when have lots of applications. We
                # need to look at using multiple threads when have lots
                # of applications. Also need to fix problem whereby one
                # all applications created, that only the first
                # application will reliably report on an even minute as
                # when the others report will depend on how long the
                # first takes.

                now = time.time()
                while self._next_harvest <= now:
                    self._next_harvest += 60.0

                # Wait until next harvest period but drop out and force
                # harvest if been notified that process is being
                # shutdown.

                delay = self._next_harvest - now
                self._harvest_shutdown.wait(delay)

                if self._harvest_shutdown.isSet():
                    # Force a final harvest on agent shutdown.

                    self._run_harvest(shutdown=True)

                    return

                # Run the normal harvest cycle.

                self._run_harvest(shutdown=False)

        except Exception:
            # An unexpected error, possibly some sort of internal agent
            # implementation issue or more likely due to modules being
            # destroyed from the main thread on process exit when the
            # background harvest thread is still running.

            if self._process_shutdown:
                _logger.exception('Unexpected exception in main harvest '
                        'loop when process being shutdown. This can occur '
                        'in rare cases due to the main thread cleaning up '
                        'and destroying objects while the background harvest '
                        'thread is still running. If this message occurs '
                        'rarely, it can be ignored. If the message occurs '
                        'on a regular basis, then please report it to New '
                        'Relic support for further investigation.')

            else:
                _logger.exception('Unexpected exception in main harvest '
                        'loop. Please report this problem to New Relic '
                        'support for further investigation.')

    def _run_harvest(self, shutdown=False):
        # This isn't going to maintain order of applications
        # such that oldest is always done first. A new one could
        # come in earlier once added and upset the overall
        # timing. The data collector should cope with this
        # though.

        if shutdown:
            _logger.debug('Commencing harvest of all application data and '
                    'forcing a shutdown at the same time.')
        else:
            _logger.debug('Commencing harvest of all application data.')

        self._harvest_count += 1
        self._last_harvest = time.time()

        for application in list(six.itervalues(self._applications)):
              try:
                  application.harvest(shutdown)

              except Exception:
                  _logger.exception('Failed to harvest data '
                                    'for %s.' % application.name)

        self._harvest_duration = time.time() - self._last_harvest

        _logger.debug('Completed harvest of all application data in %.2f '
                'seconds.', self._harvest_duration)

    def activate_agent(self):
        """Starts the main background for the agent."""

        # Skip this if agent is not actually enabled.

        if not self._config.enabled:
            _logger.warning('The Python Agent is not enabled.')
            return

        # Skip this if background thread already running.

        if self._harvest_thread.isAlive():
            return

        _logger.debug('Start Python Agent main thread.')

        self._harvest_thread.start()

    def _atexit_shutdown(self):
        """Triggers agent shutdown but flags first that this is being
        done because process is being shutdown.

        """

        self._process_shutdown = True
        self.shutdown_agent()

    def shutdown_agent(self, timeout=None):
        if self._harvest_shutdown.isSet():
            return

        if timeout is None:
            timeout = self._config.shutdown_timeout

        _logger.info('New Relic Python Agent Shutdown')

        self._harvest_shutdown.set()
        self._harvest_thread.join(timeout)

def agent_instance():
    """Returns the agent object. This function should always be used and
    instances of the agent object should never be created directly to
    ensure there is only ever one instance.

    Network connection details and the licence key needed to initialise the
    agent must have been set in the global default configuration settings
    prior to the first call of this function.

    """

    return Agent.agent_singleton()

def agent():
   warnings.warn('Internal API change. Use agent_instance() '
           'instead of agent().', DeprecationWarning, stacklevel=2)

   return agent_instance()

def shutdown_agent(timeout=None):
    agent = agent_instance()
    agent.shutdown_agent(timeout)

def register_data_source(source, application=None, name=None,
        settings=None, **properties):
    agent = agent_instance()
    agent.register_data_source(source,
            application and application.name or None, name, settings,
            **properties)

def _remove_thread_utilization():
    agent = agent_instance()
    agent.remove_thread_utilization()

def remove_thread_utilization():
    with Agent._instance_lock:
        if Agent._instance:
            _remove_thread_utilization()
        else:
            Agent.run_on_startup(_remove_thread_utilization)
