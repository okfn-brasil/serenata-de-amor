# coding: utf-8
# Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""
:mod:`gfm.strikethrough` -- Strike-through support
==================================================

The :mod:`gfm.strikethrough` module provides GitHub-like syntax for
strike-through text, that is text between double tildes:
``some ~~strike-through'ed~~ text``

Typical usage
-------------

.. testcode::

   import markdown
   from gfm import StrikethroughExtension

   print(markdown.markdown("I ~~like~~ love you!",
                           extensions=[StrikethroughExtension()]))

.. testoutput::

   <p>I <del>like</del> love you!</p>

"""

from __future__ import unicode_literals

import markdown

STRIKE_RE = r'(~{2})(.+?)(~{2})'  # ~~strike~~


class StrikethroughExtension(markdown.Extension):
    """
    An extension that adds support for strike-through text between two ``~~``.
    """

    def extendMarkdown(self, md, md_globals):
        pattern = markdown.inlinepatterns.SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.add('gfm-strikethrough', pattern, '_end')
