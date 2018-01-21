# coding: utf-8
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""
:mod:`gfm` -- Base module for GitHub-Flavored Markdown
======================================================
"""

from gfm import autolink
from gfm import automail
from gfm import hidden_hilite
from gfm import semi_sane_lists
from gfm import spaced_link
from gfm import strikethrough
from gfm import tasklist

AutolinkExtension = autolink.AutolinkExtension
AutomailExtension = automail.AutomailExtension
HiddenHiliteExtension = hidden_hilite.HiddenHiliteExtension
SemiSaneListExtension = semi_sane_lists.SemiSaneListExtension
SpacedLinkExtension = spaced_link.SpacedLinkExtension
StrikethroughExtension = strikethrough.StrikethroughExtension
TaskListExtension = tasklist.TaskListExtension

__all__ = ['AutolinkExtension', 'AutomailExtension', 'HiddenHiliteExtension',
           'SemiSaneListExtension', 'SpacedLinkExtension',
           'StrikethroughExtension', 'TaskListExtension']
