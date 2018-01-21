# coding: utf-8

# Copyright 2014-2015 Álvaro Justen <https://github.com/turicas/rows/>
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

from collections import Iterator, OrderedDict
from itertools import chain, islice
from unicodedata import normalize

from rows.fields import detect_types
from rows.table import FlexibleTable, Table


SLUG_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'


def slug(text, separator='_', permitted_chars=SLUG_CHARS,
         replace_with_separator=' -_'):
    '''Slugfy text

    Example: ' ÁLVARO  justen% ' -> 'alvaro_justen'
    '''

    # Strip non-ASCII characters
    # Example: u' ÁLVARO  justen% ' -> ' ALVARO  justen% '
    text = normalize('NFKD', text.strip()).encode('ascii', 'ignore')\
                                          .decode('ascii')

    # Replace spaces and other chars with separator
    # Example: u' ALVARO  justen% ' -> u'_ALVARO__justen%_'
    for char in replace_with_separator:
        text = text.replace(char, separator)

    # Remove non-permitted characters and put everything to lowercase
    # Example: u'_ALVARO__justen%_' -> u'_alvaro__justen_'
    text = ''.join(char for char in text if char in permitted_chars).lower()

    # Remove double occurrencies of separator
    # Example: u'_alvaro__justen_' -> u'_alvaro_justen_'
    double_separator = separator + separator
    while double_separator in text:
        text = text.replace(double_separator, separator)

    # Strip separators
    # Example: u'_alvaro_justen_' -> u'alvaro_justen'
    return text.strip(separator)


def ipartition(iterable, partition_size):
    if not isinstance(iterable, Iterator):
        iterator = iter(iterable)
    else:
        iterator = iterable

    finished = False
    while not finished:
        data = []
        for _ in range(partition_size):
            try:
                data.append(next(iterator))
            except StopIteration:
                finished = True
                break
        if data:
            yield data


def get_filename_and_fobj(filename_or_fobj, mode='r', dont_open=False):
    if getattr(filename_or_fobj, 'read', None) is not None:
        fobj = filename_or_fobj
        filename = getattr(fobj, 'name', None)
    else:
        fobj = open(filename_or_fobj, mode=mode) if not dont_open else None
        filename = filename_or_fobj

    return filename, fobj


def make_unique_name(name, existing_names, name_format='{name}_{index}',
                     start=2):
    '''Return a unique name based on `name_format` and `name`.'''

    index = start
    new_name = name
    while new_name in existing_names:
        new_name = name_format.format(name=name, index=index)
        index += 1

    return new_name


def make_header(field_names, permit_not=False):
    'Return unique and slugged field names'

    slug_chars = SLUG_CHARS if not permit_not else SLUG_CHARS + '^'

    header = [slug(field_name, permitted_chars=slug_chars)
              for field_name in field_names]
    result = []
    for index, field_name in enumerate(header):
        if not field_name:
            field_name = 'field_{}'.format(index)
        elif field_name[0].isdigit():
            field_name = 'field_{}'.format(field_name)

        if field_name in result:
            field_name = make_unique_name(name=field_name,
                                          existing_names=result,
                                          start=2)
        result.append(field_name)

    return result


def create_table(data, meta=None, fields=None, skip_header=True,
                 import_fields=None, samples=None, force_types=None,
                 *args, **kwargs):
    # TODO: add auto_detect_types=True parameter
    table_rows = iter(data)
    sample_rows = []

    if fields is None:
        header = make_header(next(table_rows))

        if samples is not None:
            sample_rows = list(islice(table_rows, 0, samples))
        else:
            sample_rows = list(table_rows)

        fields = detect_types(header, sample_rows, *args, **kwargs)

        if force_types is not None:
            # TODO: optimize field detection (ignore fields on `force_types`)
            for field_name, field_type in force_types.items():
                fields[field_name] = field_type
    else:
        if not isinstance(fields, OrderedDict):
            raise ValueError('`fields` must be an `OrderedDict`')

        if skip_header:
            _ = next(table_rows)

        header = make_header(list(fields.keys()))
        fields = OrderedDict([(field_name, fields[key])
                              for field_name, key in zip(header, fields)])

    if import_fields is not None:
        # TODO: can optimize if import_fields is not None.
        #       Example: do not detect all columns
        import_fields = make_header(import_fields)

        diff = set(import_fields) - set(header)
        if diff:
            field_names = ', '.join('"{}"'.format(field) for field in diff)
            raise ValueError("Invalid field names: {}".format(field_names))

        new_fields = OrderedDict()
        for field_name in import_fields:
            new_fields[field_name] = fields[field_name]
        fields = new_fields

    table = Table(fields=fields, meta=meta)
    # TODO: put this inside Table.__init__
    for row in chain(sample_rows, table_rows):
        table.append({field_name: value
                      for field_name, value in zip(header, row)})

    return table


def prepare_to_export(table, export_fields=None, *args, **kwargs):
    # TODO: optimize for more used cases (export_fields=None)
    table_type = type(table)
    if table_type not in (FlexibleTable, Table):
        raise ValueError('Table type not recognized')

    if export_fields is None:
        # we use already slugged-fieldnames
        export_fields = table.field_names
    else:
        # we need to slug all the field names
        export_fields = make_header(export_fields)

    table_field_names = table.field_names
    diff = set(export_fields) - set(table_field_names)
    if diff:
        field_names = ', '.join('"{}"'.format(field) for field in diff)
        raise ValueError("Invalid field names: {}".format(field_names))

    yield export_fields

    if table_type is Table:
        field_indexes = list(map(table_field_names.index, export_fields))
        for row in table._rows:
            yield [row[field_index] for field_index in field_indexes]
    elif table_type is FlexibleTable:
        for row in table._rows:
            yield [row[field_name] for field_name in export_fields]


def serialize(table, *args, **kwargs):
    prepared_table = prepare_to_export(table, *args, **kwargs)

    field_names = next(prepared_table)
    yield field_names

    field_types = [table.fields[field_name] for field_name in field_names]
    for row in prepared_table:
        yield [field_type.serialize(value, *args, **kwargs)
               for value, field_type in zip(row, field_types)]


def export_data(filename_or_fobj, data, mode='w'):
    if filename_or_fobj is not None:
        _, fobj = get_filename_and_fobj(filename_or_fobj, mode=mode)
        fobj.write(data)
        fobj.flush()
        return fobj
    else:
        return data
