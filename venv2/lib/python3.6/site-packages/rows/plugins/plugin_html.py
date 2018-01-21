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

try:
    from HTMLParser import HTMLParser  # Python 2
except:
    from html.parser import HTMLParser  # Python 3


try:
    from html import escape  # Python 3
except:
    from cgi import escape  # Python 2

import six

from lxml.html import document_fromstring
from lxml.etree import tostring as to_string, strip_tags

from rows.plugins.utils import (create_table, export_data,
                                get_filename_and_fobj, serialize)


unescape = HTMLParser().unescape


def _get_content(element):
    return (element.text if element.text is not None else '') + \
            ''.join(to_string(child, encoding=six.text_type)
                    for child in element.getchildren())


def _get_row(row, column_tag, preserve_html, properties):
    if not preserve_html:
        data = list(map(_extract_node_text, row.xpath(column_tag)))
    else:
        data = list(map(_get_content, row.xpath(column_tag)))

    if properties:
        data.append(dict(row.attrib))

    return data


def import_from_html(filename_or_fobj, encoding='utf-8', index=0,
                     ignore_colspan=True, preserve_html=False,
                     properties=False, table_tag='table', row_tag='tr',
                     column_tag='td|th', *args, **kwargs):

    filename, fobj = get_filename_and_fobj(filename_or_fobj, mode='rb')
    html = fobj.read().decode(encoding)
    html_tree = document_fromstring(html)
    tables = html_tree.xpath('//{}'.format(table_tag))
    table = tables[index]

    strip_tags(table, 'thead')
    strip_tags(table, 'tbody')
    row_elements = table.xpath(row_tag)

    table_rows = [_get_row(row,
                           column_tag=column_tag,
                           preserve_html=preserve_html,
                           properties=properties)
                  for row in row_elements]

    if properties:
        table_rows[0][-1] = 'properties'

    if preserve_html and kwargs.get('fields', None) is None:
        # The field names will be the first table row, so we need to strip HTML
        # from it even if `preserve_html` is `True` (it's `True` only for rows,
        # not for the header).
        table_rows[0] = list(map(_extract_node_text, row_elements[0]))

    max_columns = max(map(len, table_rows))
    if ignore_colspan:
        table_rows = [row for row in table_rows if len(row) == max_columns]

    meta = {'imported_from': 'html',
            'filename': filename,
            'encoding': encoding,}
    return create_table(table_rows, meta=meta, *args, **kwargs)


def export_to_html(table, filename_or_fobj=None, encoding='utf-8', *args,
                   **kwargs):
    serialized_table = serialize(table, *args, **kwargs)
    fields = next(serialized_table)
    result = ['<table>\n\n', '  <thead>\n', '    <tr>\n']
    header = ['      <th> {} </th>\n'.format(field) for field in fields]
    result.extend(header)
    result.extend(['    </tr>\n', '  </thead>\n', '\n', '  <tbody>\n', '\n'])
    for index, row in enumerate(serialized_table, start=1):
        css_class = 'odd' if index % 2 == 1 else 'even'
        result.append('    <tr class="{}">\n'.format(css_class))
        for value in row:
            result.extend(['      <td> ', escape(value), ' </td>\n'])
        result.append('    </tr>\n\n')
    result.append('  </tbody>\n\n</table>\n')
    html = ''.join(result).encode(encoding)

    return export_data(filename_or_fobj, html, mode='wb')


def _extract_node_text(node):
    'Extract text from a given lxml node'

    texts = map(six.text_type.strip,
                map(six.text_type,
                    map(unescape,
                        node.xpath('.//text()'))))
    return ' '.join(text for text in texts if text)


def count_tables(filename_or_fobj, encoding='utf-8', table_tag='table'):
    filename, fobj = get_filename_and_fobj(filename_or_fobj)
    html = fobj.read().decode(encoding)
    html_tree = document_fromstring(html)
    tables = html_tree.xpath('//{}'.format(table_tag))
    return len(tables)


def tag_to_dict(html):
    "Extract tag's attributes into a `dict`"

    element = document_fromstring(html).xpath('//html/body/child::*')[0]
    attributes = dict(element.attrib)
    attributes['text'] = element.text_content()
    return attributes


def extract_text(html):
    'Extract text from a given HTML'

    return _extract_node_text(document_fromstring(html))


def extract_links(html):
    'Extract the href values from a given HTML (returns a list of strings)'

    return document_fromstring(html).xpath('.//@href')
