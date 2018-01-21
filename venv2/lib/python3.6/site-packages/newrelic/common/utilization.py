import logging
import os
import string
import re

from newrelic.packages import requests
from newrelic.core.internal_metrics import internal_count_metric


_logger = logging.getLogger(__name__)
VALID_CHARS_RE = re.compile(r'[0-9a-zA-Z_ ./-]')


class CommonUtilization(object):
    METADATA_URL = ''
    HEADERS = None
    EXPECTED_KEYS = ()
    VENDOR_NAME = ''
    TIMEOUT = 0.5

    @classmethod
    def record_error(cls, resource, data):
        # As per spec
        internal_count_metric(
                'Supportability/utilization/%s/error' % cls.VENDOR_NAME, 1)
        _logger.warning('Invalid %r data (%r): %r',
                cls.VENDOR_NAME, resource, data)

    @classmethod
    def fetch(cls):
        # Create own requests session and disable all environment variables,
        # so that we can bypass any proxy set via env var for this request.

        session = requests.Session()
        session.trust_env = False

        try:
            resp = session.get(cls.METADATA_URL, timeout=cls.TIMEOUT,
                    headers=cls.HEADERS)
            resp.raise_for_status()
        except Exception as e:
            resp = None
            _logger.debug('Error fetching %s data from %r: %r',
                    cls.VENDOR_NAME, cls.METADATA_URL, e)

        return resp

    @classmethod
    def get_values(cls, response):
        if response is None:
            return

        try:
            j = response.json()
        except ValueError:
            _logger.debug('Invalid %s data (%r): %r',
                    cls.VENDOR_NAME, cls.METADATA_URL, response.text)
            return

        return j

    @classmethod
    def valid_chars(cls, data):
        if data is None:
            return False

        for c in data:
            if not VALID_CHARS_RE.match(c) and ord(c) < 0x80:
                return False

        return True

    @classmethod
    def valid_length(cls, data):
        if data is None:
            return False

        b = data.encode('utf-8')
        valid = len(b) <= 255
        if valid:
            return True

        return False

    @classmethod
    def normalize(cls, key, data):
        if data is None:
            return

        try:
            stripped = data.strip()

            if (stripped and cls.valid_length(stripped) and
                    cls.valid_chars(stripped)):
                return stripped
        except:
            pass

    @classmethod
    def sanitize(cls, values):
        if values is None:
            return

        out = {}
        for key in cls.EXPECTED_KEYS:
            metadata = values.get(key, None)
            if not metadata:
                cls.record_error(key, metadata)
                return

            normalized = cls.normalize(key, metadata)
            if not normalized:
                cls.record_error(key, metadata)
                return

            out[key] = normalized

        return out

    @classmethod
    def detect(cls):
        response = cls.fetch()
        values = cls.get_values(response)
        return cls.sanitize(values)


class AWSUtilization(CommonUtilization):
    EXPECTED_KEYS = ('availabilityZone', 'instanceId', 'instanceType')
    METADATA_URL = '%s/2016-09-02/dynamic/instance-identity/document' % (
        'http://169.254.169.254'
    )
    VENDOR_NAME = 'aws'


class AzureUtilization(CommonUtilization):
    METADATA_URL = ('http://169.254.169.254'
            '/metadata/instance/compute?api-version=2017-03-01')
    EXPECTED_KEYS = ('location', 'name', 'vmId', 'vmSize')
    HEADERS = {'Metadata': 'true'}
    VENDOR_NAME = 'azure'


class GCPUtilization(CommonUtilization):
    EXPECTED_KEYS = ('id', 'machineType', 'name', 'zone')
    HEADERS = {'Metadata-Flavor': 'Google'}
    METADATA_URL = 'http://%s/computeMetadata/v1/instance/?recursive=true' % (
            'metadata.google.internal')
    VENDOR_NAME = 'gcp'

    @classmethod
    def normalize(cls, key, data):
        if data is None:
            return

        if key in ('machineType', 'zone'):
            formatted = data.strip().split('/')[-1]
        elif key == 'id':
            formatted = str(data)
        else:
            formatted = data

        return super(GCPUtilization, cls).normalize(key, formatted)


class PCFUtilization(CommonUtilization):
    EXPECTED_KEYS = ('cf_instance_guid', 'cf_instance_ip', 'memory_limit')
    VENDOR_NAME = 'pcf'

    @staticmethod
    def fetch():
        cf_instance_guid = os.environ.get('CF_INSTANCE_GUID')
        cf_instance_ip = os.environ.get('CF_INSTANCE_IP')
        memory_limit = os.environ.get('MEMORY_LIMIT')
        pcf_vars = (cf_instance_guid, cf_instance_ip, memory_limit)
        if all(pcf_vars):
            return pcf_vars

    @classmethod
    def get_values(cls, response):
        if response is None or len(response) != 3:
            return

        values = {}
        for k, v in zip(cls.EXPECTED_KEYS, response):
            if hasattr(v, 'decode'):
                v = v.decode('utf-8')
            values[k] = v
        return values


class DockerUtilization(CommonUtilization):
    VENDOR_NAME = 'docker'
    EXPECTED_KEYS = ('id',)
    METADATA_FILE = '/proc/self/cgroup'
    DOCKER_RE = re.compile(r'([0-9a-f]{64,})')

    @classmethod
    def fetch(cls):
        try:
            with open(cls.METADATA_FILE, 'rb') as f:
                for line in f:
                    stripped = line.decode('utf-8').strip()
                    cgroup = stripped.split(':')
                    if len(cgroup) != 3:
                        continue
                    subsystems = cgroup[1].split(',')
                    if 'cpu' in subsystems:
                        return cgroup[2]
        except:
            # There are all sorts of exceptions that can occur here
            # (i.e. permissions, non-existent file, etc)
            pass

    @classmethod
    def get_values(cls, contents):
        if contents is None:
            return

        value = contents.split('/')[-1]
        match = cls.DOCKER_RE.search(value)
        if match:
            value = match.group(0)
            return {'id': value}

    @classmethod
    def valid_chars(cls, data):
        if data is None:
            return False

        hex_digits = set(string.hexdigits)

        valid = all((c in hex_digits for c in data))
        if valid:
            return True

        return False

    @classmethod
    def valid_length(cls, data):
        if data is None:
            return False

        # Must be exactly 64 characters
        valid = len(data) == 64
        if valid:
            return True

        return False
