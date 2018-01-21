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

from rows.plugins.utils import create_table


def import_from_dicts(data, *args, **kwargs):
    'Import data from a list of dicts'

    headers = set()
    for row in data:
        headers.update(row.keys())
    headers = sorted(list(headers))

    data = [[row.get(header, None) for header in headers] for row in data]

    meta = {'imported_from': 'dicts', }
    return create_table([headers] + data, meta=meta, *args, **kwargs)


def export_to_dicts(table, *args, **kwargs):
    return [{key: getattr(row, key) for key in table.field_names}
            for row in table]
