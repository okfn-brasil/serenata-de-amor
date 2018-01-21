# coding: utf-8
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""
:mod:`gfm.hidden_hilite` -- Fenced code blocks with no highlighting
====================================================================

The :mod:`gfm.hidden_hilite` module provides an extension that allows the use
of fenced code blocks without adding syntax highlighting or line numbers.

Typical usage
-------------

.. testcode::

   import markdown
   from gfm import HiddenHiliteExtension

   print(markdown.markdown("```\\nimport this\\nprint('foo')\\n```",
                           extensions=[HiddenHiliteExtension()]))

.. testoutput::

   <p><code>import this
   print('foo')</code></p>

"""

from markdown.extensions.codehilite import CodeHiliteExtension


class HiddenHiliteExtension(CodeHiliteExtension):
    """
    A subclass of CodeHiliteExtension that doesn't highlight on its own.
    """

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
