# coding: utf-8
# Copyright (c) 2016, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""
:mod:`gfm.tasklist` -- Task list support
========================================

The :mod:`gfm.tasklist` module provides GitHub-like support for task lists.
Those are normal lists with a checkbox-like syntax at the beginning of items
that will be converted to actual checkbox inputs. Nested lists are supported.

Example syntax::

   - [x] milk
   - [ ] eggs
   - [x] chocolate
   - [ ] if possible:
       1. [ ] solve world peace
       2. [ ] solve world hunger

.. NOTE::
   GitHub has support for updating the Markdown source text by toggling the
   checkbox (by clicking on it). This is not supported by this extension, as it
   requires server-side processing that is out of scope of a Markdown parser.

Available configuration options
-------------------------------

================== ============== ======== ===========
Name               Type           Default  Description
================== ============== ======== ===========
``unordered``      bool           ``True`` Set to ``False`` to disable parsing of unordered lists.
``ordered``        bool           ``True`` Set to ``False`` to disable parsing of ordered lists.
``max_depth``      integer        ∞        Set to a positive integer to stop parsing nested task
                                           lists that are deeper than this limit.
``list_attrs``     dict, callable ``{}``   Attributes to be added to the ``<ul>`` or ``<ol>`` element
                                           containing the items.
``item_attrs``     dict, callable ``{}``   Attributes to be added to the ``<li>`` element containing
                                           the checkbox. See `Item attributes`_.
``checkbox_attrs`` dict, callable ``{}``   Attributes to be added to the checkbox element.
                                           See `Checkbox attributes`_.
================== ============== ======== ===========

List attributes
***************

If option ``list_attrs`` is a *dict*, the key-value pairs will be applied to
the ``<ul>`` (resp. ``<ol>``) unordered (resp. ordered) list element, that is
the parent element of the ``<li>`` elements.

.. warning::

   These attributes are applied to all nesting levels of lists, that is,
   to both the root lists and their potential sub-lists, recursively.

   You can control this behavior by using a *callable* instead (see below).

If option ``list_attrs`` is a *callable*, it should be a function that respects
the following prototype::

   def function(list, depth: int) -> dict:

where:

- ``list`` is the ``<ul>`` or ``<ol>`` element;
- ``depth`` is the depth of this list relative to its root list (root lists have
  a depth of 1).

The returned *dict* items will be applied as HTML attributes to the list
element.

.. note::

   Thanks to this feature, you could apply attributes to root lists only.
   Take this code sample::

      import markdown
      from gfm import TaskListExtension

      def list_attr_cb(list, depth):
          if depth == 1:
              return {'class': 'tasklist'}
          return {}

      tl_ext = TaskListExtension(list_attrs=list_attr_cb)

      print(markdown.markdown(\"""
      - [x] some thing
      - [ ] some other
          - [ ] sub thing
          - [ ] sub other
      \""", extensions=[tl_ext]))

   In this example, only the root list will have the ``tasklist`` class
   attribute, not the one containing “sub” items.


Item attributes
***************

If option ``item_attrs`` is a *dict*, the key-value pairs will be applied to
the ``<li>`` element as its HTML attributes.

Example::

   item_attrs={'class': 'list-item'}

will result in::

   <li class="list-item">...</li>

If option ``item_attrs`` is a *callable*, it should be a function that
respects the following prototype::

   def function(parent, element, checkbox) -> dict:

where:

- ``parent`` is the ``<li>`` parent element;
- ``element`` is the ``<li>`` element;
- ``checkbox`` is the generated ``<input type="checkbox">`` element.

The returned *dict* items will be applied as HTML attributes to the ``<li>``
element containing the checkbox.

Checkbox attributes
*******************

If option ``checkbox_attrs`` is a *dict*, the key-value pairs will be applied to
the ``<input type="checkbox">`` element as its HTML attributes.

Example::

   checkbox_attrs={'class': 'list-cb'}

will result in::

   <li><input type="checkbox" class="list-cb"> ...</li>

If option ``checkbox_attrs`` is a *callable*, it should be a function that
respects the following prototype::

   def function(parent, element) -> dict:

where:

- ``parent`` is the ``<li>`` parent element;
- ``element`` is the ``<li>`` element.

The returned *dict* items will be applied as HTML attributes to the checkbox
element.

Typical usage
-------------

.. testcode::

   import markdown
   from gfm import TaskListExtension

   print(markdown.markdown(\"""
   - [x] milk
   - [ ] eggs
   - [x] chocolate
   - not a checkbox
   \""", extensions=[TaskListExtension()]))

.. testoutput::

   <ul>
   <li><input checked="checked" disabled="disabled" type="checkbox" /> milk</li>
   <li><input disabled="disabled" type="checkbox" /> eggs</li>
   <li><input checked="checked" disabled="disabled" type="checkbox" /> chocolate</li>
   <li>not a checkbox</li>
   </ul>

"""

from __future__ import unicode_literals

import markdown
from functools import reduce
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree

try:
    _string_type = unicode
except NameError:
    _string_type = str


def _to_list(obj):
    if isinstance(obj, _string_type):
        return [obj]
    if isinstance(obj, tuple):
        return list(obj)
    return obj


class TaskListProcessor(Treeprocessor):
    def __init__(self, ext):
        super(TaskListProcessor, self).__init__()
        self.ext = ext

    def run(self, root):
        ordered = self.ext.getConfig('ordered')
        unordered = self.ext.getConfig('unordered')
        if not ordered and not unordered:
            return root

        checked_pattern = _to_list(self.ext.getConfig('checked'))
        unchecked_pattern = _to_list(self.ext.getConfig('unchecked'))
        if not checked_pattern and not unchecked_pattern:
            return root

        prefix_length = reduce(max, (len(e) for e in checked_pattern +
                                     unchecked_pattern))

        item_attrs = self.ext.getConfig('item_attrs')
        list_attrs = self.ext.getConfig('list_attrs')
        base_cb_attrs = self.ext.getConfig('checkbox_attrs')
        max_depth = self.ext.getConfig('max_depth')
        if not max_depth:
            max_depth = float('inf')

        lists = set()
        stack = [(root, None, 0)]

        while stack:
            el, parent, depth = stack.pop()

            if (parent and el.tag == 'li' and
                    (parent.tag == 'ul' and unordered or
                     parent.tag == 'ol' and ordered)):
                depth += 1
                text = (el.text or '').lstrip()
                lower_text = text[:prefix_length].lower()
                found = False
                checked = False

                for p in checked_pattern:
                    if lower_text.startswith(p):
                        found = True
                        checked = True
                        text = text[len(p):]
                        break
                else:
                    for p in unchecked_pattern:
                        if lower_text.startswith(p):
                            found = True
                            text = text[len(p):]
                            break

                if found:
                    # Add root <ol> or <ul> element to the list set
                    if list_attrs:
                        lists.add((parent, depth))

                    # Checkbox attributes
                    attrs = {'type': 'checkbox', 'disabled': 'disabled'}
                    if checked:
                        attrs['checked'] = 'checked'
                    # Give user a chance to update checkbox attributes
                    attrs.update(base_cb_attrs(parent, el)
                                 if callable(base_cb_attrs)
                                 else base_cb_attrs)
                    checkbox = etree.Element('input', attrs)
                    checkbox.tail = text
                    # Prepend checkbox to <li>
                    el.text = ''
                    el.insert(0, checkbox)
                    # Give user a chance to update <li> attributes
                    for k, v in (item_attrs(parent, el, checkbox)
                                 if callable(item_attrs)
                                 else item_attrs).items():
                        el.set(k, v)

            if depth < max_depth:
                for child in el:
                    stack.append((child, el, depth))

        for list, depth in lists:
            for k, v in (list_attrs(list, depth) if callable(list_attrs)
                         else list_attrs).items():
                list.set(k, v)

        return root


class TaskListExtension(markdown.Extension):
    """
    An extension that supports GitHub task lists. Both ordered and unordered
    lists are supported and can be separately enabled. Nested lists are
    supported.

    Example::

       - [x] milk
       - [ ] eggs
       - [x] chocolate
       - [ ] if possible:
           1. [ ] solve world peace
           2. [ ] solve world hunger
    """

    def __init__(self, *args, **kwargs):
        self.config = {
            'ordered': [True, "Enable parsing of ordered lists"],
            'unordered': [True, "Enable parsing of unordered lists"],
            'checked': ['[x]', "The checked state pattern"],
            'unchecked': ['[ ]', "The unchecked state pattern"],
            'max_depth': [0, "Maximum list nesting depth (None for "
                             "unlimited)"],
            'list_attrs': [{}, "Additional attribute dict (or callable) to "
                               "add to the <ul> or <ol> element"],
            'item_attrs': [{}, "Additional attribute dict (or callable) to "
                               "add to the <li> element"],
            'checkbox_attrs': [{}, "Additional attribute dict (or callable) "
                                   "to add to the checkbox <input> element"],
        }
        super(TaskListExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        processor = TaskListProcessor(self)
        md.treeprocessors.add('gfm-tasklist', processor, '_end')
