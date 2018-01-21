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

# General imports

import rows.plugins as plugins

from rows.operations import join, transform, transpose
from rows.table import Table, FlexibleTable
from rows.localization import locale_context


# Don't have dependencies or dependencies installed on `install_requires`

import_from_json = plugins.json.import_from_json
export_to_json = plugins.json.export_to_json

import_from_dicts = plugins.dicts.import_from_dicts
export_to_dicts = plugins.dicts.export_to_dicts

import_from_csv = plugins.csv.import_from_csv
export_to_csv = plugins.csv.export_to_csv

import_from_txt = plugins.txt.import_from_txt
export_to_txt = plugins.txt.export_to_txt

# Have dependencies

if plugins.html:
    import_from_html = plugins.html.import_from_html
    export_to_html = plugins.html.export_to_html

if plugins.xpath:
    import_from_xpath = plugins.xpath.import_from_xpath

if plugins.ods:
    import_from_ods = plugins.ods.import_from_ods

if plugins.sqlite:
    import_from_sqlite = plugins.sqlite.import_from_sqlite
    export_to_sqlite = plugins.sqlite.export_to_sqlite

if plugins.xls:
    import_from_xls = plugins.xls.import_from_xls
    export_to_xls = plugins.xls.export_to_xls

if plugins.xlsx:
    import_from_xlsx = plugins.xlsx.import_from_xlsx
    export_to_xlsx = plugins.xlsx.export_to_xlsx

if plugins.parquet:
    import_from_parquet = plugins.parquet.import_from_parquet


__version__ = '0.3.1'
