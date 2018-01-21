# coding: utf-8

# Copyright 2014-2016 Álvaro Justen <https://github.com/turicas/rows/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import binascii
import collections
import datetime
import json
import locale
import re
import types

from base64 import b64decode, b64encode
from decimal import Decimal, InvalidOperation

import six


# Order matters here
__all__ = ['BoolField', 'IntegerField', 'FloatField', 'DatetimeField',
           'DateField', 'DecimalField', 'PercentField', 'JSONField',
           'EmailField', 'TextField', 'BinaryField', 'Field']
REGEXP_ONLY_NUMBERS = re.compile('[^0-9\-]')
SHOULD_NOT_USE_LOCALE = True  # This variable is changed by rows.locale_manager
NULL = ('-', 'null', 'none', 'nil', 'n/a', 'na')
NULL_BYTES = (b'-', b'null', b'none', b'nil', b'n/a', b'na')


class Field(object):
    """Base Field class - all fields should inherit from this

    As the fallback for all other field types are the BinaryField, this Field
    actually implements what is expected in the BinaryField
    """

    TYPE = (type(None), )

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        """Serialize a value to be exported

        `cls.serialize` should always return an unicode value, except for
        BinaryField
        """

        if value is None:
            value = ''
        return value

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        """Deserialize a value just after importing it

        `cls.deserialize` should always return a value of type `cls.TYPE` or
        `None`.
        """

        if isinstance(value, cls.TYPE):
            return value
        elif is_null(value):
            return None
        else:
            return value


class BinaryField(Field):
    """Field class to represent byte arrays

    Is not locale-aware (does not need to be)
    """

    TYPE = (six.binary_type, )

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is not None:
            if not isinstance(value, six.binary_type):
                raise ValueError("Can't be {}".format(cls.__name__))
            else:
                try:
                    return b64encode(value).decode('ascii')
                except (TypeError, binascii.Error):
                    return value
        else:
            return ''

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        if value is not None:
            if isinstance(value, six.binary_type):
                return value
            elif isinstance(value, six.text_type):
                try:
                    return b64decode(value)
                except (TypeError, ValueError, binascii.Error):
                    raise ValueError("Can't decode base64")
            else:
                raise ValueError("Can't be {}".format(cls.__name__))
        else:
            return b''


class BoolField(Field):
    """Base class to representing boolean

    Is not locale-aware (if you need to, please customize by changing its
    attributes like `TRUE_VALUES` and `FALSE_VALUES`)
    """

    TYPE = (bool, )
    SERIALIZED_VALUES = {True: 'true', False: 'false', None: ''}
    TRUE_VALUES = ('true', 'yes')
    FALSE_VALUES = ('false', 'no')

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        # TODO: should we serialize `None` as well or give it to the plugin?
        return cls.SERIALIZED_VALUES[value]

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(BoolField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        value = as_string(value).lower()
        if value in cls.TRUE_VALUES:
            return True
        elif value in cls.FALSE_VALUES:
            return False
        else:
            raise ValueError('Value is not boolean')


class IntegerField(Field):
    """Field class to represent integer

    Is locale-aware
    """

    TYPE = (int, )

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        if SHOULD_NOT_USE_LOCALE:
            return six.text_type(value)
        else:
            grouping = kwargs.get('grouping', None)
            return locale.format('%d', value, grouping=grouping)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(IntegerField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value
        elif isinstance(value, float):
            new_value = int(value)
            if new_value != value:
                raise ValueError("It's float, not integer")
            else:
                value = new_value

        value = as_string(value)
        return int(value) if SHOULD_NOT_USE_LOCALE \
                          else locale.atoi(value)


class FloatField(Field):
    """Field class to represent float

    Is locale-aware
    """

    TYPE = (float, )

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        if SHOULD_NOT_USE_LOCALE:
            return six.text_type(value)
        else:
            grouping = kwargs.get('grouping', None)
            return locale.format('%f', value, grouping=grouping)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(FloatField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        value = as_string(value)
        if SHOULD_NOT_USE_LOCALE:
            return float(value)
        else:
            return locale.atof(value)


class DecimalField(Field):
    """Field class to represent decimal data (as Python's decimal.Decimal)

    Is locale-aware
    """

    TYPE = (Decimal, )

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        value_as_string = six.text_type(value)
        if SHOULD_NOT_USE_LOCALE:
            return value_as_string
        else:
            grouping = kwargs.get('grouping', None)
            has_decimal_places = value_as_string.find('.') != -1
            if not has_decimal_places:
                string_format = '%d'
            else:
                decimal_places = len(value_as_string.split('.')[1])
                string_format = '%.{}f'.format(decimal_places)
            return locale.format(string_format, value, grouping=grouping)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(DecimalField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value
        elif type(value) in (int, float):
            return Decimal(six.text_type(value))

        if SHOULD_NOT_USE_LOCALE:
            try:
                return Decimal(value)
            except InvalidOperation:
                raise ValueError("Can't be {}".format(cls.__name__))
        else:
            locale_vars = locale.localeconv()
            decimal_separator = locale_vars['decimal_point']
            interesting_vars = ('decimal_point', 'mon_decimal_point',
                                'mon_thousands_sep', 'negative_sign',
                                'positive_sign', 'thousands_sep')
            chars = (locale_vars[x].replace('.', r'\.').replace('-', r'\-')
                     for x in interesting_vars)
            interesting_chars = ''.join(set(chars))
            regexp = re.compile(r'[^0-9{} ]'.format(interesting_chars))
            value = as_string(value)
            if regexp.findall(value):
                raise ValueError("Can't be {}".format(cls.__name__))

            parts = [REGEXP_ONLY_NUMBERS.subn('', number)[0]
                     for number in value.split(decimal_separator)]
            if len(parts) > 2:
                raise ValueError("Can't deserialize with this locale.")
            try:
                value = Decimal(parts[0])
                if len(parts) == 2:
                    decimal_places = len(parts[1])
                    value = value + (Decimal(parts[1]) / (10 ** decimal_places))
            except InvalidOperation:
                raise ValueError("Can't be {}".format(cls.__name__))
            return value


class PercentField(DecimalField):
    """Field class to represent percent values

    Is locale-aware (inherit this behaviour from `rows.DecimalField`)
    """

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''
        elif value == Decimal('0'):
            return '0.00%'

        value = Decimal(six.text_type(value * 100)[:-2])
        value = super(PercentField, cls).serialize(value, *args, **kwargs)
        return '{}%'.format(value)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        if isinstance(value, cls.TYPE):
            return value
        elif is_null(value):
            return None

        value = as_string(value)
        if '%' not in value:
            raise ValueError("Can't be {}".format(cls.__name__))
        value = value.replace('%', '')
        return super(PercentField, cls).deserialize(value) / 100


class DateField(Field):
    """Field class to represent date

    Is not locale-aware (does not need to be)
    """

    TYPE = (datetime.date, )
    INPUT_FORMAT = '%Y-%m-%d'
    OUTPUT_FORMAT = '%Y-%m-%d'

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        return six.text_type(value.strftime(cls.OUTPUT_FORMAT))

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(DateField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        value = as_string(value)

        dt_object = datetime.datetime.strptime(value, cls.INPUT_FORMAT)
        return datetime.date(dt_object.year, dt_object.month, dt_object.day)


class DatetimeField(Field):
    """Field class to represent date-time

    Is not locale-aware (does not need to be)
    """

    TYPE = (datetime.datetime, )
    DATETIME_REGEXP = re.compile('^([0-9]{4})-([0-9]{2})-([0-9]{2})[ T]'
                                 '([0-9]{2}):([0-9]{2}):([0-9]{2})$')

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        return six.text_type(value.isoformat())

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(DatetimeField, cls).deserialize(value)
        if value is None or isinstance(value, cls.TYPE):
            return value

        value = as_string(value)
        # TODO: may use iso8601
        groups = cls.DATETIME_REGEXP.findall(value)
        if not groups:
            raise ValueError("Can't be {}".format(cls.__name__))
        else:
            return datetime.datetime(*[int(x) for x in groups[0]])


class TextField(Field):
    """Field class to represent unicode strings

    Is not locale-aware (does not need to be)
    """

    TYPE = (six.text_type, )

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        if value is None or isinstance(value, cls.TYPE):
            return value
        else:
            return as_string(value)


class EmailField(TextField):
    """Field class to represent e-mail addresses

    Is not locale-aware (does not need to be)
    """

    EMAIL_REGEXP = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]+$',
                              flags=re.IGNORECASE)

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        if value is None:
            return ''

        return six.text_type(value)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(EmailField, cls).deserialize(value)
        if value is None or not value.strip():
            return None

        result = cls.EMAIL_REGEXP.findall(value)
        if not result:
            raise ValueError("Can't be {}".format(cls.__name__))
        else:
            return result[0]


class JSONField(Field):
    """Field class to represent JSON-encoded strings

    Is not locale-aware (does not need to be)
    """

    TYPE = (list, dict)

    @classmethod
    def serialize(cls, value, *args, **kwargs):
        return json.dumps(value)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        if value is None or isinstance(value, cls.TYPE):
            return value
        else:
            return json.loads(value)


local_vars = locals()
TYPES = [(key, local_vars.get(key)) for key in __all__ if key != 'Field']
AVAILABLE_FIELD_TYPES = [item[1] for item in TYPES]


def as_string(value):
    if isinstance(value, six.binary_type):
        raise ValueError('Binary is not supported')
    elif isinstance(value, six.text_type):
        return value
    else:
        return six.text_type(value)


def is_null(value):
    if value is None:
        return True
    elif type(value) is six.binary_type:
        value = value.strip().lower()
        return not value or value in NULL_BYTES
    else:
        value_str = as_string(value).strip().lower()
        return not value_str or value_str in NULL


def unique_values(values):
    result = []
    for value in values:
        if not is_null(value) and value not in result:
            result.append(value)
    return result


def detect_types(field_names, field_values, field_types=AVAILABLE_FIELD_TYPES,
                 *args, **kwargs):
    """Where the magic happens"""

    # TODO: look strategy of csv.Sniffer.has_header
    # TODO: may receive 'type hints'
    # TODO: should support receiving unicode objects directly
    # TODO: should expect data in unicode or will be able to use binary data?

    field_values = list(field_values)
    if not field_values:
        return collections.OrderedDict([(field_name, BinaryField)
                                        for field_name in field_names])

    number_of_fields = len(field_names)
    columns = list(zip(*[row for row in field_values
                         if len(row) == number_of_fields]))

    if len(columns) != number_of_fields:
        raise ValueError('Number of fields differ')

    detected_types = collections.OrderedDict([(field_name, None)
                                              for field_name in field_names])
    for index, field_name in enumerate(field_names):
        data = unique_values(columns[index])
        native_types = set(type(value) for value in data)

        if not data:
            # all values with an empty field (can't identify) -> BinaryField
            identified_type = BinaryField
        elif native_types == set([six.binary_type]):
            identified_type = BinaryField
        else:
            # ok, let's try to identify the type of this column by
            # trying to convert every non-null value in the sample
            possible_types = list(field_types)
            for value in data:
                cant_be = set()
                for type_ in possible_types:
                    try:
                        type_.deserialize(value, *args, **kwargs)
                    except (ValueError, TypeError):
                        cant_be.add(type_)
                for type_to_remove in cant_be:
                    possible_types.remove(type_to_remove)

            identified_type = possible_types[0]  # priorities matter

        detected_types[field_name] = identified_type

    return detected_types


def identify_type(value):
    value_type = type(value)
    if value_type not in (six.text_type, six.binary_type):
        possible_types = [type_class for type_name, type_class in TYPES
                          if value_type in type_class.TYPE]
        if not possible_types:
            detected = detect_types(['some_field'], [[value]])['some_field']
        else:
            detected = possible_types[0]
    else:
        detected = detect_types(['some_field'], [[value]])['some_field']

    return detected
