import threading
import warnings

import newrelic.core.config
import newrelic.core.agent

import newrelic.packages.six as six

class Application(object):

    _lock = threading.Lock()
    _instances = {}

    _delayed_callables = {}

    @staticmethod
    def _instance(name):
        if name is None:
            name = newrelic.core.config.global_settings().app_name

        # Ensure we grab a reference to the agent before grabbing
        # the lock, else startup callback on agent initialisation
        # could deadlock as it tries to create a application when
        # we already have the lock held.

        agent = newrelic.core.agent.agent_instance()

        # Try first without lock. If we find it we can return.

        instance = Application._instances.get(name, None)

        if not instance:
            with Application._lock:
                # Now try again with lock so that only one gets
                # to create and add it.

                instance = Application._instances.get(name, None)
                if not instance:
                    instance = Application(name, agent)
                    Application._instances[name] = instance

        return instance

    @staticmethod
    def run_on_initialization(name, callback):
        Application._delayed_callables[name] = callback

    def __init__(self, name, agent=None):
        self._name = name
        self._linked = {}
        self.enabled = True

        if agent is None:
            agent = newrelic.core.agent.agent_instance()

        self._agent = agent

        callback = Application._delayed_callables.get(name)
        if callback:
            callback(self)

    @property
    def name(self):
        return self._name

    @property
    def global_settings(self):
        return self._agent.global_settings()

    @property
    def settings(self):
        global_settings = self._agent.global_settings()
        if global_settings.debug.ignore_all_server_settings:
            return global_settings
        return self._agent.application_settings(self._name)

    @property
    def active(self):
        return self.settings is not None

    def activate(self, timeout=None):
        # If timeout not supplied then the default from the global
        # configuration will later be used. Note that the timeout only
        # applies on the first call to activate the application.

        self._agent.activate_application(self._name, self._linked, timeout)

    def shutdown(self):
        pass

    @property
    def linked_applications(self):
        return list(six.iterkeys(self._linked))

    def link_to_application(self, name):
        self._linked[name] = True

    def record_exception(self, exc=None, value=None, tb=None, params={},
            ignore_errors=[]):

        if not self.active:
            return

        self._agent.record_exception(self._name, exc, value, tb, params,
                ignore_errors)

    def record_custom_metric(self, name, value):
        if self.active:
            self._agent.record_custom_metric(self._name, name, value)

    def record_metric(self, name, value):
        warnings.warn('Internal API change. Use record_custom_metric() '
                'instead of record_metric().', DeprecationWarning,
                stacklevel=2)

        return self.record_custom_metric(name, value)

    def record_custom_metrics(self, metrics):
        if self.active and metrics:
            self._agent.record_custom_metrics(self._name, metrics)

    def record_custom_event(self, event_type, params):
        if self.active:
            self._agent.record_custom_event(self._name, event_type, params)

    def record_metrics(self, metrics):
        warnings.warn('Internal API change. Use record_custom_metrics() '
                'instead of record_metrics().', DeprecationWarning,
                stacklevel=2)

        return self.record_custom_metrics(metrics)

    def record_transaction(self, data, profile_samples=None):
        if self.active:
            self._agent.record_transaction(self._name, data, profile_samples)

    def normalize_name(self, name, rule_type='url'):
        if self.active:
            return self._agent.normalize_name(self._name, name, rule_type)
        return name, False

def application_instance(name=None):
    return Application._instance(name)

def application():
   warnings.warn('Internal API change. Use application_instance() '
           'instead of application().', DeprecationWarning, stacklevel=2)

   return application_instance()

def register_application(name=None, timeout=None):
    instance = application_instance(name)
    instance.activate(timeout)
    return instance

def application_settings(name=None):
    instance = application_instance(name)
    return instance.settings
