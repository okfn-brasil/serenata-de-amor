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

from io import BytesIO

import six

import unicodecsv

from rows.plugins.utils import create_table, get_filename_and_fobj, serialize


sniffer = unicodecsv.Sniffer()
DELIMITERS_PY2 = (b',', b';', b'\t')
DELIMITERS_PY3 = (',', ';', '\t')

if six.PY2:
    def discover_dialect(sample, encoding):
        try:
            return sniffer.sniff(sample,
                                 delimiters=DELIMITERS_PY2)
        except unicodecsv.Error:
            # Could not detect dialect, fall back to 'excel'
            return unicodecsv.excel
elif six.PY3:
    def discover_dialect(sample, encoding):
        try:
            return sniffer.sniff(sample.decode(encoding),
                                 delimiters=DELIMITERS_PY3)
        except unicodecsv.Error:
            # Could not detect dialect, fall back to 'excel'
            return unicodecsv.excel


def import_from_csv(filename_or_fobj, encoding='utf-8', dialect=None,
                    sample_size=8192, *args, **kwargs):
    '''Import data from a CSV file

    If a file-like object is provided it MUST be in binary mode, like in
    `open(filename, mode='rb')`.
    '''

    filename, fobj = get_filename_and_fobj(filename_or_fobj, mode='rb')

    if dialect is None:
        cursor = fobj.tell()
        dialect = discover_dialect(fobj.read(sample_size), encoding)
        fobj.seek(cursor)

    reader = unicodecsv.reader(fobj, encoding=encoding, dialect=dialect)

    meta = {'imported_from': 'csv',
            'filename': filename,
            'encoding': encoding,}
    return create_table(reader, meta=meta, *args, **kwargs)


def export_to_csv(table, filename_or_fobj=None, encoding='utf-8',
                  dialect=unicodecsv.excel, *args, **kwargs):
    '''Export a `rows.Table` to a CSV file

    If a file-like object is provided it MUST be in binary mode, like in
    `open(filename, mode='wb')`.
    If not filename/fobj is provided, the function returns a string with CSV
    contents.
    '''
    # TODO: will work only if table.fields is OrderedDict
    # TODO: should use fobj? What about creating a method like json.dumps?

    if filename_or_fobj is not None:
        _, fobj = get_filename_and_fobj(filename_or_fobj, mode='wb')
    else:
        fobj = BytesIO()

    writer = unicodecsv.writer(fobj, encoding=encoding, dialect=dialect)
    for row in serialize(table, *args, **kwargs):
        writer.writerow(row)

    if filename_or_fobj is not None:
        fobj.flush()
        return fobj
    else:
        fobj.seek(0)
        result = fobj.read()
        fobj.close()
        return result
