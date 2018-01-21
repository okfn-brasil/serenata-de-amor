# coding: utf-8
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""
:mod:`gfm.autolink` -- Turn URLs into links
===========================================

The :mod:`gfm.autolink` module provides an extension that turns all raw URLs
into marked-up links.

This is based on the `web-only URL regex`_ by John Gruber (public domain).

This regex seems to line up pretty closely with GitHub's URL matching.
Two cases were identified where they differ. In both cases, the
regex were slightly modified to bring it in line with GitHub's parsing:

* GitHub accepts FTP-protocol URLs;
* GitHub only accepts URLs with protocols or ``www.``, whereas Gruber's regex
  accepts things like ``foo.com/bar``.

Typical usage
-------------

.. testcode::

   import markdown
   from gfm import AutolinkExtension

   print(markdown.markdown("I love this http://example.org/ check it out",
                           extensions=[AutolinkExtension()]))

.. testoutput::

   <p>I love this <a href="http://example.org/">http://example.org/</a> check it out</p>


.. _web-only URL regex: http://daringfireball.net/2010/07/improved_regex_for_matching_urls

"""

from __future__ import unicode_literals

import re
import markdown


URL_RE = (r'(?i)\b((?:(?:ftp|https?)://|www\d{0,3}[.])(?:[^\s()<>]+|'
          r'\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()'
          r'<>]+\)))*\)|[^\s`!()\[\]{};:' + r"'" + r'".,<>?«»“”‘’]))')
PROTOCOL_RE = re.compile(r'^(ftp|https?)://', re.IGNORECASE)


# We can't re-use the built-in AutolinkPattern because we need to add protocols
# to links without them.
class AutolinkPattern(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        el = markdown.util.etree.Element('a')

        href = m.group(2)
        if not PROTOCOL_RE.match(href):
            href = 'http://%s' % href
        el.set('href', self.unescape(href))

        el.text = markdown.util.AtomicString(m.group(2))
        return el


class AutolinkExtension(markdown.Extension):
    """
    An extension that turns URLs into links.
    """

    def extendMarkdown(self, md, md_globals):
        autolink = AutolinkPattern(URL_RE, md)
        md.inlinePatterns.add('gfm-autolink', autolink, '_end')
