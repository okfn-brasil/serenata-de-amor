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

from collections import OrderedDict

from rows.table import Table
from rows.plugins.utils import create_table


def join(keys, tables):
    """Merge a list of `Table` objects using `keys` to group rows"""

    # Make new (merged) Table fields
    fields = OrderedDict()
    for table in tables:
        fields.update(table.fields)
    # TODO: may raise an error if a same field is different in some tables

    # Check if all keys are inside merged Table's fields
    fields_keys = set(fields.keys())
    for key in keys:
        if key not in fields_keys:
            raise ValueError('Invalid key: "{}"'.format(key))

    # Group rows by key, without missing ordering
    none_fields = lambda: OrderedDict({field: None for field in fields.keys()})
    data = OrderedDict()
    for table in tables:
        for row in table:
            row_key = tuple([getattr(row, key) for key in keys])
            if row_key not in data:
                data[row_key] = none_fields()
            data[row_key].update(row._asdict())

    merged = Table(fields=fields)
    merged.extend(data.values())
    return merged


def transform(fields, function, *tables):
    "Return a new table based on other tables and a transformation function"

    new_table = Table(fields=fields)

    for table in tables:
        for row in filter(bool, map(lambda row: function(row, table), table)):
            new_table.append(row)

    return new_table


def transpose(table, fields_column, *args, **kwargs):
    field_names = []
    new_rows = [{} for _ in range(len(table.fields) - 1)]
    for row in table:
        row = row._asdict()
        field_name = row[fields_column]
        field_names.append(field_name)
        del row[fields_column]
        for index, value in enumerate(row.values()):
            new_rows[index][field_name] = value

    table_rows = [[row[field_name] for field_name in field_names]
                  for row in new_rows]
    return create_table([field_names] + table_rows, *args, **kwargs)
