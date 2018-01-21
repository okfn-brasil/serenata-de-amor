# coding: utf-8

from __future__ import unicode_literals

import contextlib
import locale

import six

import rows.fields


@contextlib.contextmanager
def locale_context(name, category=locale.LC_ALL):

    old_name = locale.getlocale()
    if None not in old_name:
        old_name = '.'.join(old_name)
    if isinstance(name, six.text_type):
        name = str(name)

    if old_name != name:
        locale.setlocale(category, name)

    rows.fields.SHOULD_NOT_USE_LOCALE = False
    try:
        yield
    finally:
        if old_name != name:
            locale.setlocale(category, old_name)

    rows.fields.SHOULD_NOT_USE_LOCALE = True
