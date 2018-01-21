""" This module provides a structure to hang the configuration settings. We
use an empty class structure and manually populate it. The global defaults
will be overlaid with any settings from the local agent configuration file.
For a specific application we will then deep copy the global default
settings and then overlay that with application settings obtained from the
server side core application. Finally, to allow for local testing and
debugging, for selected override configuration settings, we will apply back
the global defaults or those from local agent configuration.

"""

import os
import logging
import copy

from newrelic.core.attribute_filter import AttributeFilter

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


# By default, Transaction Events and Custom Events have the same size
# reservoir. Error Events have a different default size.

DEFAULT_RESERVOIR_SIZE = 1200
ERROR_EVENT_RESERVOIR_SIZE = 100

# settings that should be completely ignored if set server side
IGNORED_SERVER_SIDE_SETTINGS = ['utilization.logical_processors',
        'utilization.total_ram_mib', 'utilization.billing_hostname']


class _NullHandler(logging.Handler):
    def emit(self, record):
        pass


_logger = logging.getLogger(__name__)
_logger.addHandler(_NullHandler())


# The Settings objects and the global default settings. We create a
# distinct type for each sub category of settings that the agent knows
# about so that an error when accessing a non existant setting is more
# descriptive and identifies the category of settings. When applying
# server side configuration we create normal Settings object for new
# sub categories we don't know about.

class Settings(object):
    def __repr__(self):
        return repr(self.__dict__)

    def __iter__(self):
        return iter(flatten_settings(self).items())

    def __contains__(self, item):
        return hasattr(self, item)


class AttributesSettings(Settings):
    pass


class ThreadProfilerSettings(Settings):
    pass


class TransactionTracerSettings(Settings):
    pass


class TransactionTracerAttributesSettings(Settings):
    pass


class ErrorCollectorSettings(Settings):
    pass


class ErrorCollectorAttributesSettings(Settings):
    pass


class BrowserMonitorSettings(Settings):
    pass


class BrowserMonitorAttributesSettings(Settings):
    pass


class TransactionNameSettings(Settings):
    pass


class TransactionMetricsSettings(Settings):
    pass


class RumSettings(Settings):
    pass


class SlowSqlSettings(Settings):
    pass


class AgentLimitsSettings(Settings):
    pass


class ConsoleSettings(Settings):
    pass


class DebugSettings(Settings):
    pass


class CrossApplicationTracerSettings(Settings):
    pass


class XraySessionSettings(Settings):
    pass


class TransactionEventsSettings(Settings):
    pass


class TransactionEventsAttributesSettings(Settings):
    pass


class CustomInsightsEventsSettings(Settings):
    pass


class ProcessHostSettings(Settings):
    pass


class SyntheticsSettings(Settings):
    pass


class MessageTracerSettings(Settings):
    pass


class UtilizationSettings(Settings):
    pass


class StripExceptionMessageSettings(Settings):
    pass


class DatastoreTracerSettings(Settings):
    pass


class DatastoreTracerInstanceReportingSettings(Settings):
    pass


class DatastoreTracerDatabaseNameReportingSettings(Settings):
    pass


class HerokuSettings(Settings):
    pass


_settings = Settings()
_settings.attributes = AttributesSettings()
_settings.thread_profiler = ThreadProfilerSettings()
_settings.transaction_tracer = TransactionTracerSettings()
_settings.transaction_tracer.attributes = TransactionTracerAttributesSettings()
_settings.error_collector = ErrorCollectorSettings()
_settings.error_collector.attributes = ErrorCollectorAttributesSettings()
_settings.browser_monitoring = BrowserMonitorSettings()
_settings.browser_monitoring.attributes = BrowserMonitorAttributesSettings()
_settings.transaction_name = TransactionNameSettings()
_settings.transaction_metrics = TransactionMetricsSettings()
_settings.rum = RumSettings()
_settings.slow_sql = SlowSqlSettings()
_settings.agent_limits = AgentLimitsSettings()
_settings.console = ConsoleSettings()
_settings.debug = DebugSettings()
_settings.cross_application_tracer = CrossApplicationTracerSettings()
_settings.xray_session = XraySessionSettings()
_settings.transaction_events = TransactionEventsSettings()
_settings.transaction_events.attributes = TransactionEventsAttributesSettings()
_settings.custom_insights_events = CustomInsightsEventsSettings()
_settings.process_host = ProcessHostSettings()
_settings.synthetics = SyntheticsSettings()
_settings.message_tracer = MessageTracerSettings()
_settings.utilization = UtilizationSettings()
_settings.strip_exception_messages = StripExceptionMessageSettings()
_settings.datastore_tracer = DatastoreTracerSettings()
_settings.datastore_tracer.instance_reporting = \
        DatastoreTracerInstanceReportingSettings()
_settings.datastore_tracer.database_name_reporting = \
        DatastoreTracerDatabaseNameReportingSettings()
_settings.heroku = HerokuSettings()

_settings.log_file = os.environ.get('NEW_RELIC_LOG', None)
_settings.audit_log_file = os.environ.get('NEW_RELIC_AUDIT_LOG', None)


def _environ_as_int(name, default=0):
    val = os.environ.get(name, default)
    try:
        return int(val)
    except ValueError:
        return default


def _environ_as_bool(name, default=False):
    flag = os.environ.get(name, default)
    if default is None or default:
        try:
            flag = not flag.lower() in ['off', 'false', '0']
        except AttributeError:
            pass
    else:
        try:
            flag = flag.lower() in ['on', 'true', '1']
        except AttributeError:
            pass
    return flag


def _environ_as_set(name, default=''):
    value = os.environ.get(name, default)
    return set(value.split())


def _environ_as_mapping(name, default=''):
    result = []
    items = os.environ.get(name, default)

    # Strip all whitespace and semicolons from the end of the string.
    # That way, when we split a valid labels string by ';', the resulting
    # list will contain no empty elements. When we loop through the
    # elements, if we see one that is empty, or can't be split by ':',
    # then we know the string has an invalid format.

    items = items.strip('; \t\n\r\f\v')

    if not items:
        return result

    for item in items.split(';'):

        try:
            key, value = item.split(':')
        except ValueError:
            _logger.warning('Invalid configuration. Cannot parse: %r.'
                    'Expected format \'key1:value1;key2:value2 ... \'.',
                     items)
            result = []
            break

        key = key.strip()
        value = value.strip()

        if key and value:
            result.append((key, value))
        else:
            _logger.warning('Invalid configuration. Cannot parse: %r.'
                    'Expected format \'key1:value1;key2:value2 ... \'.',
                     items)
            result = []
            break

    return result


def _parse_ignore_status_codes(value, target):
    items = value.split()
    for item in items:
        try:
            negate = item.startswith('!')
            if negate:
                item = item[1:]

            start, end = item.split('-')

            values = set(range(int(start), int(end) + 1))

            if negate:
                target.difference_update(values)
            else:
                target.update(values)

        except ValueError:
            if negate:
                target.discard(int(item))
            else:
                target.add(int(item))
    return target


def _parse_attributes(s):
    valid = []
    for item in s.split():
        if '*' not in item[:-1] and len(item.encode('utf-8')) < 256:
            valid.append(item)
        else:
            _logger.warning('Improperly formatted attribute: %r', item)
    return valid


_LOG_LEVEL = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

_settings.enabled = _environ_as_bool('NEW_RELIC_ENABLED', False)

_settings.feature_flag = _environ_as_set('NEW_RELIC_FEATURE_FLAG', '')

_settings.log_level = os.environ.get('NEW_RELIC_LOG_LEVEL', 'INFO').upper()

if _settings.log_level in _LOG_LEVEL:
    _settings.log_level = _LOG_LEVEL[_settings.log_level]
else:
    _settings.log_level = logging.INFO

_settings.license_key = os.environ.get('NEW_RELIC_LICENSE_KEY', None)
_settings.api_key = os.environ.get('NEW_RELIC_API_KEY', None)

_settings.ssl = _environ_as_bool('NEW_RELIC_SSL', True)

_settings.host = os.environ.get('NEW_RELIC_HOST', 'collector.newrelic.com')
_settings.port = int(os.environ.get('NEW_RELIC_PORT', '0'))

_settings.proxy_scheme = os.environ.get('NEW_RELIC_PROXY_SCHEME', None)
_settings.proxy_host = os.environ.get('NEW_RELIC_PROXY_HOST', None)
_settings.proxy_port = int(os.environ.get('NEW_RELIC_PROXY_PORT', '0'))
_settings.proxy_user = os.environ.get('NEW_RELIC_PROXY_USER', None)
_settings.proxy_pass = os.environ.get('NEW_RELIC_PROXY_PASS', None)

_settings.app_name = os.environ.get('NEW_RELIC_APP_NAME', 'Python Application')
_settings.linked_applications = []

_settings.process_host.display_name = os.environ.get(
        'NEW_RELIC_PROCESS_HOST_DISPLAY_NAME', None)

_settings.labels = _environ_as_mapping('NEW_RELIC_LABELS', '')

_settings.monitor_mode = _environ_as_bool('NEW_RELIC_MONITOR_MODE', True)

_settings.developer_mode = _environ_as_bool('NEW_RELIC_DEVELOPER_MODE', False)

_settings.high_security = _environ_as_bool('NEW_RELIC_HIGH_SECURITY', False)

_settings.attribute_filter = None

_settings.collect_errors = True
_settings.collect_error_events = True
_settings.collect_traces = True
_settings.collect_analytics_events = True
_settings.collect_custom_events = True

_settings.apdex_t = 0.5
_settings.web_transactions_apdex = {}

_settings.capture_params = None
_settings.ignored_params = []

_settings.capture_environ = True
_settings.include_environ = ['REQUEST_METHOD', 'HTTP_USER_AGENT',
                              'HTTP_REFERER', 'CONTENT_TYPE',
                              'CONTENT_LENGTH', 'HTTP_HOST', 'HTTP_ACCEPT']

_settings.max_stack_trace_lines = 50

_settings.sampling_rate = 0

_settings.startup_timeout = float(
       os.environ.get('NEW_RELIC_STARTUP_TIMEOUT', '0.0'))
_settings.shutdown_timeout = float(
       os.environ.get('NEW_RELIC_SHUTDOWN_TIMEOUT', '2.5'))

_settings.beacon = None
_settings.error_beacon = None
_settings.application_id = None
_settings.browser_key = None
_settings.episodes_url = None
_settings.js_agent_loader = None
_settings.js_agent_file = None

_settings.url_rules = []
_settings.metric_name_rules = []
_settings.transaction_name_rules = []
_settings.transaction_segment_terms = []

_settings.cross_process_id = None
_settings.trusted_account_ids = []
_settings.encoding_key = None

_settings.attributes.enabled = True
_settings.attributes.exclude = []
_settings.attributes.include = []

_settings.thread_profiler.enabled = True
_settings.cross_application_tracer.enabled = True
_settings.xray_session.enabled = True

_settings.transaction_events.enabled = True
_settings.transaction_events.max_samples_stored = DEFAULT_RESERVOIR_SIZE
_settings.transaction_events.attributes.enabled = True
_settings.transaction_events.attributes.exclude = []
_settings.transaction_events.attributes.include = []

_settings.custom_insights_events.enabled = True
_settings.custom_insights_events.max_samples_stored = DEFAULT_RESERVOIR_SIZE

_settings.transaction_tracer.enabled = True
_settings.transaction_tracer.transaction_threshold = None
_settings.transaction_tracer.record_sql = 'obfuscated'
_settings.transaction_tracer.stack_trace_threshold = 0.5
_settings.transaction_tracer.explain_enabled = True
_settings.transaction_tracer.explain_threshold = 0.5
_settings.transaction_tracer.function_trace = []
_settings.transaction_tracer.generator_trace = []
_settings.transaction_tracer.top_n = 20
_settings.transaction_tracer.attributes.enabled = True
_settings.transaction_tracer.attributes.exclude = []
_settings.transaction_tracer.attributes.include = []

_settings.error_collector.enabled = True
_settings.error_collector.capture_events = True
_settings.error_collector.max_event_samples_stored = ERROR_EVENT_RESERVOIR_SIZE
_settings.error_collector.capture_source = False
_settings.error_collector.ignore_errors = []
_settings.error_collector.ignore_status_codes = _parse_ignore_status_codes(
        '100-102 200-208 226 300-308 404', set())
_settings.error_collector.attributes.enabled = True
_settings.error_collector.attributes.exclude = []
_settings.error_collector.attributes.include = []

_settings.browser_monitoring.enabled = True
_settings.browser_monitoring.auto_instrument = True
_settings.browser_monitoring.loader = 'rum'  # Valid values: 'full', 'none'
_settings.browser_monitoring.loader_version = None
_settings.browser_monitoring.debug = False
_settings.browser_monitoring.ssl_for_http = None
_settings.browser_monitoring.content_type = ['text/html']
_settings.browser_monitoring.attributes.enabled = False
_settings.browser_monitoring.attributes.exclude = []
_settings.browser_monitoring.attributes.include = []

_settings.transaction_name.limit = None
_settings.transaction_name.naming_scheme = os.environ.get(
        'NEW_RELIC_TRANSACTION_NAMING_SCHEME')

_settings.slow_sql.enabled = True

_settings.synthetics.enabled = True

_settings.agent_limits.data_collector_timeout = 30.0
_settings.agent_limits.transaction_traces_nodes = 2000
_settings.agent_limits.sql_query_length_maximum = 16384
_settings.agent_limits.slow_sql_stack_trace = 30
_settings.agent_limits.max_sql_connections = 4
_settings.agent_limits.sql_explain_plans = 30
_settings.agent_limits.sql_explain_plans_per_harvest = 60
_settings.agent_limits.slow_sql_data = 10
_settings.agent_limits.merge_stats_maximum = 5
_settings.agent_limits.errors_per_transaction = 5
_settings.agent_limits.errors_per_harvest = 20
_settings.agent_limits.slow_transaction_dry_harvests = 5
_settings.agent_limits.thread_profiler_nodes = 20000
_settings.agent_limits.xray_transactions = 10
_settings.agent_limits.xray_profile_overhead = 0.05
_settings.agent_limits.xray_profile_maximum = 500
_settings.agent_limits.synthetics_events = 200
_settings.agent_limits.synthetics_transactions = 20
_settings.agent_limits.data_compression_threshold = 64 * 1024
_settings.agent_limits.data_compression_level = None
_settings.agent_limits.max_outstanding_traces = 100

_settings.console.listener_socket = None
_settings.console.allow_interpreter_cmd = False

_settings.debug.ignore_all_server_settings = False
_settings.debug.local_settings_overrides = []

_settings.debug.disable_api_supportability_metrics = False
_settings.debug.log_agent_initialization = False
_settings.debug.log_data_collector_calls = False
_settings.debug.log_data_collector_payloads = False
_settings.debug.log_malformed_json_data = False
_settings.debug.log_transaction_trace_payload = False
_settings.debug.log_thread_profile_payload = False
_settings.debug.log_normalization_rules = False
_settings.debug.log_raw_metric_data = False
_settings.debug.log_normalized_metric_data = False
_settings.debug.log_explain_plan_queries = False
_settings.debug.log_autorum_middleware = False
_settings.debug.record_transaction_failure = False
_settings.debug.enable_coroutine_profiling = False
_settings.debug.explain_plan_obfuscation = 'simple'
_settings.debug.disable_certificate_validation = False

_settings.message_tracer.segment_parameters_enabled = True

_settings.utilization.detect_aws = True
_settings.utilization.detect_azure = True
_settings.utilization.detect_docker = True
_settings.utilization.detect_gcp = True
_settings.utilization.detect_pcf = True

_settings.utilization.logical_processors = _environ_as_int(
        'NEW_RELIC_UTILIZATION_LOGICAL_PROCESSORS')
_settings.utilization.total_ram_mib = _environ_as_int(
        'NEW_RELIC_UTILIZATION_TOTAL_RAM_MIB')
_settings.utilization.billing_hostname = os.environ.get(
        'NEW_RELIC_UTILIZATION_BILLING_HOSTNAME')

_settings.strip_exception_messages.enabled = False
_settings.strip_exception_messages.whitelist = []

_settings.datastore_tracer.instance_reporting.enabled = True
_settings.datastore_tracer.database_name_reporting.enabled = True

_settings.heroku.use_dyno_names = _environ_as_bool(
        'NEW_RELIC_HEROKU_USE_DYNO_NAMES', default=True)
_settings.heroku.dyno_name_prefixes_to_shorten = list(_environ_as_set(
        'NEW_RELIC_HEROKU_DYNO_NAME_PREFIXES_TO_SHORTEN', 'scheduler run'))


def global_settings():
    """This returns the default global settings. Generally only used
    directly in test scripts and test harnesses or when applying global
    settings from agent configuration file. Making changes to the settings
    object returned by this function will not have any effect on any
    applications that have already been initialised. This is because when
    the settings are obtained from the core application a snapshot of these
    settings will be taken.

    >>> global_settings = global_settings()
    >>> global_settings.browser_monitoring.auto_instrument = True
    >>> global_settings.browser_monitoring.auto_instrument
    True

    """

    return _settings


def flatten_settings(settings):
    """This returns dictionary of settings flattened into a single
    key namespace rather than nested hierarchy.

    """

    def _flatten(settings, name, object):
        for key, value in object.__dict__.items():
            if isinstance(value, Settings):
                if name:
                    _flatten(settings, '%s.%s' % (name, key), value)
                else:
                    _flatten(settings, key, value)
            else:
                if name:
                    settings['%s.%s' % (name, key)] = value
                else:
                    settings[key] = value

        return settings

    return _flatten({}, None, settings)


def create_obfuscated_netloc(username, password, hostname, mask):
    """Create a netloc string from hostname, username and password. If the
    username and/or password is present, replace them with the obfuscation
    mask. Otherwise, leave them out of netloc.

    """

    if username:
        username = mask

    if password:
        password = mask

    if username and password:
        netloc = '%s:%s@%s' % (username, password, hostname)
    elif username:
        netloc = '%s@%s' % (username, hostname)
    else:
        netloc = hostname

    return netloc


def global_settings_dump(settings_object=None):
    """This returns dictionary of global settings flattened into a single
    key namespace rather than nested hierarchy. This is used to send the
    global settings configuration back to core application.

    """

    if settings_object is None:
        settings_object = _settings

    settings = flatten_settings(settings_object)

    # Strip out any sensitive settings as can be sent unencrypted.
    # The license key is being sent already, but no point sending
    # it again.

    del settings['license_key']
    del settings['api_key']

    # If proxy credentials are included in the settings, we obfuscate
    # them before sending, rather than deleting.

    obfuscated = '****'

    if settings['proxy_user'] is not None:
        settings['proxy_user'] = obfuscated

    if settings['proxy_pass'] is not None:
        settings['proxy_pass'] = obfuscated

    # For the case of proxy_host we have to do a bit more work as it
    # could be a URI which includes the username and password within
    # it. What we do here is parse the value and if identified as a
    # URI, we recompose it with the obfuscated username and password.

    proxy_host = settings['proxy_host']

    if proxy_host:
        components = urlparse.urlparse(proxy_host)

        if components.scheme:

            netloc = create_obfuscated_netloc(components.username,
                    components.password, components.hostname, obfuscated)

            if components.port:
                uri = '%s://%s:%s%s' % (components.scheme, netloc,
                        components.port, components.path)
            else:
                uri = '%s://%s%s' % (components.scheme, netloc,
                        components.path)

            settings['proxy_host'] = uri

    return settings


# Creation of an application settings object from global default settings
# and any server side configuration settings.

def apply_config_setting(settings_object, name, value):
    """Apply a setting to the settings object where name is a dotted path.
    If there is no pre existing settings object for a sub category then
    one will be created and added automatically.

    >>> name = 'browser_monitoring.auto_instrument'
    >>> value = True
    >>>
    >>> global_settings = global_settings()
    >>> apply_config_setting(global_settings, name, value)

    """

    target = settings_object
    fields = name.split('.', 1)

    while len(fields) > 1:
        if not hasattr(target, fields[0]):
            setattr(target, fields[0], Settings())
        target = getattr(target, fields[0])
        fields = fields[1].split('.', 1)

    setattr(target, fields[0], value)


def fetch_config_setting(settings_object, name):
    """Fetch a setting from the settings object where name is a dotted path.

    >>> name = 'browser_monitoring.auto_instrument'
    >>>
    >>> global_settings = global_settings()
    >>> global_settings.browser_monitoring.auto_instrument = True
    >>> fetch_config_setting(global_settings, name)
    True

    """

    target = settings_object
    fields = name.split('.', 1)

    target = getattr(target, fields[0])

    while len(fields) > 1:
        fields = fields[1].split('.', 1)
        target = getattr(target, fields[0])

    return target


def apply_server_side_settings(server_side_config={}, settings=_settings):
    """Create a snapshot of the global default settings and overlay it
    with any server side configuration settings. Any local settings
    overrides to take precedence over server side configuration settings
    will then be reapplied to the copy. Note that the intention is that
    the resulting settings object will be cached for subsequent use
    within the application object the settings pertain to.

    >>> server_config = {'browser_monitoring.auto_instrument': True}
    >>>
    >>> settings_snapshot = apply_server_side_settings(server_config)

    """

    settings_snapshot = copy.deepcopy(settings)

    # Break out the server side agent config settings which
    # are stored under 'agent_config' key.

    agent_config = server_side_config.pop('agent_config', {})

    # Remap as necessary any server side agent config settings.

    if 'transaction_tracer.transaction_threshold' in agent_config:
        value = agent_config['transaction_tracer.transaction_threshold']
        if value == 'apdex_f':
            agent_config['transaction_tracer.transaction_threshold'] = None

    # Overlay with global server side configuration settings.

    for (name, value) in server_side_config.items():
        apply_config_setting(settings_snapshot, name, value)

    # Overlay with agent server side configuration settings.
    # Assuming for now that agent service side configuration
    # can always take precedence over the global server side
    # configuration settings.

    for (name, value) in agent_config.items():
        apply_config_setting(settings_snapshot, name, value)

    # Reapply on top any local setting overrides.

    for name in _settings.debug.local_settings_overrides:
        value = fetch_config_setting(_settings, name)
        apply_config_setting(settings_snapshot, name, value)

    return settings_snapshot


def finalize_application_settings(server_side_config={}, settings=_settings):
    """Overlay server-side settings and add attribute filter."""

    # Remove values from server_config that should not overwrite the
    # ones set locally
    server_side_config = _remove_ignored_configs(server_side_config)

    application_settings = apply_server_side_settings(
            server_side_config, settings)

    application_settings.attribute_filter = AttributeFilter(
            flatten_settings(application_settings))

    return application_settings


def _remove_ignored_configs(server_settings):
    if not server_settings.get('agent_config'):
        return server_settings

    # These settings should be ignored completely
    for ignored_setting in IGNORED_SERVER_SIDE_SETTINGS:
        server_settings['agent_config'].pop(ignored_setting, None)

    return server_settings


def ignore_status_code(status):
    return status in _settings.error_collector.ignore_status_codes
