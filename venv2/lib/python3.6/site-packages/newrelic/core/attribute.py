import logging

from collections import namedtuple

from newrelic.packages import six

from newrelic.core.attribute_filter import (DST_ALL, DST_ERROR_COLLECTOR,
        DST_TRANSACTION_TRACER, DST_TRANSACTION_EVENTS)


_logger = logging.getLogger(__name__)

_Attribute = namedtuple('_Attribute',
        ['name', 'value', 'destinations'])

# The following destinations are created here, never changed, and only
# used increate_agent_attributes. It is placed at the module level here
# as an optimization.

# All agent attributes go to transaction traces and error traces by default.

_DESTINATIONS = DST_ERROR_COLLECTOR | DST_TRANSACTION_TRACER
_DESTINATIONS_WITH_EVENTS = _DESTINATIONS | DST_TRANSACTION_EVENTS

# The following subset goes to transaction events by default.

_TRANSACTION_EVENT_DEFAULT_ATTRIBUTES = set((
        'host.displayName',
        'request.method',
        'request.headers.contentType',
        'request.headers.contentLength',
        'response.status',
        'response.headers.contentLength',
        'response.headers.contentType',
        'message.queueName',
        'message.routingKey',
))

MAX_NUM_USER_ATTRIBUTES = 64
MAX_ATTRIBUTE_LENGTH = 255
MAX_64_BIT_INT = 2 ** 63 - 1


class NameTooLongException(Exception):
    pass


class NameIsNotStringException(Exception):
    pass


class IntTooLargeException(Exception):
    pass


class CastingFailureException(Exception):
    pass


class Attribute(_Attribute):

    def __repr__(self):
        return "Attribute(name=%r, value=%r, destinations=%r)" % (
                self.name, self.value, bin(self.destinations))


def create_attributes(attr_dict, destinations, attribute_filter):
    attributes = []

    for k, v in attr_dict.items():
        dest = attribute_filter.apply(k, destinations)
        attributes.append(Attribute(k, v, dest))

    return attributes


def create_agent_attributes(attr_dict, attribute_filter):
    attributes = []

    for k, v in attr_dict.items():
        if k in _TRANSACTION_EVENT_DEFAULT_ATTRIBUTES:
            dest = attribute_filter.apply(k, _DESTINATIONS_WITH_EVENTS)
        else:
            dest = attribute_filter.apply(k, _DESTINATIONS)

        attributes.append(Attribute(k, v, dest))

    return attributes


def create_user_attributes(attr_dict, attribute_filter):
    destinations = DST_ALL
    return create_attributes(attr_dict, destinations, attribute_filter)


def truncate(text, maxsize=MAX_ATTRIBUTE_LENGTH, encoding='utf-8'):

    # Truncate text so that it's byte representation
    # is no longer than maxsize bytes.

    # If text is unicode (Python 2 or 3), return unicode.
    # If text is a Python 2 string, return str.

    if isinstance(text, six.text_type):
        return _truncate_unicode(text, maxsize, encoding)
    else:
        return _truncate_bytes(text, maxsize)


def _truncate_unicode(u, maxsize, encoding='utf-8'):
    encoded = u.encode(encoding)[:maxsize]
    return encoded.decode(encoding, 'ignore')


def _truncate_bytes(s, maxsize):
    return s[:maxsize]


def check_name_length(name, max_length=MAX_ATTRIBUTE_LENGTH, encoding='utf-8'):
    trunc_name = truncate(name, max_length, encoding)
    if name != trunc_name:
        raise NameTooLongException()


def check_name_is_string(name):
    if not isinstance(name, (six.text_type, six.binary_type)):
        raise NameIsNotStringException()


def check_max_int(value, max_int=MAX_64_BIT_INT):
    if isinstance(value, six.integer_types) and value > max_int:
        raise IntTooLargeException()


def process_user_attribute(name, value):

    # Perform all necessary checks on a potential attribute.
    #
    # Returns:
    #       (name, value) if attribute is OK.
    #       (NONE, NONE) if attribute isn't.
    #
    # If any of these checks fail, they will raise an exception, so we
    # log a message, and return (None, None).

    FAILED_RESULT = (None, None)

    try:
        check_name_is_string(name)
        check_name_length(name)
        check_max_int(value)

        value = sanitize(value)

    except NameIsNotStringException:
        _logger.debug('Attribute name must be a string. Dropping '
                'attribute: %r=%r', name, value)
        return FAILED_RESULT

    except NameTooLongException:
        _logger.debug('Attribute name exceeds maximum length. Dropping '
                'attribute: %r=%r', name, value)
        return FAILED_RESULT

    except IntTooLargeException:
        _logger.debug('Attribute value exceeds maximum integer value. '
                'Dropping attribute: %r=%r', name, value)
        return FAILED_RESULT

    except CastingFailureException:
        _logger.debug('Attribute value cannot be cast to a string. '
                'Dropping attribute: %r=%r', name, value)
        return FAILED_RESULT

    else:

        # Check length after casting

        valid_types_text = (six.text_type, six.binary_type)

        if isinstance(value, valid_types_text):
            trunc_value = truncate(value)
            if value != trunc_value:
                _logger.debug('Attribute value exceeds maximum length '
                        '(%r bytes). Truncating value: %r=%r.',
                        MAX_ATTRIBUTE_LENGTH, name, trunc_value)

            value = trunc_value

        return (name, value)


def sanitize(value):

    # Return value unchanged, if it's a valid type that is supported by
    # Insights. Otherwise, convert value to a string.
    #
    # Raise CastingFailureException, if str(value) somehow fails.

    valid_value_types = (six.text_type, six.binary_type, bool, float,
            six.integer_types)

    if not isinstance(value, valid_value_types):
        original = value

        try:
            value = str(value)
        except Exception:
            raise CastingFailureException()
        else:
            _logger.debug('Attribute value is of type: %r. Casting %r to '
                    'string: %s', type(original), original, value)

    return value
