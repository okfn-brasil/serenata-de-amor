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

from rows.plugins.utils import (create_table, export_data,
                                get_filename_and_fobj, serialize)

DASH, PLUS, PIPE = '-', '+', '|'


def _max_column_sizes(field_names, table_rows):
    columns = zip(*([field_names] + table_rows))
    return {field_name: max(len(value) for value in column)
            for field_name, column in zip(field_names, columns)}


def import_from_txt(filename_or_fobj, encoding='utf-8', *args, **kwargs):
    # TODO: should be able to change DASH, PLUS and PIPE
    filename, fobj = get_filename_and_fobj(filename_or_fobj, mode='rb')
    contents = fobj.read().decode(encoding).strip().splitlines()

    # remove '+----+----+' lines
    contents = contents[1:-1]
    del contents[1]

    table_rows = [[value.strip() for value in row.split(PIPE)[1:-1]]
                  for row in contents]
    meta = {'imported_from': 'txt',
            'filename': filename,
            'encoding': encoding,}
    return create_table(table_rows, meta=meta, *args, **kwargs)


def export_to_txt(table, filename_or_fobj=None, encoding=None,
                  *args, **kwargs):
    '''Export a `rows.Table` to text

    This function can return the result as a string or save into a file (via
    filename or file-like object).

    `encoding` could be `None` if no filename/file-like object is specified,
    then the return type will be `six.text_type`.
    '''
    # TODO: should be able to change DASH, PLUS and PIPE
    # TODO: will work only if table.fields is OrderedDict

    serialized_table = serialize(table, *args, **kwargs)
    field_names = next(serialized_table)
    table_rows = list(serialized_table)
    max_sizes = _max_column_sizes(field_names, table_rows)

    dashes = [DASH * (max_sizes[field] + 2) for field in field_names]
    header = [field.center(max_sizes[field]) for field in field_names]
    header = '{} {} {}'.format(PIPE, ' {} '.format(PIPE).join(header), PIPE)
    split_line = PLUS + PLUS.join(dashes) + PLUS

    result = [split_line, header, split_line]
    for row in table_rows:
        values = [value.rjust(max_sizes[field_name])
                  for field_name, value in zip(field_names, row)]
        row_data = ' {} '.format(PIPE).join(values)
        result.append('{} {} {}'.format(PIPE, row_data, PIPE))
    result.extend([split_line, ''])
    data = '\n'.join(result)

    if encoding is not None:
        data = data.encode(encoding)

    return export_data(filename_or_fobj, data, mode='wb')
