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

import zipfile

from decimal import Decimal

from lxml.etree import tostring as xml_to_string, fromstring as xml_from_string

from rows.plugins.utils import create_table, get_filename_and_fobj


def xpath(element, xpath, namespaces):
    return xml_from_string(xml_to_string(element)).xpath(xpath,
                                                         namespaces=namespaces)


def attrib(cell, namespace, name):
    return cell.attrib['{{{}}}{}'.format(namespace, name)]


def complete_with_None(lists, size):
    for element in lists:
        element.extend([None] * (size - len(element)))
        yield element


def import_from_ods(filename_or_fobj, index=0, *args, **kwargs):
    # TODO: import spreadsheet by name
    # TODO: unescape values

    filename, _ = get_filename_and_fobj(filename_or_fobj)

    ods_file = zipfile.ZipFile(filename)
    content_fobj = ods_file.open('content.xml')
    xml = content_fobj.read()  # will return bytes
    content_fobj.close()

    document = xml_from_string(xml)
    namespaces = document.nsmap
    spreadsheet = document.xpath('//office:spreadsheet',
                                 namespaces=namespaces)[0]
    tables = xpath(spreadsheet, '//table:table', namespaces)
    table = tables[index]

    table_rows_obj = xpath(table, '//table:table-row', namespaces)
    table_rows = []
    for row_obj in table_rows_obj:
        row = []
        for cell in xpath(row_obj, '//table:table-cell', namespaces):
            children = cell.getchildren()
            if not children:
                continue

            # TODO: evalute 'boolean' and 'time' types
            value_type = attrib(cell, namespaces['office'], 'value-type')
            if value_type == 'date':
                cell_value = attrib(cell, namespaces['office'], 'date-value')
            elif value_type == 'float':
                cell_value = attrib(cell, namespaces['office'], 'value')
            elif value_type == 'percentage':
                cell_value = attrib(cell, namespaces['office'], 'value')
                cell_value = Decimal(str(Decimal(cell_value) * 100)[:-2])
                cell_value = '{}%'.format(cell_value)
            elif value_type == 'string':
                try:
                    # get computed string (from formula, for example)
                    cell_value = attrib(cell, namespaces['office'],
                                        'string-value')
                except KeyError:
                    # computed string not present => get from <p>...</p>
                    cell_value = children[0].text
            else:  # value_type == some type we don't know
                cell_value = children[0].text

            try:
                repeat = attrib(cell, namespaces['table'],
                                'number-columns-repeated')
            except KeyError:
                row.append(cell_value)
            else:
                for _ in range(int(repeat)):
                    row.append(cell_value)

        if row:
            table_rows.append(row)

    max_length = max(len(row) for row in table_rows)
    full_rows = complete_with_None(table_rows, max_length)
    meta = {'imported_from': 'ods', 'filename': filename,}
    return create_table(full_rows, meta=meta, *args, **kwargs)
