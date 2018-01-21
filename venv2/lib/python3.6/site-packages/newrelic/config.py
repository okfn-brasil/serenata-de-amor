import os
import sys
import logging
import traceback
import warnings

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from newrelic.packages import six

from newrelic.common.log_file import initialize_logging
from newrelic.common.object_names import expand_builtin_exception_name
from newrelic.core.config import (Settings, apply_config_setting,
        fetch_config_setting)

import newrelic.core.agent
import newrelic.core.config

import newrelic.api.settings
import newrelic.api.import_hook
import newrelic.api.exceptions
import newrelic.api.web_transaction
import newrelic.api.background_task
import newrelic.api.database_trace
import newrelic.api.external_trace
import newrelic.api.function_trace
import newrelic.api.generator_trace
import newrelic.api.profile_trace
import newrelic.api.memcache_trace
import newrelic.api.transaction_name
import newrelic.api.error_trace
import newrelic.api.function_profile
import newrelic.api.object_wrapper
import newrelic.api.application

import newrelic.console

__all__ = ['initialize', 'filter_app_factory']

_logger = logging.getLogger(__name__)

# Register our importer which implements post import hooks for
# triggering of callbacks to monkey patch modules before import
# returns them to caller.

sys.meta_path.insert(0, newrelic.api.import_hook.ImportHookFinder())

# The set of valid feature flags that the agent currently uses.
# This will be used to validate what is provided and issue warnings
# if feature flags not in set are provided.

_FEATURE_FLAGS = set([
    'tornado.instrumentation.r1',
    'tornado.instrumentation.r2',
    'tornado.instrumentation.r3',
    'tornado.instrumentation.r4',
    'django.instrumentation.inclusion-tags.r1',
])

# Names of configuration file and deployment environment. This
# will be overridden by the load_configuration() function when
# configuration is loaded.

_config_file = None
_environment = None
_ignore_errors = True

# This is the actual internal settings object. Options which
# are read from the configuration file will be applied to this.

_settings = newrelic.api.settings.settings()

# Use the raw config parser as we want to avoid interpolation
# within values. This avoids problems when writing lambdas
# within the actual configuration file for options which value
# can be dynamically calculated at time wrapper is executed.
# This configuration object can be used by the instrumentation
# modules to look up customised settings defined in the loaded
# configuration file.

_config_object = ConfigParser.RawConfigParser()

# Cache of the parsed global settings found in the configuration
# file. We cache these so can dump them out to the log file once
# all the settings have been read.

_cache_object = []

# Mechanism for extracting settings from the configuration for use in
# instrumentation modules and extensions.


def extra_settings(section, types={}, defaults={}):
    settings = {}

    if _config_object.has_section(section):
        settings.update(_config_object.items(section))

    settings_object = Settings()

    for name, value in defaults.items():
        apply_config_setting(settings_object, name, value)

    for name, value in settings.items():
        if name in types:
            value = types[name](value)

        apply_config_setting(settings_object, name, value)

    return settings_object


# Define some mapping functions to convert raw values read from
# configuration file into the internal types expected by the
# internal configuration settings object.

_LOG_LEVEL = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

_RECORD_SQL = {
    "off": newrelic.api.settings.RECORDSQL_OFF,
    "raw": newrelic.api.settings.RECORDSQL_RAW,
    "obfuscated": newrelic.api.settings.RECORDSQL_OBFUSCATED,
}


def _map_log_level(s):
    return _LOG_LEVEL[s.upper()]


def _map_feature_flag(s):
    return set(s.split())


def _map_labels(s):
    return newrelic.core.config._environ_as_mapping(name='', default=s)


def _map_transaction_threshold(s):
    if s == 'apdex_f':
        return None
    return float(s)


def _map_record_sql(s):
    return _RECORD_SQL[s]


def _map_split_strings(s):
    return s.split()


def _map_console_listener_socket(s):
    return s % {'pid': os.getpid()}


def _merge_ignore_status_codes(s):
    return newrelic.core.config._parse_ignore_status_codes(
            s, _settings.error_collector.ignore_status_codes)


def _map_browser_monitoring_content_type(s):
    return s.split()


def _map_strip_exception_messages_whitelist(s):
    return [expand_builtin_exception_name(item) for item in s.split()]


def _map_inc_excl_attributes(s):
    return newrelic.core.config._parse_attributes(s)


# Processing of a single setting from configuration file.

def _raise_configuration_error(section, option=None):
    _logger.error('CONFIGURATION ERROR')
    if section:
        _logger.error('Section = %s' % section)

    if option is None:
        options = _config_object.options(section)

        _logger.error('Options = %s' % options)
        _logger.exception('Exception Details')

        if not _ignore_errors:
            if section:
                raise newrelic.api.exceptions.ConfigurationError(
                        'Invalid configuration for section "%s". '
                        'Check New Relic agent log file for further '
                        'details.' % section)
            else:
                raise newrelic.api.exceptions.ConfigurationError(
                        'Invalid configuration. Check New Relic agent '
                        'log file for further details.')

    else:
        _logger.error('Option = %s' % option)
        _logger.exception('Exception Details')

        if not _ignore_errors:
            if section:
                raise newrelic.api.exceptions.ConfigurationError(
                        'Invalid configuration for option "%s" in '
                        'section "%s". Check New Relic agent log '
                        'file for further details.' % (option, section))
            else:
                raise newrelic.api.exceptions.ConfigurationError(
                        'Invalid configuration for option "%s". '
                        'Check New Relic agent log file for further '
                        'details.' % option)


def _process_setting(section, option, getter, mapper):
    try:
        # The type of a value is dictated by the getter
        # function supplied.

        value = getattr(_config_object, getter)(section, option)

        # The getter parsed the value okay but want to
        # pass this through a mapping function to change
        # it to internal value suitable for internal
        # settings object. This is usually one where the
        # value was a string.

        if mapper:
            value = mapper(value)

        # Now need to apply the option from the
        # configuration file to the internal settings
        # object. Walk the object path and assign it.

        target = _settings
        fields = option.split('.', 1)

        while True:
            if len(fields) == 1:
                setattr(target, fields[0], value)
                break
            else:
                target = getattr(target, fields[0])
                fields = fields[1].split('.', 1)

        # Cache the configuration so can be dumped out to
        # log file when whole main configuration has been
        # processed. This ensures that the log file and log
        # level entries have been set.

        _cache_object.append((option, value))

    except ConfigParser.NoSectionError:
        pass

    except ConfigParser.NoOptionError:
        pass

    except Exception:
        _raise_configuration_error(section, option)


# Processing of all the settings for specified section except
# for log file and log level which are applied separately to
# ensure they are set as soon as possible.

def _process_configuration(section):
    _process_setting(section, 'feature_flag',
                     'get', _map_feature_flag)
    _process_setting(section, 'app_name',
                     'get', None)
    _process_setting(section, 'labels',
                     'get', _map_labels)
    _process_setting(section, 'license_key',
                     'get', None)
    _process_setting(section, 'api_key',
                     'get', None)
    _process_setting(section, 'host',
                     'get', None)
    _process_setting(section, 'port',
                     'getint', None)
    _process_setting(section, 'ssl',
                     'getboolean', None)
    _process_setting(section, 'proxy_scheme',
                     'get', None)
    _process_setting(section, 'proxy_host',
                     'get', None)
    _process_setting(section, 'proxy_port',
                     'getint', None)
    _process_setting(section, 'proxy_user',
                     'get', None)
    _process_setting(section, 'proxy_pass',
                     'get', None)
    _process_setting(section, 'audit_log_file',
                     'get', None)
    _process_setting(section, 'monitor_mode',
                     'getboolean', None)
    _process_setting(section, 'developer_mode',
                     'getboolean', None)
    _process_setting(section, 'high_security',
                     'getboolean', None)
    _process_setting(section, 'capture_params',
                     'getboolean', None)
    _process_setting(section, 'ignored_params',
                     'get', _map_split_strings)
    _process_setting(section, 'capture_environ',
                     'getboolean', None)
    _process_setting(section, 'include_environ',
                     'get', _map_split_strings)
    _process_setting(section, 'max_stack_trace_lines',
                     'getint', None)
    _process_setting(section, 'startup_timeout',
                     'getfloat', None)
    _process_setting(section, 'shutdown_timeout',
                     'getfloat', None)
    _process_setting(section, 'attributes.enabled',
                     'getboolean', None)
    _process_setting(section, 'attributes.exclude',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'attributes.include',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'transaction_name.naming_scheme',
                     'get', None)
    _process_setting(section, 'thread_profiler.enabled',
                     'getboolean', None)
    _process_setting(section, 'xray_session.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_tracer.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_tracer.transaction_threshold',
                     'get', _map_transaction_threshold)
    _process_setting(section, 'transaction_tracer.record_sql',
                     'get', _map_record_sql)
    _process_setting(section, 'transaction_tracer.stack_trace_threshold',
                     'getfloat', None)
    _process_setting(section, 'transaction_tracer.explain_enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_tracer.explain_threshold',
                     'getfloat', None)
    _process_setting(section, 'transaction_tracer.function_trace',
                     'get', _map_split_strings)
    _process_setting(section, 'transaction_tracer.generator_trace',
                     'get', _map_split_strings)
    _process_setting(section, 'transaction_tracer.top_n',
                     'getint', None)
    _process_setting(section, 'transaction_tracer.attributes.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_tracer.attributes.exclude',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'transaction_tracer.attributes.include',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'error_collector.enabled',
                     'getboolean', None)
    _process_setting(section, 'error_collector.capture_events',
                     'getboolean', None)
    _process_setting(section, 'error_collector.max_event_samples_stored',
                     'getint', None)
    _process_setting(section, 'error_collector.capture_source',
                     'getboolean', None)
    _process_setting(section, 'error_collector.ignore_errors',
                     'get', _map_split_strings)
    _process_setting(section, 'error_collector.ignore_status_codes',
                     'get', _merge_ignore_status_codes)
    _process_setting(section, 'error_collector.attributes.enabled',
                     'getboolean', None)
    _process_setting(section, 'error_collector.attributes.exclude',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'error_collector.attributes.include',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'browser_monitoring.enabled',
                     'getboolean', None)
    _process_setting(section, 'browser_monitoring.auto_instrument',
                     'getboolean', None)
    _process_setting(section, 'browser_monitoring.loader',
                     'get', None)
    _process_setting(section, 'browser_monitoring.debug',
                     'getboolean', None)
    _process_setting(section, 'browser_monitoring.ssl_for_http',
                     'getboolean', None)
    _process_setting(section, 'browser_monitoring.content_type',
                     'get', _map_split_strings)
    _process_setting(section, 'browser_monitoring.attributes.enabled',
                     'getboolean', None)
    _process_setting(section, 'browser_monitoring.attributes.exclude',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'browser_monitoring.attributes.include',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'slow_sql.enabled',
                     'getboolean', None)
    _process_setting(section, 'synthetics.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_events.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_events.max_samples_stored',
                     'getint', None)
    _process_setting(section, 'transaction_events.attributes.enabled',
                     'getboolean', None)
    _process_setting(section, 'transaction_events.attributes.exclude',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'transaction_events.attributes.include',
                     'get', _map_inc_excl_attributes)
    _process_setting(section, 'custom_insights_events.enabled',
                     'getboolean', None)
    _process_setting(section, 'custom_insights_events.max_samples_stored',
                     'getint', None)
    _process_setting(section, 'local_daemon.socket_path',
                     'get', None)
    _process_setting(section, 'local_daemon.synchronous_startup',
                     'getboolean', None)
    _process_setting(section, 'agent_limits.transaction_traces_nodes',
                     'getint', None)
    _process_setting(section, 'agent_limits.sql_query_length_maximum',
                     'getint', None)
    _process_setting(section, 'agent_limits.slow_sql_stack_trace',
                     'getint', None)
    _process_setting(section, 'agent_limits.max_sql_connections',
                     'getint', None)
    _process_setting(section, 'agent_limits.sql_explain_plans',
                     'getint', None)
    _process_setting(section, 'agent_limits.sql_explain_plans_per_harvest',
                     'getint', None)
    _process_setting(section, 'agent_limits.slow_sql_data',
                     'getint', None)
    _process_setting(section, 'agent_limits.merge_stats_maximum',
                     'getint', None)
    _process_setting(section, 'agent_limits.errors_per_transaction',
                     'getint', None)
    _process_setting(section, 'agent_limits.errors_per_harvest',
                     'getint', None)
    _process_setting(section, 'agent_limits.slow_transaction_dry_harvests',
                     'getint', None)
    _process_setting(section, 'agent_limits.thread_profiler_nodes',
                     'getint', None)
    _process_setting(section, 'agent_limits.xray_transactions',
                     'getint', None)
    _process_setting(section, 'agent_limits.xray_profile_overhead',
                     'getfloat', None)
    _process_setting(section, 'agent_limits.xray_profile_maximum',
                     'getint', None)
    _process_setting(section, 'agent_limits.synthetics_events',
                     'getint', None)
    _process_setting(section, 'agent_limits.synthetics_transactions',
                     'getint', None)
    _process_setting(section, 'agent_limits.data_compression_threshold',
                     'getint', None)
    _process_setting(section, 'agent_limits.data_compression_level',
                     'getint', None)
    _process_setting(section, 'agent_limits.max_outstanding_traces',
                    'getint', None)
    _process_setting(section, 'console.listener_socket',
                     'get', _map_console_listener_socket)
    _process_setting(section, 'console.allow_interpreter_cmd',
                     'getboolean', None)
    _process_setting(section, 'debug.disable_api_supportability_metrics',
                     'getboolean', None)
    _process_setting(section, 'debug.log_data_collector_calls',
                     'getboolean', None)
    _process_setting(section, 'debug.log_data_collector_payloads',
                     'getboolean', None)
    _process_setting(section, 'debug.log_malformed_json_data',
                     'getboolean', None)
    _process_setting(section, 'debug.log_transaction_trace_payload',
                     'getboolean', None)
    _process_setting(section, 'debug.log_thread_profile_payload',
                     'getboolean', None)
    _process_setting(section, 'debug.log_raw_metric_data',
                     'getboolean', None)
    _process_setting(section, 'debug.log_normalized_metric_data',
                     'getboolean', None)
    _process_setting(section, 'debug.log_normalization_rules',
                     'getboolean', None)
    _process_setting(section, 'debug.log_agent_initialization',
                     'getboolean', None)
    _process_setting(section, 'debug.log_explain_plan_queries',
                     'getboolean', None)
    _process_setting(section, 'debug.log_autorum_middleware',
                     'getboolean', None)
    _process_setting(section, 'debug.enable_coroutine_profiling',
                     'getboolean', None)
    _process_setting(section, 'debug.record_transaction_failure',
                     'getboolean', None)
    _process_setting(section, 'debug.explain_plan_obfuscation',
                     'get', None)
    _process_setting(section, 'debug.disable_certificate_validation',
                     'getboolean', None)
    _process_setting(section, 'cross_application_tracer.enabled',
                     'getboolean', None)
    _process_setting(section, 'message_tracer.segment_parameters_enabled',
                     'getboolean', None)
    _process_setting(section, 'process_host.display_name',
                     'get', None)
    _process_setting(section, 'utilization.detect_aws',
                     'getboolean', None)
    _process_setting(section, 'utilization.detect_azure',
                     'getboolean', None)
    _process_setting(section, 'utilization.detect_docker',
                     'getboolean', None)
    _process_setting(section, 'utilization.detect_gcp',
                     'getboolean', None)
    _process_setting(section, 'utilization.detect_pcf',
                     'getboolean', None)
    _process_setting(section, 'utilization.logical_processors',
                     'getint', None)
    _process_setting(section, 'utilization.total_ram_mib',
                     'getint', None)
    _process_setting(section, 'utilization.billing_hostname',
                     'get', None)
    _process_setting(section, 'strip_exception_messages.enabled',
                     'getboolean', None)
    _process_setting(section, 'strip_exception_messages.whitelist',
                     'get', _map_strip_exception_messages_whitelist)
    _process_setting(section, 'datastore_tracer.instance_reporting.enabled',
                     'getboolean', None)
    _process_setting(section,
                     'datastore_tracer.database_name_reporting.enabled',
                     'getboolean', None)
    _process_setting(section, 'heroku.use_dyno_names',
                     'getboolean', None)
    _process_setting(section, 'heroku.dyno_name_prefixes_to_shorten',
                     'get', _map_split_strings)


# Loading of configuration from specified file and for specified
# deployment environment. Can also indicate whether configuration
# and instrumentation errors should raise an exception or not.

_configuration_done = False


def _process_app_name_setting():
    # Do special processing to handle the case where the application
    # name was actually a semicolon separated list of names. In this
    # case the first application name is the primary and the others are
    # linked applications the application also reports to. What we need
    # to do is explicitly retrieve the application object for the
    # primary application name and link it with the other applications.
    # When activating the application the linked names will be sent
    # along to the core application where the association will be
    # created if the do not exist.

    name = _settings.app_name.split(';')[0].strip() or 'Python Application'

    linked = []
    for altname in _settings.app_name.split(';')[1:]:
        altname = altname.strip()
        if altname:
            linked.append(altname)

    def _link_applications(application):
        for altname in linked:
            _logger.debug("link to %s" % ((name, altname),))
            application.link_to_application(altname)

    if linked:
        newrelic.api.application.Application.run_on_initialization(
                name, _link_applications)
        _settings.linked_applications = linked

    _settings.app_name = name


def _process_labels_setting(labels=None):
    # Do special processing to handle labels. Initially the labels
    # setting will be a list of key/value tuples. This needs to be
    # converted into a list of dictionaries. It is also necessary
    # to eliminate duplicates by taking the last value, plus apply
    # length limits and limits on the number collected.

    if labels is None:
        labels = _settings.labels

    length_limit = 255
    count_limit = 64

    deduped = {}

    for key, value in labels:

        if len(key) > length_limit:
            _logger.warning('Improper configuration. Label key %s is too '
                    'long. Truncating key to: %s' % (key, key[:length_limit]))

        if len(value) > length_limit:
            _logger.warning('Improper configuration. Label value %s is too '
                    'long. Truncating value to: %s' %
                    (value, value[:length_limit]))

        if len(deduped) >= count_limit:
            _logger.warning('Improper configuration. Maximum number of labels '
                    'reached. Using first %d labels.' % count_limit)
            break

        key = key[:length_limit]
        value = value[:length_limit]

        deduped[key] = value

    result = []

    for key, value in deduped.items():
        result.append({'label_type': key, 'label_value': value})

    _settings.labels = result


def delete_setting(settings_object, name):
    """Delete setting from settings_object.

    If passed a 'root' setting, like 'error_collector', it will
    delete 'error_collector' and all settings underneath it, such
    as 'error_collector.attributes.enabled'

    """

    target = settings_object
    fields = name.split('.', 1)

    while len(fields) > 1:
        if not hasattr(target, fields[0]):
            break
        target = getattr(target, fields[0])
        fields = fields[1].split('.', 1)

    try:
        delattr(target, fields[0])
    except AttributeError:
        _logger.debug('Failed to delete setting: %r', name)


def translate_deprecated_settings(settings, cached_settings):
    # If deprecated setting has been set by user, but the new
    # setting has not, then translate the deprecated setting to the
    # new one.
    #
    # If both deprecated and new setting have been applied, ignore
    # deprecated setting.
    #
    # In either case, delete the deprecated one from the settings object.

    # Parameters:
    #
    #    settings:
    #         Settings object
    #
    #   cached_settings:
    #         A list of (key, value) pairs of the parsed global settings
    #         found in the config file.

    # NOTE:
    #
    # cached_settings is a list of option key/values and can have duplicate
    # keys, if the customer used environment sections in the config file.
    # Since options are applied to the settings object in order, so that the
    # options at the end of the list will override earlier options with the
    # same key, then converting to a dict will result in each option having
    # the most recently applied value.

    cached = dict(cached_settings)

    deprecated_settings_map = [
        (
            'transaction_tracer.capture_attributes',
            'transaction_tracer.attributes.enabled'
        ),
        (
            'error_collector.capture_attributes',
            'error_collector.attributes.enabled'
        ),
        (
            'browser_monitoring.capture_attributes',
            'browser_monitoring.attributes.enabled'
        ),
        (
            'analytics_events.capture_attributes',
            'transaction_events.attributes.enabled'
        ),
        (
            'analytics_events.enabled',
            'transaction_events.enabled'
        ),
        (
            'analytics_events.max_samples_stored',
            'transaction_events.max_samples_stored'
        ),
    ]

    for (old_key, new_key) in deprecated_settings_map:

        if old_key in cached:
            _logger.info('Deprecated setting found: %r. Please use new '
                    'setting: %r.', old_key, new_key)

            if new_key in cached:
                _logger.info('Ignoring deprecated setting: %r. Using new '
                        'setting: %r.', old_key, new_key)
            else:
                apply_config_setting(settings, new_key, cached[old_key])
                _logger.info('Applying value of deprecated setting %r to %r.',
                        old_key, new_key)

            delete_setting(settings, old_key)

    # The 'ignored_params' setting is more complicated than the above
    # deprecated settings, so it gets handled separately.

    if 'ignored_params' in cached:

        _logger.info('Deprecated setting found: ignored_params. Please use '
                'new setting: attributes.exclude. For the new setting, an '
                'ignored parameter should be prefaced with '
                '"request.parameters.". For example, ignoring a parameter '
                'named "foo" should be added added to attributes.exclude as '
                '"request.parameters.foo."')

        # Don't merge 'ignored_params' settings. If user set
        # 'attributes.exclude' setting, only use those values,
        # and ignore 'ignored_params' settings.

        if 'attributes.exclude' in cached:
            _logger.info('Ignoring deprecated setting: ignored_params. Using '
                    'new setting: attributes.exclude.')

        else:
            ignored_params = fetch_config_setting(settings, 'ignored_params')

            for p in ignored_params:
                attr_value = 'request.parameters.' + p
                excluded_attrs = fetch_config_setting(
                        settings, 'attributes.exclude')

                if attr_value not in excluded_attrs:
                    settings.attributes.exclude.append(attr_value)
                    _logger.info('Applying value of deprecated setting '
                            'ignored_params to attributes.exclude: %r.',
                            attr_value)

        delete_setting(settings, 'ignored_params')

    # The 'capture_params' setting is deprecated, but since it affects
    # attribute filter default destinations, it is not translated here. We
    # log a message, but keep the capture_params setting.
    #
    # See newrelic.core.transaction:Transaction.agent_attributes to see how
    # it is used.

    if 'capture_params' in cached:
        _logger.info('Deprecated setting found: capture_params. Please use '
                'new setting: attributes.exclude. To disable capturing all '
                'request parameters, add "request.parameters.*" to '
                'attributes.exclude.')

    # Log a DeprecationWarning for customers who have disabled SSL. Disabling
    # SSL will be disallowed in a future agent version.
    if not settings.ssl:
        msg = ('Disabling SSL will be disallowed in a future agent version. '
               'Please enable ssl by removing ssl=false from your New Relic '
               'configuration file or by removing the NEW_RELIC_SSL '
               'environment variable from the application environment.')

        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        _logger.warning(msg)

    return settings


def apply_local_high_security_mode_setting(settings):
    # When High Security Mode is activated, certain settings must be
    # set to be secure, even if that requires overriding a setting that
    # has been individually configured as insecure.

    if not settings.high_security:
        return settings

    log_template = ('Overriding setting for %r because High '
                    'Security Mode has been activated. The original '
                    'setting was %r. The new setting is %r.')

    if not settings.ssl:
        settings.ssl = True
        _logger.info(log_template, 'ssl', False, True)

    # capture_params is a deprecated setting for users, and has three
    # possible values:
    #
    #   True:  For backward compatibility.
    #   False: For backward compatibility.
    #   None:  The current default setting.
    #
    # In High Security, capture_params must be False, but we only need
    # to log if the customer has actually used the deprecated setting
    # and set it to True.

    if settings.capture_params:
        settings.capture_params = False
        _logger.info(log_template, 'capture_params', True, False)
    elif settings.capture_params is None:
        settings.capture_params = False

    if settings.transaction_tracer.record_sql == 'raw':
        settings.transaction_tracer.record_sql = 'obfuscated'
        _logger.info(log_template, 'transaction_tracer.record_sql',
            'raw', 'obfuscated')

    if not settings.strip_exception_messages.enabled:
        settings.strip_exception_messages.enabled = True
        _logger.info(log_template, 'strip_exception_messages.enabled',
                False, True)

    if settings.custom_insights_events.enabled:
        settings.custom_insights_events.enabled = False
        _logger.info(log_template, 'custom_insights_events.enabled', True,
                False)

    if settings.message_tracer.segment_parameters_enabled:
        settings.message_tracer.segment_parameters_enabled = False
        _logger.info(log_template,
                'message_tracer.segment_parameters_enabled',
                True, False)

    return settings


def _load_configuration(config_file=None, environment=None,
        ignore_errors=True, log_file=None, log_level=None):

    global _configuration_done

    global _config_file
    global _environment
    global _ignore_errors

    # Check whether initialisation has been done previously. If
    # it has then raise a configuration error if it was against
    # a different configuration. Otherwise just return. We don't
    # check at this time if an incompatible configuration has
    # been read from a different sub interpreter. If this occurs
    # then results will be undefined. Use from different sub
    # interpreters of the same process is not recommended.

    if _configuration_done:
        if _config_file != config_file or _environment != environment:
            raise newrelic.api.exceptions.ConfigurationError(
                    'Configuration has already been done against '
                    'differing configuration file or environment. '
                    'Prior configuration file used was "%s" and '
                    'environment "%s".' % (_config_file, _environment))
        else:
            return

    _configuration_done = True

    # Update global variables tracking what configuration file and
    # environment was used, plus whether errors are to be ignored.

    _config_file = config_file
    _environment = environment
    _ignore_errors = ignore_errors

    # If no configuration file then nothing more to be done.

    if not config_file:

        _logger.debug("no agent configuration file")

        # Force initialisation of the logging system now in case
        # setup provided by environment variables.

        if log_file is None:
            log_file = _settings.log_file

        if log_level is None:
            log_level = _settings.log_level

        initialize_logging(log_file, log_level)

        # Validate provided feature flags and log a warning if get one
        # which isn't valid.

        for flag in _settings.feature_flag:
            if flag not in _FEATURE_FLAGS:
                _logger.warning('Unknown agent feature flag %r provided. '
                        'Check agent documentation or release notes, or '
                        'contact New Relic support for clarification of '
                        'validity of the specific feature flag.', flag)

        # Look for an app_name setting which is actually a semi colon
        # list of application names and adjust app_name setting and
        # registered linked applications for later handling.

        _process_app_name_setting()

        # Look for any labels and translate them into required form
        # for sending up to data collector on registration.

        _process_labels_setting()

        return

    _logger.debug("agent configuration file was %s" % config_file)

    # Now read in the configuration file. Cache the config file
    # name in internal settings object as indication of succeeding.

    if not _config_object.read([config_file]):
        raise newrelic.api.exceptions.ConfigurationError(
                 'Unable to open configuration file %s.' % config_file)

    _settings.config_file = config_file

    # Must process log file entries first so that errors with
    # the remainder will get logged if log file is defined.

    _process_setting('newrelic', 'log_file', 'get', None)

    if environment:
        _process_setting('newrelic:%s' % environment,
                         'log_file', 'get', None)

    if log_file is None:
        log_file = _settings.log_file

    _process_setting('newrelic', 'log_level', 'get', _map_log_level)

    if environment:
        _process_setting('newrelic:%s' % environment,
                         'log_level', 'get', _map_log_level)

    if log_level is None:
        log_level = _settings.log_level

    # Force initialisation of the logging system now that we
    # have the log file and log level.

    initialize_logging(log_file, log_level)

    # Now process the remainder of the global configuration
    # settings.

    _process_configuration('newrelic')

    # And any overrides specified with a section corresponding
    # to a specific deployment environment.

    if environment:
        _settings.environment = environment
        _process_configuration('newrelic:%s' % environment)

    # Log details of the configuration options which were
    # read and the values they have as would be applied
    # against the internal settings object.

    for option, value in _cache_object:
        _logger.debug("agent config %s = %s" % (option, repr(value)))

    # Validate provided feature flags and log a warning if get one
    # which isn't valid.

    for flag in _settings.feature_flag:
        if flag not in _FEATURE_FLAGS:
            _logger.warning('Unknown agent feature flag %r provided. '
                    'Check agent documentation or release notes, or '
                    'contact New Relic support for clarification of '
                    'validity of the specific feature flag.', flag)

    # Translate old settings

    translate_deprecated_settings(_settings, _cache_object)

    # Apply High Security Mode policy if enabled in local agent
    # configuration file.

    apply_local_high_security_mode_setting(_settings)

    # Look for an app_name setting which is actually a semi colon
    # list of application names and adjust app_name setting and
    # registered linked applications for later handling.

    _process_app_name_setting()

    # Look for any labels and translate them into required form
    # for sending up to data collector on registration.

    _process_labels_setting()

    # Instrument with function trace any callables supplied by the
    # user in the configuration.

    for function in _settings.transaction_tracer.function_trace:
        try:
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'
            label = None
            params = None
            terminal = False
            rollup = None

            _logger.debug("register function-trace %s" %
                    ((module, object_path, name, group),))

            hook = _function_trace_import_hook(object_path, name, group,
                    label, params, terminal, rollup)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section=None,
                    option='transaction_tracer.function_trace')

    # Instrument with generator trace any callables supplied by the
    # user in the configuration.

    for function in _settings.transaction_tracer.generator_trace:
        try:
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'

            _logger.debug("register generator-trace %s" %
                    ((module, object_path, name, group),))

            hook = _generator_trace_import_hook(object_path, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section=None,
                    option='transaction_tracer.generator_trace')


# Generic error reporting functions.

def _raise_instrumentation_error(type, locals):
    _logger.error('INSTRUMENTATION ERROR')
    _logger.error('Type = %s' % type)
    _logger.error('Locals = %s' % locals)
    _logger.exception('Exception Details')

    if not _ignore_errors:
        raise newrelic.api.exceptions.InstrumentationError(
                'Failure when instrumenting code. Check New Relic '
                'agent log file for further details.')


# Registration of module import hooks defined in configuration file.

_module_import_hook_results = {}
_module_import_hook_registry = {}


def module_import_hook_results():
    return _module_import_hook_results


def _module_import_hook(target, module, function):
    def _instrument(target):
        _logger.debug("instrument module %s" %
                ((target, module, function),))

        try:
            instrumented = target._nr_instrumented
        except AttributeError:
            instrumented = target._nr_instrumented = set()

        if (module, function) in instrumented:
            _logger.debug("instrumentation already run %s" %
                    ((target, module, function),))
            return

        instrumented.add((module, function))

        try:
            getattr(newrelic.api.import_hook.import_module(module),
                    function)(target)

            _module_import_hook_results[(target.__name__, module,
                    function)] = ''

        except Exception:
            _module_import_hook_results[(target.__name__, module,
                    function)] = traceback.format_exception(*sys.exc_info())

            _raise_instrumentation_error('import-hook', locals())

    return _instrument


def _process_module_configuration():
    for section in _config_object.sections():
        if not section.startswith('import-hook:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            execute = _config_object.get(section, 'execute')
            fields = execute.split(':', 1)
            module = fields[0]
            function = 'instrument'
            if len(fields) != 1:
                function = fields[1]

            target = section.split(':', 1)[1]

            if target not in _module_import_hook_registry:
                _module_import_hook_registry[target] = (module, function)

                _logger.debug("register module %s" %
                        ((target, module, function),))

                hook = _module_import_hook(target, module, function)
                newrelic.api.import_hook.register_import_hook(target, hook)

                _module_import_hook_results.setdefault(
                        (target, module, function), None)

        except Exception:
            _raise_configuration_error(section)


# Setup wsgi application wrapper defined in configuration file.

def _wsgi_application_import_hook(object_path, application):
    def _instrument(target):
        _logger.debug("wrap wsgi-application %s" %
                ((target, object_path, application),))

        try:
            newrelic.api.web_transaction.wrap_wsgi_application(
                    target, object_path, application)
        except Exception:
            _raise_instrumentation_error('wsgi-application', locals())

    return _instrument


def _process_wsgi_application_configuration():
    for section in _config_object.sections():
        if not section.startswith('wsgi-application:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            application = None

            if _config_object.has_option(section, 'application'):
                application = _config_object.get(section, 'application')

            _logger.debug("register wsgi-application %s" %
                    ((module, object_path, application),))

            hook = _wsgi_application_import_hook(object_path, application)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup background task wrapper defined in configuration file.

def _background_task_import_hook(object_path, application, name, group):
    def _instrument(target):
        _logger.debug("wrap background-task %s" %
                ((target, object_path, application, name, group),))

        try:
            newrelic.api.background_task.wrap_background_task(
                    target, object_path, application, name, group)
        except Exception:
            _raise_instrumentation_error('background-task', locals())

    return _instrument


def _process_background_task_configuration():
    for section in _config_object.sections():
        if not section.startswith('background-task:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            application = None
            name = None
            group = 'Function'

            if _config_object.has_option(section, 'application'):
                application = _config_object.get(section, 'application')
            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')
            if _config_object.has_option(section, 'group'):
                group = _config_object.get(section, 'group')

            if name and name.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)

            _logger.debug("register background-task %s" %
                    ((module, object_path, application, name, group),))

            hook = _background_task_import_hook(object_path,
                  application, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup database traces defined in configuration file.

def _database_trace_import_hook(object_path, sql):
    def _instrument(target):
        _logger.debug("wrap database-trace %s" %
                ((target, object_path, sql),))

        try:
            newrelic.api.database_trace.wrap_database_trace(
                    target, object_path, sql)
        except Exception:
            _raise_instrumentation_error('database-trace', locals())

    return _instrument


def _process_database_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('database-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            sql = _config_object.get(section, 'sql')

            if sql.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                sql = eval(sql, vars)

            _logger.debug("register database-trace %s" %
                    ((module, object_path, sql),))

            hook = _database_trace_import_hook(object_path, sql)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup external traces defined in configuration file.

def _external_trace_import_hook(object_path, library, url, method):
    def _instrument(target):
        _logger.debug("wrap external-trace %s" %
                ((target, object_path, library, url, method),))

        try:
            newrelic.api.external_trace.wrap_external_trace(
                    target, object_path, library, url, method)
        except Exception:
            _raise_instrumentation_error('external-trace', locals())

    return _instrument


def _process_external_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('external-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            method = None

            library = _config_object.get(section, 'library')
            url = _config_object.get(section, 'url')
            if _config_object.has_option(section, 'method'):
                method = _config_object.get(section, 'method')

            if url.startswith('lambda '):
                vars = {"callable_name":
                          newrelic.api.object_wrapper.callable_name}
                url = eval(url, vars)

            if method and method.startswith('lambda '):
                vars = {"callable_name":
                          newrelic.api.object_wrapper.callable_name}
                method = eval(method, vars)

            _logger.debug("register external-trace %s" %
                    ((module, object_path, library, url, method),))

            hook = _external_trace_import_hook(object_path,
                    library, url, method)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup function traces defined in configuration file.

def _function_trace_import_hook(object_path, name, group, label, params,
        terminal, rollup):
    def _instrument(target):
        _logger.debug("wrap function-trace %s" %
                ((target, object_path, name, group, label, params,
                terminal, rollup),))

        try:
            newrelic.api.function_trace.wrap_function_trace(
                    target, object_path, name, group, label, params,
                    terminal, rollup)
        except Exception:
            _raise_instrumentation_error('function-trace', locals())

    return _instrument


def _process_function_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('function-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'
            label = None
            params = None
            terminal = False
            rollup = None

            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')
            if _config_object.has_option(section, 'group'):
                group = _config_object.get(section, 'group')
            if _config_object.has_option(section, 'label'):
                label = _config_object.get(section, 'label')
            if _config_object.has_option(section, 'terminal'):
                terminal = _config_object.getboolean(section, 'terminal')
            if _config_object.has_option(section, 'rollup'):
                rollup = _config_object.get(section, 'rollup')

            if name and name.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)

            _logger.debug("register function-trace %s" %
                    ((module, object_path, name, group, label, params,
                    terminal, rollup),))

            hook = _function_trace_import_hook(object_path, name, group,
                    label, params, terminal, rollup)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup generator traces defined in configuration file.

def _generator_trace_import_hook(object_path, name, group):
    def _instrument(target):
        _logger.debug("wrap generator-trace %s" %
                ((target, object_path, name, group),))

        try:
            newrelic.api.generator_trace.wrap_generator_trace(
                    target, object_path, name, group)
        except Exception:
            _raise_instrumentation_error('generator-trace', locals())

    return _instrument


def _process_generator_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('generator-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'

            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')
            if _config_object.has_option(section, 'group'):
                group = _config_object.get(section, 'group')

            if name and name.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)

            _logger.debug("register generator-trace %s" %
                    ((module, object_path, name, group),))

            hook = _generator_trace_import_hook(object_path, name, group)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup profile traces defined in configuration file.

def _profile_trace_import_hook(object_path, name, group, depth):
    def _instrument(target):
        _logger.debug("wrap profile-trace %s" %
                ((target, object_path, name, group, depth),))

        try:
            newrelic.api.profile_trace.wrap_profile_trace(
                    target, object_path, name, group, depth=depth)
        except Exception:
            _raise_instrumentation_error('profile-trace', locals())

    return _instrument


def _process_profile_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('profile-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'
            depth = 3

            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')
            if _config_object.has_option(section, 'group'):
                group = _config_object.get(section, 'group')
            if _config_object.has_option(section, 'depth'):
                depth = _config_object.get(section, 'depth')

            if name and name.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)

            _logger.debug("register profile-trace %s" %
                    ((module, object_path, name, group, depth),))

            hook = _profile_trace_import_hook(object_path, name, group,
                    depth=depth)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup memcache traces defined in configuration file.

def _memcache_trace_import_hook(object_path, command):
    def _instrument(target):
        _logger.debug("wrap memcache-trace %s" %
                ((target, object_path, command),))

        try:
            newrelic.api.memcache_trace.wrap_memcache_trace(
                    target, object_path, command)
        except Exception:
            _raise_instrumentation_error('memcache-trace', locals())

    return _instrument


def _process_memcache_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('memcache-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            command = _config_object.get(section, 'command')

            if command.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                command = eval(command, vars)

            _logger.debug("register memcache-trace %s" %
                    ((module, object_path, command),))

            hook = _memcache_trace_import_hook(object_path, command)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup name transaction wrapper defined in configuration file.

def _transaction_name_import_hook(object_path, name, group, priority):
    def _instrument(target):
        _logger.debug("wrap transaction-name %s" %
                ((target, object_path, name, group, priority),))

        try:
            newrelic.api.transaction_name.wrap_transaction_name(
                    target, object_path, name, group, priority)
        except Exception:
            _raise_instrumentation_error('transaction-name', locals())

    return _instrument


def _process_transaction_name_configuration():
    for section in _config_object.sections():
        # Support 'name-transaction' for backward compatibility.
        if (not section.startswith('transaction-name:') and
                not section.startswith('name-transaction:')):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            name = None
            group = 'Function'
            priority = None

            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')
            if _config_object.has_option(section, 'group'):
                group = _config_object.get(section, 'group')
            if _config_object.has_option(section, 'priority'):
                priority = _config_object.getint(section, 'priority')

            if name and name.startswith('lambda '):
                vars = {"callable_name":
                         newrelic.api.object_wrapper.callable_name}
                name = eval(name, vars)

            _logger.debug("register transaction-name %s" %
                    ((module, object_path, name, group, priority),))

            hook = _transaction_name_import_hook(object_path, name,
                                                 group, priority)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Setup error trace wrapper defined in configuration file.

def _error_trace_import_hook(object_path, ignore_errors):
    def _instrument(target):
        _logger.debug("wrap error-trace %s" %
                ((target, object_path, ignore_errors),))

        try:
            newrelic.api.error_trace.wrap_error_trace(
                    target, object_path, ignore_errors)
        except Exception:
            _raise_instrumentation_error('error-trace', locals())

    return _instrument


def _process_error_trace_configuration():
    for section in _config_object.sections():
        if not section.startswith('error-trace:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            ignore_errors = []

            if _config_object.has_option(section, 'ignore_errors'):
                ignore_errors = _config_object.get(section,
                        'ignore_errors').split()

            _logger.debug("register error-trace %s" %
                  ((module, object_path, ignore_errors),))

            hook = _error_trace_import_hook(object_path, ignore_errors)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


# Automatic data source loading defined in configuration file.

_data_sources = []


def _process_data_source_configuration():
    for section in _config_object.sections():
        if not section.startswith('data-source:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            application = None
            name = None
            settings = {}
            properties = {}

            if _config_object.has_option(section, 'application'):
                application = _config_object.get(section, 'application')
            if _config_object.has_option(section, 'name'):
                name = _config_object.get(section, 'name')

            if _config_object.has_option(section, 'settings'):
                config_section = _config_object.get(section, 'settings')
                settings.update(_config_object.items(config_section))

            properties.update(_config_object.items(section))

            properties.pop('enabled', None)
            properties.pop('function', None)
            properties.pop('application', None)
            properties.pop('name', None)
            properties.pop('settings', None)

            _logger.debug("register data-source %s" %
                    ((module, object_path, name),))

            _data_sources.append((section, module, object_path, application,
                    name, settings, properties))
        except Exception:
            _raise_configuration_error(section)


def _startup_data_source():
    _logger.debug('Registering data sources defined in configuration.')

    agent_instance = newrelic.core.agent.agent_instance()

    for section, module, object_path, application, name, \
            settings, properties in _data_sources:
        try:
            source = getattr(newrelic.api.import_hook.import_module(
                    module), object_path)

            agent_instance.register_data_source(source,
                    application, name, settings, **properties)

        except Exception:
            _logger.exception('Attempt to register data source %s:%s with '
                    'name %r from section %r of agent configuration file '
                    'has failed. Data source will be skipped.', module,
                    object_path, name, section)


_data_sources_done = False


def _setup_data_source():

    global _data_sources_done

    if _data_sources_done:
        return

    _data_sources_done = True

    if _data_sources:
        newrelic.core.agent.Agent.run_on_startup(_startup_data_source)


# Setup function profiler defined in configuration file.

def _function_profile_import_hook(object_path, filename, delay, checkpoint):
    def _instrument(target):
        _logger.debug("wrap function-profile %s" %
                ((target, object_path, filename, delay, checkpoint),))

        try:
            newrelic.api.function_profile.wrap_function_profile(target,
                    object_path, filename, delay, checkpoint)
        except Exception:
            _raise_instrumentation_error('function-profile', locals())

    return _instrument


def _process_function_profile_configuration():
    for section in _config_object.sections():
        if not section.startswith('function-profile:'):
            continue

        enabled = False

        try:
            enabled = _config_object.getboolean(section, 'enabled')
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            _raise_configuration_error(section)

        if not enabled:
            continue

        try:
            function = _config_object.get(section, 'function')
            (module, object_path) = function.split(':', 1)

            filename = None
            delay = 1.0
            checkpoint = 30

            filename = _config_object.get(section, 'filename')

            if _config_object.has_option(section, 'delay'):
                delay = _config_object.getfloat(section, 'delay')
            if _config_object.has_option(section, 'checkpoint'):
                checkpoint = _config_object.getfloat(section, 'checkpoint')

            _logger.debug("register function-profile %s" %
                    ((module, object_path, filename, delay, checkpoint),))

            hook = _function_profile_import_hook(object_path, filename,
                    delay, checkpoint)
            newrelic.api.import_hook.register_import_hook(module, hook)
        except Exception:
            _raise_configuration_error(section)


def _process_module_definition(target, module, function='instrument'):
    enabled = True
    execute = None

    # XXX This check makes the following checks to see if import hook
    # was defined in agent configuration file redundant. Leave it as is
    # for now until can clean up whole configuration system.

    if target in _module_import_hook_registry:
        return

    try:
        section = 'import-hook:%s' % target
        if _config_object.has_section(section):
            enabled = _config_object.getboolean(section, 'enabled')
    except ConfigParser.NoOptionError:
        pass
    except Exception:
        _raise_configuration_error(section)

    try:
        if _config_object.has_option(section, 'execute'):
            execute = _config_object.get(section, 'execute')

    except Exception:
        _raise_configuration_error(section)

    try:
        if enabled and not execute:
            _module_import_hook_registry[target] = (module, function)

            _logger.debug("register module %s" %
                    ((target, module, function),))

            newrelic.api.import_hook.register_import_hook(target,
                    _module_import_hook(target, module, function))

            _module_import_hook_results.setdefault(
                    (target, module, function), None)

    except Exception:
        _raise_instrumentation_error('import-hook', locals())


def _process_module_builtin_defaults():
    _process_module_definition('asyncio.tasks',
            'newrelic.hooks.coroutines_asyncio',
            'instrument_asyncio_tasks')

    _process_module_definition('django.core.handlers.base',
            'newrelic.hooks.framework_django',
            'instrument_django_core_handlers_base')
    _process_module_definition('django.core.handlers.wsgi',
            'newrelic.hooks.framework_django',
            'instrument_django_core_handlers_wsgi')
    _process_module_definition('django.core.urlresolvers',
            'newrelic.hooks.framework_django',
            'instrument_django_core_urlresolvers')
    _process_module_definition('django.template',
            'newrelic.hooks.framework_django',
            'instrument_django_template')
    _process_module_definition('django.template.loader_tags',
            'newrelic.hooks.framework_django',
            'instrument_django_template_loader_tags')
    _process_module_definition('django.core.servers.basehttp',
            'newrelic.hooks.framework_django',
            'instrument_django_core_servers_basehttp')
    _process_module_definition('django.contrib.staticfiles.views',
            'newrelic.hooks.framework_django',
            'instrument_django_contrib_staticfiles_views')
    _process_module_definition('django.contrib.staticfiles.handlers',
            'newrelic.hooks.framework_django',
            'instrument_django_contrib_staticfiles_handlers')
    _process_module_definition('django.views.debug',
            'newrelic.hooks.framework_django',
            'instrument_django_views_debug')
    _process_module_definition('django.http.multipartparser',
            'newrelic.hooks.framework_django',
            'instrument_django_http_multipartparser')
    _process_module_definition('django.core.mail',
            'newrelic.hooks.framework_django',
            'instrument_django_core_mail')
    _process_module_definition('django.core.mail.message',
            'newrelic.hooks.framework_django',
            'instrument_django_core_mail_message')
    _process_module_definition('django.views.generic.base',
            'newrelic.hooks.framework_django',
            'instrument_django_views_generic_base')
    _process_module_definition('django.core.management.base',
            'newrelic.hooks.framework_django',
            'instrument_django_core_management_base')
    _process_module_definition('django.template.base',
            'newrelic.hooks.framework_django',
            'instrument_django_template_base')
    _process_module_definition('django.middleware.gzip',
            'newrelic.hooks.framework_django',
            'instrument_django_gzip_middleware')

    # New modules in Django 1.10
    _process_module_definition('django.urls.resolvers',
            'newrelic.hooks.framework_django',
            'instrument_django_core_urlresolvers')
    _process_module_definition('django.urls.base',
            'newrelic.hooks.framework_django',
            'instrument_django_urls_base')
    _process_module_definition('django.core.handlers.exception',
            'newrelic.hooks.framework_django',
            'instrument_django_core_handlers_exception')

    _process_module_definition('flask.app',
            'newrelic.hooks.framework_flask',
            'instrument_flask_app')
    _process_module_definition('flask.templating',
            'newrelic.hooks.framework_flask',
            'instrument_flask_templating')
    _process_module_definition('flask.blueprints',
            'newrelic.hooks.framework_flask',
            'instrument_flask_blueprints')
    _process_module_definition('flask.views',
            'newrelic.hooks.framework_flask',
            'instrument_flask_views')

    _process_module_definition('flask_compress',
            'newrelic.hooks.middleware_flask_compress',
            'instrument_flask_compress')

    # _process_module_definition('web.application',
    #        'newrelic.hooks.framework_webpy')
    # _process_module_definition('web.template',
    #        'newrelic.hooks.framework_webpy')

    _process_module_definition('gluon.compileapp',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_compileapp')
    _process_module_definition('gluon.restricted',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_restricted')
    _process_module_definition('gluon.main',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_main')
    _process_module_definition('gluon.template',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_template')
    _process_module_definition('gluon.tools',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_tools')
    _process_module_definition('gluon.http',
            'newrelic.hooks.framework_web2py',
            'instrument_gluon_http')

    _process_module_definition('gluon.contrib.feedparser',
            'newrelic.hooks.external_feedparser')
    _process_module_definition('gluon.contrib.memcache.memcache',
            'newrelic.hooks.memcache_memcache')

    _process_module_definition('grpc._channel',
            'newrelic.hooks.external_grpc',
            'instrument_grpc__channel')
    _process_module_definition('google.protobuf.reflection',
            'newrelic.hooks.external_grpc',
            'instrument_google_protobuf_reflection')

    _process_module_definition('pylons.wsgiapp',
            'newrelic.hooks.framework_pylons')
    _process_module_definition('pylons.controllers.core',
            'newrelic.hooks.framework_pylons')
    _process_module_definition('pylons.templating',
            'newrelic.hooks.framework_pylons')

    _process_module_definition('bottle',
            'newrelic.hooks.framework_bottle',
            'instrument_bottle')

    _process_module_definition('cherrypy._cpreqbody',
            'newrelic.hooks.framework_cherrypy',
            'instrument_cherrypy__cpreqbody')
    _process_module_definition('cherrypy._cprequest',
            'newrelic.hooks.framework_cherrypy',
            'instrument_cherrypy__cprequest')
    _process_module_definition('cherrypy._cpdispatch',
            'newrelic.hooks.framework_cherrypy',
            'instrument_cherrypy__cpdispatch')
    _process_module_definition('cherrypy._cpwsgi',
            'newrelic.hooks.framework_cherrypy',
            'instrument_cherrypy__cpwsgi')
    _process_module_definition('cherrypy._cptree',
            'newrelic.hooks.framework_cherrypy',
            'instrument_cherrypy__cptree')

    if 'tornado.instrumentation.r3' in _settings.feature_flag:
        _process_module_definition('tornado.httpserver',
                'newrelic.hooks.framework_tornado_r3.httpserver',
                'instrument_tornado_httpserver')
        _process_module_definition('tornado.httpclient',
                'newrelic.hooks.framework_tornado_r3.httpclient',
                'instrument_tornado_httpclient')
        _process_module_definition('tornado.curl_httpclient',
                'newrelic.hooks.framework_tornado_r3.curl_httpclient',
                'instrument_tornado_curl_httpclient')
        _process_module_definition('tornado.httputil',
                'newrelic.hooks.framework_tornado_r3.httputil',
                'instrument_tornado_httputil')
        _process_module_definition('tornado.web',
                'newrelic.hooks.framework_tornado_r3.web',
                'instrument_tornado_web')
        _process_module_definition('tornado.stack_context',
                'newrelic.hooks.framework_tornado_r3.stack_context',
                'instrument_tornado_stack_context')
        _process_module_definition('tornado.ioloop',
                'newrelic.hooks.framework_tornado_r3.ioloop',
                'instrument_tornado_ioloop')
        _process_module_definition('tornado.gen',
                'newrelic.hooks.framework_tornado_r3.gen',
                'instrument_tornado_gen')
        _process_module_definition('tornado.concurrent',
                'newrelic.hooks.framework_tornado_r3.concurrent',
                'instrument_concurrent')
        _process_module_definition('concurrent.futures',
                'newrelic.hooks.framework_tornado_r3.concurrent',
                'instrument_concurrent')
        _process_module_definition('tornado.http1connection',
                'newrelic.hooks.framework_tornado_r3.http1connection',
                'instrument_tornado_http1connection')
        _process_module_definition('tornado.platform.asyncio',
                'newrelic.hooks.framework_tornado_r3.ioloop',
                'instrument_tornado_asyncio_loop')

    elif 'tornado.instrumentation.r1' in _settings.feature_flag:
        _process_module_definition('tornado.wsgi',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_wsgi')

        _process_module_definition('tornado.httpserver',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_httpserver')
        _process_module_definition('tornado.httputil',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_httputil')
        _process_module_definition('tornado.web',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_web')
        _process_module_definition('tornado.template',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_template')
        _process_module_definition('tornado.stack_context',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_stack_context')
        _process_module_definition('tornado.ioloop',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_ioloop')
        _process_module_definition('tornado.iostream',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_iostream')
        _process_module_definition('tornado.curl_httpclient',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_curl_httpclient')
        _process_module_definition('tornado.simple_httpclient',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_simple_httpclient')
        _process_module_definition('tornado.gen',
                'newrelic.hooks.framework_tornado_r1',
                'instrument_tornado_gen')

    elif 'tornado.instrumentation.r4' in _settings.feature_flag:
        _process_module_definition('tornado.web',
                'newrelic.hooks.framework_tornado_r4.web',
                'instrument_tornado_web')
        _process_module_definition('tornado.routing',
                'newrelic.hooks.framework_tornado_r4.routing',
                'instrument_tornado_routing')
        _process_module_definition('tornado.httpclient',
                'newrelic.hooks.framework_tornado_r4.httpclient',
                'instrument_tornado_httpclient')
        _process_module_definition('tornado.httputil',
                'newrelic.hooks.framework_tornado_r4.httputil',
                'instrument_tornado_httputil')
        _process_module_definition('tornado.gen',
                'newrelic.hooks.framework_tornado_r4.gen',
                'instrument_tornado_gen')

    else:
        _process_module_definition('tornado.wsgi',
                'newrelic.hooks.framework_tornado.wsgi',
                'instrument_tornado_wsgi')

        _process_module_definition('tornado.httpserver',
                'newrelic.hooks.framework_tornado.httpserver',
                'instrument_tornado_httpserver')
        _process_module_definition('tornado.iostream',
                'newrelic.hooks.framework_tornado.iostream',
                'instrument_tornado_iostream')
        _process_module_definition('tornado.ioloop',
                'newrelic.hooks.framework_tornado.ioloop',
                'instrument_tornado_ioloop')
        _process_module_definition('tornado.httputil',
                'newrelic.hooks.framework_tornado.httputil',
                'instrument_tornado_httputil')
        _process_module_definition('tornado.curl_httpclient',
                'newrelic.hooks.framework_tornado.curl_httpclient',
                'instrument_tornado_curl_httpclient')
        _process_module_definition('tornado.simple_httpclient',
                'newrelic.hooks.framework_tornado.simple_httpclient',
                'instrument_tornado_simple_httpclient')
        _process_module_definition('tornado.web',
                'newrelic.hooks.framework_tornado.web',
                'instrument_tornado_web')
        _process_module_definition('tornado.stack_context',
                'newrelic.hooks.framework_tornado.stack_context',
                'instrument_tornado_stack_context')
        _process_module_definition('tornado.template',
                'newrelic.hooks.framework_tornado.template',
                'instrument_tornado_template')
        _process_module_definition('tornado.gen',
                'newrelic.hooks.framework_tornado.gen',
                'instrument_tornado_gen')

    _process_module_definition('paste.httpserver',
            'newrelic.hooks.adapter_paste',
            'instrument_paste_httpserver')

    _process_module_definition('gunicorn.app.base',
            'newrelic.hooks.adapter_gunicorn',
            'instrument_gunicorn_app_base')

    _process_module_definition('cx_Oracle',
            'newrelic.hooks.database_cx_oracle',
            'instrument_cx_oracle')

    _process_module_definition('ibm_db_dbi',
            'newrelic.hooks.database_ibm_db_dbi',
            'instrument_ibm_db_dbi')

    _process_module_definition('mysql.connector',
            'newrelic.hooks.database_mysql',
            'instrument_mysql_connector')
    _process_module_definition('MySQLdb',
            'newrelic.hooks.database_mysqldb',
            'instrument_mysqldb')
    _process_module_definition('oursql',
            'newrelic.hooks.database_oursql',
            'instrument_oursql')
    _process_module_definition('pymysql',
            'newrelic.hooks.database_pymysql',
            'instrument_pymysql')

    _process_module_definition('pyodbc',
            'newrelic.hooks.database_pyodbc',
            'instrument_pyodbc')

    _process_module_definition('pymssql',
            'newrelic.hooks.database_pymssql',
            'instrument_pymssql')

    _process_module_definition('psycopg2',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2')
    _process_module_definition('psycopg2._psycopg2',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2__psycopg2')
    _process_module_definition('psycopg2.extensions',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2_extensions')
    _process_module_definition('psycopg2._json',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2__json')
    _process_module_definition('psycopg2._range',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2__range')
    _process_module_definition('psycopg2.sql',
            'newrelic.hooks.database_psycopg2',
            'instrument_psycopg2_sql')

    _process_module_definition('psycopg2ct',
            'newrelic.hooks.database_psycopg2ct',
            'instrument_psycopg2ct')
    _process_module_definition('psycopg2ct.extensions',
            'newrelic.hooks.database_psycopg2ct',
            'instrument_psycopg2ct_extensions')

    _process_module_definition('psycopg2cffi',
            'newrelic.hooks.database_psycopg2cffi',
            'instrument_psycopg2cffi')
    _process_module_definition('psycopg2cffi.extensions',
            'newrelic.hooks.database_psycopg2cffi',
            'instrument_psycopg2cffi_extensions')

    _process_module_definition('postgresql.driver.dbapi20',
            'newrelic.hooks.database_postgresql',
            'instrument_postgresql_driver_dbapi20')

    _process_module_definition('postgresql.interface.proboscis.dbapi2',
            'newrelic.hooks.database_postgresql',
            'instrument_postgresql_interface_proboscis_dbapi2')

    _process_module_definition('sqlite3',
            'newrelic.hooks.database_sqlite',
            'instrument_sqlite3')
    _process_module_definition('sqlite3.dbapi2',
            'newrelic.hooks.database_sqlite',
            'instrument_sqlite3_dbapi2')

    _process_module_definition('pysqlite2',
            'newrelic.hooks.database_sqlite',
            'instrument_sqlite3')
    _process_module_definition('pysqlite2.dbapi2',
            'newrelic.hooks.database_sqlite',
            'instrument_sqlite3_dbapi2')

    _process_module_definition('memcache',
            'newrelic.hooks.datastore_memcache',
            'instrument_memcache')
    _process_module_definition('umemcache',
            'newrelic.hooks.datastore_umemcache',
            'instrument_umemcache')
    _process_module_definition('pylibmc.client',
            'newrelic.hooks.datastore_pylibmc',
            'instrument_pylibmc_client')
    _process_module_definition('bmemcached.client',
            'newrelic.hooks.datastore_bmemcached',
            'instrument_bmemcached_client')
    _process_module_definition('pymemcache.client',
            'newrelic.hooks.datastore_pymemcache',
            'instrument_pymemcache_client')

    _process_module_definition('jinja2.environment',
            'newrelic.hooks.template_jinja2')

    _process_module_definition('mako.runtime',
            'newrelic.hooks.template_mako',
            'instrument_mako_runtime')
    _process_module_definition('mako.template',
            'newrelic.hooks.template_mako',
            'instrument_mako_template')

    _process_module_definition('genshi.template.base',
            'newrelic.hooks.template_genshi')

    if six.PY2:
        _process_module_definition('httplib',
                'newrelic.hooks.external_httplib')
    else:
        _process_module_definition('http.client',
                'newrelic.hooks.external_httplib')

    _process_module_definition('httplib2',
            'newrelic.hooks.external_httplib2')

    if six.PY2:
        _process_module_definition('urllib',
                'newrelic.hooks.external_urllib')
    else:
        _process_module_definition('urllib.request',
                'newrelic.hooks.external_urllib')

    if six.PY2:
        _process_module_definition('urllib2',
                'newrelic.hooks.external_urllib2')

    _process_module_definition('urllib3.connectionpool',
            'newrelic.hooks.external_urllib3',
            'instrument_urllib3_connectionpool')
    _process_module_definition('urllib3.connection',
            'newrelic.hooks.external_urllib3',
            'instrument_urllib3_connection')

    _process_module_definition('aiohttp.wsgi',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_wsgi')
    _process_module_definition('aiohttp.web',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_web')
    _process_module_definition('aiohttp.web_reqrep',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_web_response')
    _process_module_definition('aiohttp.web_response',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_web_response')
    _process_module_definition('aiohttp.web_urldispatcher',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_web_urldispatcher')
    _process_module_definition('aiohttp.client',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_client')
    _process_module_definition('aiohttp.client_reqrep',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_client_reqrep')
    _process_module_definition('aiohttp.protocol',
            'newrelic.hooks.framework_aiohttp',
            'instrument_aiohttp_protocol')

    _process_module_definition('requests.api',
            'newrelic.hooks.external_requests',
            'instrument_requests_api')
    _process_module_definition('requests.sessions',
            'newrelic.hooks.external_requests',
            'instrument_requests_sessions')
    _process_module_definition('requests.packages.urllib3.connection',
            'newrelic.hooks.external_urllib3',
            'instrument_urllib3_connection')

    _process_module_definition('feedparser',
            'newrelic.hooks.external_feedparser')

    _process_module_definition('xmlrpclib',
            'newrelic.hooks.external_xmlrpclib')

    _process_module_definition('dropbox',
            'newrelic.hooks.external_dropbox')

    _process_module_definition('facepy.graph_api',
            'newrelic.hooks.external_facepy')

    _process_module_definition('pysolr',
            'newrelic.hooks.datastore_pysolr',
            'instrument_pysolr')

    _process_module_definition('solr',
            'newrelic.hooks.datastore_solrpy',
            'instrument_solrpy')

    _process_module_definition('elasticsearch.client',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client')
    _process_module_definition('elasticsearch.client.cat',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_cat')
    _process_module_definition('elasticsearch.client.cluster',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_cluster')
    _process_module_definition('elasticsearch.client.indices',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_indices')
    _process_module_definition('elasticsearch.client.nodes',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_nodes')
    _process_module_definition('elasticsearch.client.snapshot',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_snapshot')
    _process_module_definition('elasticsearch.client.tasks',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_tasks')
    _process_module_definition('elasticsearch.client.ingest',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_client_ingest')
    _process_module_definition('elasticsearch.connection.base',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_connection_base')
    _process_module_definition('elasticsearch.transport',
            'newrelic.hooks.datastore_elasticsearch',
            'instrument_elasticsearch_transport')

    _process_module_definition('pika.adapters',
            'newrelic.hooks.messagebroker_pika',
            'instrument_pika_adapters')
    _process_module_definition('pika.channel',
            'newrelic.hooks.messagebroker_pika',
            'instrument_pika_channel')
    _process_module_definition('pika.spec',
            'newrelic.hooks.messagebroker_pika',
            'instrument_pika_spec')

    _process_module_definition('pyelasticsearch.client',
            'newrelic.hooks.datastore_pyelasticsearch',
            'instrument_pyelasticsearch_client')

    _process_module_definition('pymongo.connection',
            'newrelic.hooks.datastore_pymongo',
            'instrument_pymongo_connection')
    _process_module_definition('pymongo.mongo_client',
            'newrelic.hooks.datastore_pymongo',
            'instrument_pymongo_mongo_client')
    _process_module_definition('pymongo.collection',
            'newrelic.hooks.datastore_pymongo',
            'instrument_pymongo_collection')

    _process_module_definition('redis.connection',
            'newrelic.hooks.datastore_redis',
            'instrument_redis_connection')
    _process_module_definition('redis.client',
            'newrelic.hooks.datastore_redis',
            'instrument_redis_client')

    _process_module_definition('motor',
            'newrelic.hooks.datastore_motor', 'patch_motor')

    _process_module_definition('piston.resource',
            'newrelic.hooks.component_piston',
            'instrument_piston_resource')
    _process_module_definition('piston.doc',
            'newrelic.hooks.component_piston',
            'instrument_piston_doc')

    _process_module_definition('tastypie.resources',
            'newrelic.hooks.component_tastypie',
            'instrument_tastypie_resources')
    _process_module_definition('tastypie.api',
            'newrelic.hooks.component_tastypie',
            'instrument_tastypie_api')

    _process_module_definition('rest_framework.views',
            'newrelic.hooks.component_djangorestframework',
            'instrument_rest_framework_views')
    _process_module_definition('rest_framework.decorators',
            'newrelic.hooks.component_djangorestframework',
            'instrument_rest_framework_decorators')

    _process_module_definition('celery.task.base',
            'newrelic.hooks.application_celery',
            'instrument_celery_app_task')
    _process_module_definition('celery.app.task',
            'newrelic.hooks.application_celery',
            'instrument_celery_app_task')
    _process_module_definition('celery.worker',
            'newrelic.hooks.application_celery',
            'instrument_celery_worker')
    _process_module_definition('celery.concurrency.processes',
            'newrelic.hooks.application_celery',
            'instrument_celery_worker')
    _process_module_definition('celery.concurrency.prefork',
            'newrelic.hooks.application_celery',
            'instrument_celery_worker')
    # _process_module_definition('celery.loaders.base',
    #        'newrelic.hooks.application_celery',
    #        'instrument_celery_loaders_base')
    _process_module_definition('celery.execute.trace',
            'newrelic.hooks.application_celery',
            'instrument_celery_execute_trace')
    _process_module_definition('celery.task.trace',
            'newrelic.hooks.application_celery',
            'instrument_celery_execute_trace')
    _process_module_definition('celery.app.trace',
            'newrelic.hooks.application_celery',
            'instrument_celery_execute_trace')

    _process_module_definition('flup.server.cgi',
            'newrelic.hooks.adapter_flup',
            'instrument_flup_server_cgi')
    _process_module_definition('flup.server.ajp_base',
            'newrelic.hooks.adapter_flup',
            'instrument_flup_server_ajp_base')
    _process_module_definition('flup.server.fcgi_base',
            'newrelic.hooks.adapter_flup',
            'instrument_flup_server_fcgi_base')
    _process_module_definition('flup.server.scgi_base',
            'newrelic.hooks.adapter_flup',
            'instrument_flup_server_scgi_base')

    _process_module_definition('pywapi',
            'newrelic.hooks.external_pywapi',
            'instrument_pywapi')

    _process_module_definition('meinheld.server',
            'newrelic.hooks.adapter_meinheld',
            'instrument_meinheld_server')

    _process_module_definition('waitress.server',
            'newrelic.hooks.adapter_waitress',
            'instrument_waitress_server')

    _process_module_definition('gevent.wsgi',
            'newrelic.hooks.adapter_gevent',
            'instrument_gevent_wsgi')
    _process_module_definition('gevent.pywsgi',
            'newrelic.hooks.adapter_gevent',
            'instrument_gevent_pywsgi')

    _process_module_definition('wsgiref.simple_server',
            'newrelic.hooks.adapter_wsgiref',
            'instrument_wsgiref_simple_server')

    _process_module_definition('cherrypy.wsgiserver',
            'newrelic.hooks.adapter_cherrypy',
            'instrument_cherrypy_wsgiserver')

    _process_module_definition('pyramid.router',
            'newrelic.hooks.framework_pyramid',
            'instrument_pyramid_router')
    _process_module_definition('pyramid.config',
            'newrelic.hooks.framework_pyramid',
            'instrument_pyramid_config_views')
    _process_module_definition('pyramid.config.views',
            'newrelic.hooks.framework_pyramid',
            'instrument_pyramid_config_views')

    _process_module_definition('cornice.service',
            'newrelic.hooks.component_cornice',
            'instrument_cornice_service')

    # _process_module_definition('twisted.web.server',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_server')
    # _process_module_definition('twisted.web.http',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_http')
    # _process_module_definition('twisted.web.resource',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_web_resource')
    # _process_module_definition('twisted.internet.defer',
    #        'newrelic.hooks.framework_twisted',
    #        'instrument_twisted_internet_defer')

    _process_module_definition('gevent.monkey',
            'newrelic.hooks.coroutines_gevent',
            'instrument_gevent_monkey')

    _process_module_definition('weberror.errormiddleware',
            'newrelic.hooks.middleware_weberror',
            'instrument_weberror_errormiddleware')
    _process_module_definition('weberror.reporter',
            'newrelic.hooks.middleware_weberror',
            'instrument_weberror_reporter')

    _process_module_definition('thrift.transport.TSocket',
            'newrelic.hooks.external_thrift')

    _process_module_definition('gearman.client',
            'newrelic.hooks.application_gearman',
            'instrument_gearman_client')
    _process_module_definition('gearman.connection_manager',
            'newrelic.hooks.application_gearman',
            'instrument_gearman_connection_manager')
    _process_module_definition('gearman.worker',
            'newrelic.hooks.application_gearman',
            'instrument_gearman_worker')

    _process_module_definition('botocore.endpoint',
            'newrelic.hooks.external_botocore',
            'instrument_botocore_endpoint')


def _process_module_entry_points():
    try:
        import pkg_resources
    except ImportError:
        return

    group = 'newrelic.hooks'

    for entrypoint in pkg_resources.iter_entry_points(group=group):
        target = entrypoint.name

        if target in _module_import_hook_registry:
            continue

        module = entrypoint.module_name

        if entrypoint.attrs:
            function = '.'.join(entrypoint.attrs)
        else:
            function = 'instrument'

        _process_module_definition(target, module, function)


_instrumentation_done = False


def _setup_instrumentation():

    global _instrumentation_done

    if _instrumentation_done:
        return

    _instrumentation_done = True

    _process_module_configuration()
    _process_module_entry_points()
    _process_module_builtin_defaults()

    _process_wsgi_application_configuration()
    _process_background_task_configuration()

    _process_database_trace_configuration()
    _process_external_trace_configuration()
    _process_function_trace_configuration()
    _process_generator_trace_configuration()
    _process_profile_trace_configuration()
    _process_memcache_trace_configuration()

    _process_transaction_name_configuration()

    _process_error_trace_configuration()

    _process_data_source_configuration()

    _process_function_profile_configuration()


def _setup_extensions():
    try:
        import pkg_resources
    except ImportError:
        return

    group = 'newrelic.extension'

    for entrypoint in pkg_resources.iter_entry_points(group=group):
        __import__(entrypoint.module_name)
        module = sys.modules[entrypoint.module_name]
        module.initialize()


_console = None


def _startup_agent_console():
    global _console

    if _console:
        return

    _console = newrelic.console.ConnectionManager(
            _settings.console.listener_socket)


def _setup_agent_console():
    if _settings.console.listener_socket:
        newrelic.core.agent.Agent.run_on_startup(_startup_agent_console)


def initialize(config_file=None, environment=None, ignore_errors=None,
            log_file=None, log_level=None):

    if config_file is None:
        config_file = os.environ.get('NEW_RELIC_CONFIG_FILE', None)

    if environment is None:
        environment = os.environ.get('NEW_RELIC_ENVIRONMENT', None)

    if ignore_errors is None:
        ignore_errors = newrelic.core.config._environ_as_bool(
                'NEW_RELIC_IGNORE_STARTUP_ERRORS', True)

    _load_configuration(config_file, environment, ignore_errors,
            log_file, log_level)

    if _settings.monitor_mode or _settings.developer_mode:
        _settings.enabled = True
        _setup_instrumentation()
        _setup_data_source()
        _setup_extensions()
        _setup_agent_console()
    else:
        _settings.enabled = False


def filter_app_factory(app, global_conf, config_file, environment=None):
    initialize(config_file, environment)
    return newrelic.api.web_transaction.WSGIApplicationWrapper(app)
