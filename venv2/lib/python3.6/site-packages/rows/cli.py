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

# TODO: define exit codes
# TODO: move default options to base command
# TODO: may move all 'destination' to '--output'
# TODO: test this whole module
# TODO: add option to pass 'create_table' options in command-line (like force
#       fields)

import shlex
import sqlite3
import sys

from io import BytesIO

import click
import requests.exceptions

import rows

from rows.utils import (detect_source, export_to_uri, import_from_source,
                        import_from_uri)
from rows.plugins.utils import make_header


DEFAULT_INPUT_ENCODING = 'utf-8'
DEFAULT_OUTPUT_ENCODING = 'utf-8'
DEFAULT_INPUT_LOCALE = 'C'
DEFAULT_OUTPUT_LOCALE = 'C'


def _import_table(source, encoding, verify_ssl=True, *args, **kwargs):
    try:
        table = import_from_uri(source,
                                default_encoding=DEFAULT_INPUT_ENCODING,
                                verify_ssl=verify_ssl,
                                encoding=encoding, *args, **kwargs)
    except requests.exceptions.SSLError:
        click.echo('ERROR: SSL verification failed! '
                   'Use `--verify-ssl=no` if you want to ignore.', err=True)
        sys.exit(2)
    else:
        return table

def _get_field_names(field_names, table_field_names, permit_not=False):
    new_field_names = make_header(field_names.split(','),
                                  permit_not=permit_not)
    if not permit_not:
        diff = set(new_field_names) - set(table_field_names)
    else:
        diff = set(field_name.replace('^', '')
                   for field_name in new_field_names) - set(table_field_names)

    if diff:
        missing = ', '.join(['"{}"'.format(field) for field in diff])
        click.echo('Table does not have fields: {}'.format(missing), err=True)
        sys.exit(1)
    else:
        return new_field_names


@click.group()
@click.version_option(version=rows.__version__, prog_name='rows')
def cli():
    pass


@cli.command(help='Convert table on `source` URI to `destination`')
@click.option('--input-encoding')
@click.option('--output-encoding')
@click.option('--input-locale')
@click.option('--output-locale')
@click.option('--verify-ssl', default=True, type=bool)
@click.option('--order-by')
@click.argument('source')
@click.argument('destination')
def convert(input_encoding, output_encoding, input_locale, output_locale,
            verify_ssl, order_by, source, destination):

    # TODO: may use sys.stdout.encoding if output_file = '-'
    output_encoding = output_encoding or DEFAULT_OUTPUT_ENCODING

    if input_locale is not None:
        with rows.locale_context(input_locale):
            table = _import_table(source, encoding=input_encoding,
                                  verify_ssl=verify_ssl)
    else:
        table = _import_table(source, encoding=input_encoding,
                              verify_ssl=verify_ssl)

    if order_by is not None:
        order_by = _get_field_names(order_by,
                                    table.field_names,
                                    permit_not=True)
        # TODO: use complete list of `order_by` fields
        table.order_by(order_by[0].replace('^', '-'))

    if output_locale is not None:
        with rows.locale_context(output_locale):
            export_to_uri(table, destination, encoding=output_encoding)
    else:
        export_to_uri(table, destination, encoding=output_encoding)


@cli.command(help='Join tables from `source` URIs using `key(s)` to group '
                  'rows and save into `destination`')
@click.option('--input-encoding')
@click.option('--output-encoding')
@click.option('--input-locale')
@click.option('--output-locale')
@click.option('--verify-ssl', default=True, type=bool)
@click.option('--order-by')
@click.argument('keys')
@click.argument('sources', nargs=-1, required=True)
@click.argument('destination')
def join(input_encoding, output_encoding, input_locale, output_locale,
         verify_ssl, order_by, keys, sources, destination):

    # TODO: may use sys.stdout.encoding if output_file = '-'
    output_encoding = output_encoding or DEFAULT_OUTPUT_ENCODING
    keys = [key.strip() for key in keys.split(',')]

    if input_locale is not None:
        with rows.locale_context(input_locale):
            tables = [_import_table(source, encoding=input_encoding,
                                    verify_ssl=verify_ssl)
                     for source in sources]
    else:
        tables = [_import_table(source, encoding=input_encoding,
                                verify_ssl=verify_ssl)
                  for source in sources]

    result = rows.join(keys, tables)

    if order_by is not None:
        order_by = _get_field_names(order_by,
                                    result.field_names,
                                    permit_not=True)
        # TODO: use complete list of `order_by` fields
        result.order_by(order_by[0].replace('^', '-'))

    if output_locale is not None:
        with rows.locale_context(output_locale):
            export_to_uri(result, destination, encoding=output_encoding)
    else:
        export_to_uri(result, destination, encoding=output_encoding)


@cli.command(name='sum',
             help='Sum tables from `source` URIs and save into `destination`')
@click.option('--input-encoding')
@click.option('--output-encoding')
@click.option('--input-locale')
@click.option('--output-locale')
@click.option('--verify-ssl', default=True, type=bool)
@click.option('--order-by')
@click.argument('sources', nargs=-1, required=True)
@click.argument('destination')
def sum_(input_encoding, output_encoding, input_locale, output_locale,
         verify_ssl, order_by, sources, destination):

    # TODO: may use sys.stdout.encoding if output_file = '-'
    output_encoding = output_encoding or DEFAULT_OUTPUT_ENCODING

    if input_locale is not None:
        with rows.locale_context(input_locale):
            tables = [_import_table(source, encoding=input_encoding,
                                    verify_ssl=verify_ssl)
                    for source in sources]
    else:
        tables = [_import_table(source, encoding=input_encoding,
                                verify_ssl=verify_ssl)
                  for source in sources]

    result = sum(tables)

    if order_by is not None:
        order_by = _get_field_names(order_by,
                                    result.field_names,
                                    permit_not=True)
        # TODO: use complete list of `order_by` fields
        result.order_by(order_by[0].replace('^', '-'))

    if output_locale is not None:
        with rows.locale_context(output_locale):
            export_to_uri(result, destination, encoding=output_encoding)
    else:
        export_to_uri(result, destination, encoding=output_encoding)


@cli.command(name='print', help='Print a table')
@click.option('--input-encoding')
@click.option('--output-encoding')
@click.option('--input-locale')
@click.option('--output-locale')
@click.option('--table-index', default=0)
@click.option('--verify-ssl', default=True, type=bool)
@click.option('--fields')
@click.option('--fields-except')
@click.option('--order-by')
@click.argument('source', required=True)
def print_(input_encoding, output_encoding, input_locale, output_locale,
           table_index, verify_ssl, fields, fields_except, order_by, source):

    if fields is not None and fields_except is not None:
        click.echo('ERROR: `--fields` cannot be used with `--fields-except`',
                   err=True)
        sys.exit(20)

    output_encoding = output_encoding or sys.stdout.encoding or \
                      DEFAULT_OUTPUT_ENCODING

    # TODO: may use `import_fields` for better performance
    if input_locale is not None:
        with rows.locale_context(input_locale):
            table = _import_table(source, encoding=input_encoding,
                                  verify_ssl=verify_ssl,
                                  index=table_index)
    else:
        table = _import_table(source, encoding=input_encoding,
                              verify_ssl=verify_ssl,
                              index=table_index)

    table_field_names = table.field_names
    if fields is not None:
        fields = _get_field_names(fields, table_field_names)
    if fields_except is not None:
        fields_except = _get_field_names(fields_except, table_field_names)

    # TODO: should set `export_fields = None` if `--fields` and
    # `--fields-except` are `None`
    if fields is not None and fields_except is None:
        export_fields = fields
    elif fields is not None and fields_except is not None:
        export_fields = list(fields)
        for field_to_remove in fields_except:
            export_fields.remove(field_to_remove)
    elif fields is None and fields_except is not None:
        export_fields = list(table_field_names)
        for field_to_remove in fields_except:
            export_fields.remove(field_to_remove)
    else:
        export_fields = table_field_names

    if order_by is not None:
        order_by = _get_field_names(order_by,
                                    table_field_names,
                                    permit_not=True)
        # TODO: use complete list of `order_by` fields
        table.order_by(order_by[0].replace('^', '-'))

    fobj = BytesIO()
    if output_locale is not None:
        with rows.locale_context(output_locale):
            rows.export_to_txt(table, fobj, encoding=output_encoding,
                               export_fields=export_fields)
    else:
        rows.export_to_txt(table, fobj, encoding=output_encoding,
                           export_fields=export_fields)

    fobj.seek(0)
    # TODO: may pass unicode to click.echo if output_encoding is not provided
    click.echo(fobj.read())


@cli.command(name='query', help='Query a table using SQL')
@click.option('--input-encoding')
@click.option('--output-encoding')
@click.option('--input-locale')
@click.option('--output-locale')
@click.option('--verify-ssl', default=True, type=bool)
@click.option('--fields')
@click.option('--output')
@click.argument('query', required=True)
@click.argument('sources', nargs=-1, required=True)
def query(input_encoding, output_encoding, input_locale, output_locale,
          verify_ssl, fields, output, query, sources):

    # TODO: may use sys.stdout.encoding if output_file = '-'
    output_encoding = output_encoding or sys.stdout.encoding or \
                      DEFAULT_OUTPUT_ENCODING

    if not query.lower().startswith('select'):
        field_names = '*' if fields is None else fields
        table_names = ', '.join(['table{}'.format(index)
                                 for index in range(1, len(sources) + 1)])
        query = 'SELECT {} FROM {} WHERE {}'.format(field_names, table_names,
                                                    query)

    if len(sources) == 1:
        source = detect_source(sources[0], verify_ssl=verify_ssl)

        if source.plugin_name != 'sqlite':
            if input_locale is not None:
                with rows.locale_context(input_locale):
                    table = import_from_source(source, DEFAULT_INPUT_ENCODING)
            else:
                table = import_from_source(source, DEFAULT_INPUT_ENCODING)

            sqlite_connection = sqlite3.Connection(':memory:')
            rows.export_to_sqlite(table,
                                  sqlite_connection,
                                  table_name='table1')
            result = rows.import_from_sqlite(sqlite_connection, query=query)

        else:
            # Optimization: query the SQLite database directly
            result = import_from_source(source,
                                        DEFAULT_INPUT_ENCODING,
                                        query=query)

    else:
        if input_locale is not None:
            with rows.locale_context(input_locale):
                tables = [_import_table(source, encoding=input_encoding,
                                        verify_ssl=verify_ssl)
                          for source in sources]
        else:
            tables = [_import_table(source, encoding=input_encoding,
                                    verify_ssl=verify_ssl)
                      for source in sources]

        sqlite_connection = sqlite3.Connection(':memory:')
        for index, table in enumerate(tables, start=1):
            rows.export_to_sqlite(table,
                                  sqlite_connection,
                                  table_name='table{}'.format(index))

        result = rows.import_from_sqlite(sqlite_connection, query=query)

    if output is None:
        fobj = BytesIO()
        if output_locale is not None:
            with rows.locale_context(output_locale):
                rows.export_to_txt(result, fobj, encoding=output_encoding)
        else:
            rows.export_to_txt(result, fobj, encoding=output_encoding)
        fobj.seek(0)
        click.echo(fobj.read())
    else:
        if output_locale is not None:
            with rows.locale_context(output_locale):
                export_to_uri(result, output, encoding=output_encoding)
        else:
            export_to_uri(result, output, encoding=output_encoding)


if __name__ == '__main__':
    cli()
