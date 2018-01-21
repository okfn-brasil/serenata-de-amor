import os
import logging
import time
import signal
import threading
import socket
import atexit

try:
    from ConfigParser import RawConfigParser, NoOptionError
except ImportError:
    from configparser import RawConfigParser, NoOptionError

from newrelic import version as agent_version

from newrelic.common.object_names import callable_name

from newrelic.network.platform_api import PlatformInterface
from newrelic.network.exceptions import (DiscardDataForRequest, RetryDataForRequest)

from newrelic.samplers.data_sampler import DataSampler
from newrelic.samplers.decorators import (data_source_generator, data_source_factory)

_logger = logging.getLogger(__name__)

_LOG_LEVEL = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

_LOG_FORMAT = '%(asctime)s (%(process)d/%(threadName)s) ' \
              '%(name)s %(levelname)s - %(message)s'

class RequestsConnectionFilter(logging.Filter):
    def filter(self, record):
        return False

class Stats(dict):

    """Bucket for accumulating custom metrics in format required for
    platform agent API.

    """

    # Is based on a dict all metrics are sent to the core
    # application as that and list as base class means it
    # encodes direct to JSON as we need it.

    def __init__(self, count=0, total=0.0, min=0.0, max=0.0,
            sum_of_squares=0.0):
        self.count = count
        self.total = total
        self.min = min
        self.max = max
        self.sum_of_squares = sum_of_squares

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        return self[name]

    def merge_stats(self, other):
        """Merge data from another instance of this object."""

        self.total += other.total
        self.min = self.count and min(self.min, other.min) or other.min
        self.max = max(self.max, other.max)
        self.sum_of_squares += other.sum_of_squares

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self.count += other.count

    def merge_value(self, value):
        """Merge data from a value."""

        self.total += value
        self.min = self.count and min(self.min, value) or value
        self.max = max(self.max, value)
        self.sum_of_squares += value ** 2

        # Must update the call count last as update of the
        # minimum call time is dependent on initial value.

        self.count += 1

class DataAggregator(object):

    def __init__(self, sampler):
        self.sampler = sampler

        self.period_start = 0.0
        self.metrics_table = None

    def __getattr__(self, name):
        return getattr(self.sampler, name)

    def start(self):
        self.sampler.start()

        self.period_start = time.time()
        self.metrics_table = None

    def stop(self):
        self.sampler.stop()

        self.period_start = 0.0
        self.metrics_table = None

    def upload(self, session):
        assert self.instance is not None

        if not self.period_start:
            return

        now = time.time()

        duration = now - self.period_start

        metrics = self.metrics_table or {}
        self.metrics_table = None

        def c2t(count=0, total=0.0, min=0.0, max=0.0, sum_of_squares=0.0):
            return (count, total, min, max, sum_of_squares)

        try:
            for name, value in self.metrics():
                stats = metrics.get(name)
                if stats is None:
                    stats = Stats()
                    metrics[name] = stats

                try:
                    try:
                        stats.merge_stats(Stats(*c2t(**value)))
                    except Exception:
                        stats.merge_value(value)

                except Exception:
                    _logger.exception('The merging of custom metric '
                            'sample %r from data sampler %r has failed. '
                            'Validate the format of the sample. If this '
                            'issue persists then please report this '
                            'problem to the data source provider or New '
                            'Relic support for further investigation.',
                            value, self.name)
                    break

        except Exception:
            _logger.exception('The processing of custom metrics from '
                    'data sampler %r has failed.  If this issue persists '
                    'then please report this problem to the data source '
                    'provider or New Relic support for further '
                    'investigation.', self.name)

            return []

        try:
            session.send_metric_data(self.name, self.guid, self.version,
                    duration, metrics)

        except RetryDataForRequest:
            # Throw away data if cannot report data after 5
            # minutes if trying.

            if duration < 300:
                self.metrics_table = metrics

            else:
                _logger.exception('Unable to report data custom metrics '
                        'from data sampler %r for a period of 5 minutes. '
                        'Data being discarded. If this issue persists '
                        'then please report this problem to the data source '
                        'provider or New Relic support for further '
                        'investigation.', self.name)

                self.metrics_table = None
                self.period_start = now

        except DiscardDataForRequest:
            _logger.exception('Unable to report data custom metrics '
                    'from data sampler %r. Data being discarded. If this '
                    'issue persists then please report this problem to '
                    'the data source provider or New Relic support for '
                    'further investigation.', self.name)

            self.metrics_table = None
            self.period_start = now

        except Exception:
            # An unexpected error, likely some sort of internal
            # agent implementation issue.

            _logger.exception('Unexpected exception when attempting '
                    'to harvest custom metrics and send it to the '
                    'data collector. Please report this problem to '
                    'New Relic support for further investigation.')

            self.metrics_table = None
            self.period_start = now

        else:
            self.period_start = now

class Agent(object):

    def __init__(self, license_key, host, port, ssl, timeout, proxy_host,
            proxy_port, proxy_user, proxy_pass):
        self._interface = PlatformInterface(license_key, host, port, ssl,
                timeout, proxy_host, proxy_port, proxy_user, proxy_pass)
        self._harvest_shutdown = threading.Event()
        self._data_sources = []

    def register(self, source, name=None, settings=None, **properties):
        self._data_sources.append((source, name, settings, properties))

    def harvest(self, data_aggregators):
        _logger.debug('Commencing data harvest.')

        session = self._interface.create_session()

        try:
            for data_aggregator in data_aggregators:
                _logger.debug('Harvest data source %r with guid %r. '
                        'Reporting data to %r.', data_aggregator.name,
                        data_aggregator.guid, data_aggregator.consumer)

                data_aggregator.upload(session)

        finally:
            session.close_connection()

    def run(self):
        """Means of running standalone process to consume data sources and
        post custom metrics collected.

        """

        _logger.info('New Relic Python Agent - Data Source (%s)',
                agent_version)

        data_aggregators = []

        for (source, name, settings, properties) in self._data_sources:
            try:
                data_sampler = DataSampler('New Relic (Platform)', source,
                        name, settings, **properties)

                if data_sampler.guid is None:
                    _logger.warning('Skipping data source %s as does not '
                            'have an associated data source guid.', source)

                    continue

                data_aggregator = DataAggregator(data_sampler)

                data_aggregators.append(data_aggregator)

            except Exception:
                _logger.exception('Attempt to register data source %s '
                        'with name %r has failed. Data source will be '
                        'skipped.', source, name)

        if not data_aggregators:
            _logger.warning('No valid data sources defined.')
            return

        _logger.debug('Starting data samplers.')

        for data_aggregator in data_aggregators:
            data_aggregator.start()

        next_harvest = time.time()

        try:
            _logger.debug('Starting main harvest loop.')

            while True:
                now = time.time()
                while next_harvest <= now:
                    next_harvest += 60.0

                delay = next_harvest - now

                self._harvest_shutdown.wait(delay)

                if self._harvest_shutdown.isSet():
                    _logger.info('New Relic Python Agent Shutdown')
                    self.harvest(data_aggregators)
                    return

                self.harvest(data_aggregators)

        except Exception:
            _logger.exception('Unexpected exception when attempting '
                    'to harvest custom metrics and send it to the '
                    'data collector. Please report this problem to '
                    'New Relic support for further investigation.')

    def shutdown(self, *args):
        self._harvest_shutdown.set()

def run(config_file, background=False):
    config_object = RawConfigParser()
    config_object.read([config_file])

    def option(name, section='newrelic', type=None, **kwargs):
        try:
            getter = 'get%s' % (type or '')
            return getattr(config_object, getter)(section, name)
        except NoOptionError:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise

    settings = {}

    license_key = os.environ.get('NEW_RELIC_LICENSE_KEY')
    license_key = option('license_key', default=license_key)

    host = option('host', default='platform-api.newrelic.com')
    port = option('port', type='int', default=None)
    ssl = option('ssl', type='boolean', default=True)

    proxy_host = option('proxy_host', default=None)
    proxy_port = option('proxy_port', type='int', default=None)
    proxy_user = option('proxy_user', default=None)
    proxy_pass = option('proxy_pass', default=None)

    timeout = option('agent_limits.data_collector_timeout',
            type='float', default=30.0)

    log_file = os.environ.get('NEW_RELIC_LOG_FILE')
    log_file = option('log_file', default=log_file)

    if log_file in ('stdout', 'stderr'):
        log_file = None

    log_level = os.environ.get('NEW_RELIC_LOG_LEVEL', 'INFO').upper()
    log_level = option('log_level', default=log_level).upper()

    if log_level in _LOG_LEVEL:
        log_level = _LOG_LEVEL[log_level]
    else:
        log_level = logging.INFO

    if not background:
        if log_file:
            try:
                os.unlink(log_file)
            except Exception:
                pass

        _requests_logger = logging.getLogger(
            'newrelic.packages.requests.packages.urllib3.connectionpool')
        _requests_logger.addFilter(RequestsConnectionFilter())

        logging.basicConfig(filename=log_file,
                level=log_level, format=_LOG_FORMAT)

    _warn = ('The platform API (used by newrelic-admin data-source) has '
            'been deprecated and will be removed from a future agent version. '
            'Please use data sources '
            '(https://docs.newrelic.com/docs/agents/python-agent/'
            'supported-features/'
            'python-custom-metrics#registering-a-data-source) '
            'in place of the platform API.')

    _logger.warning(_warn)
    print(_warn)

    agent = Agent(license_key, host, port, ssl, timeout, proxy_host,
            proxy_port, proxy_user, proxy_pass)

    for section in config_object.sections():
        if not section.startswith('data-source:'):
            continue

        enabled = option('enabled', section, 'boolean', default=True)

        if not enabled:
            continue

        function = option('function', section)
        (module_name, object_path) = function.split(':', 1)

        settings = {}
        properties = {}

        name = option('name', section=section, default=None)
        config = option('settings', section=section, default=None)

        if config:
            settings.update(config_object.items(config))

        properties.update(config_object.items(section))

        properties.pop('enabled', None)
        properties.pop('function', None)
        properties.pop('name', None)
        properties.pop('settings', None)

        _logger.debug("register data-source %s" % (
                (module_name, object_path, name),))

        try:
            module = __import__(module_name)
            for part in module_name.split('.')[1:]:
                module = getattr(module, part)
            parts = object_path.split('.')
            source = getattr(module, parts[0])
            for part in parts[1:]:
                source = getattr(source, part)

        except Exception:
            _logger.exception('Attempt to load data source %s:%s with '
                    'name %r from section %r of agent configuration file '
                    'has failed. Data source will be skipped.', module_name,
                    object_path, name, section)

        else:
            agent.register(source, name, settings, **properties)

    atexit.register(agent.shutdown)

    if background:
        thread = threading.Thread(target=agent.run)
        thread.setDaemon()
        thread.start()

    else:
        signal.signal(signal.SIGINT, agent.shutdown)
        signal.signal(signal.SIGTERM, agent.shutdown)
        signal.signal(signal.SIGHUP, agent.shutdown)

        agent.run()
