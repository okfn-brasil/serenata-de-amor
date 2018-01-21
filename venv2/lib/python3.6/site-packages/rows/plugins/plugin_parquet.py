# coding: utf-8

# Copyright 2016 Álvaro Justen <https://github.com/turicas/rows/>
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

import logging

from collections import OrderedDict

from rows import fields
from rows.plugins.utils import create_table, get_filename_and_fobj


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logging.getLogger("parquet").addHandler(NullHandler())

import parquet


PARQUET_TO_ROWS = {
        parquet.parquet_thrift.Type.BOOLEAN: fields.BoolField,
        parquet.parquet_thrift.Type.BYTE_ARRAY: fields.BinaryField,
        parquet.parquet_thrift.Type.DOUBLE: fields.FloatField,
        parquet.parquet_thrift.Type.FIXED_LEN_BYTE_ARRAY: fields.BinaryField,
        parquet.parquet_thrift.Type.FLOAT: fields.FloatField,
        parquet.parquet_thrift.Type.INT32: fields.IntegerField,
        parquet.parquet_thrift.Type.INT64: fields.IntegerField,
        parquet.parquet_thrift.Type.INT96: fields.IntegerField,
}

def import_from_parquet(filename_or_fobj, *args, **kwargs):
    'Import data from a Parquet file'

    filename, fobj = get_filename_and_fobj(filename_or_fobj, mode='rb')

    # TODO: should look into `schema.converted_type` also
    types = OrderedDict([(schema.name, PARQUET_TO_ROWS[schema.type])
                         for schema in parquet._read_footer(fobj).schema
                         if schema.type is not None])
    header = list(types.keys())
    table_rows = list(parquet.reader(fobj))  # TODO: be lazy

    meta = {'imported_from': 'parquet', 'filename': filename,}
    return create_table([header] + table_rows, meta=meta, force_types=types,
                        *args, **kwargs)
