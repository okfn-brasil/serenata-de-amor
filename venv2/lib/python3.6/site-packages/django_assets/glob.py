"""Copied from python-glob2, made to work in a single file, to avoid
having a dependency.
"""


"""Filename matching with shell patterns.

fnmatch(FILENAME, PATTERN) matches according to the local convention.
fnmatchcase(FILENAME, PATTERN) always takes case in account.

The functions operate by translating the pattern into a regular
expression.  They cache the compiled regular expressions for speed.

The function translate(PATTERN) returns a regular expression
corresponding to PATTERN.  (It does not compile it.)
"""

import re
from webassets import six

__all__ = ["filter", "fnmatch", "fnmatchcase", "translate"]

_cache = {}
_MAXCACHE = 100

def _purge():
    """Clear the pattern cache"""
    _cache.clear()

def fnmatch(name, pat):
    """Test whether FILENAME matches PATTERN.

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char not in seq

    An initial period in FILENAME is not special.
    Both FILENAME and PATTERN are first case-normalized
    if the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).
    """

    import os
    name = os.path.normcase(name)
    pat = os.path.normcase(pat)
    return fnmatchcase(name, pat)

def fnmatch_filter(names, pat):
    """Return the subset of the list NAMES that match PAT"""
    import os,posixpath
    result=[]
    pat=os.path.normcase(pat)
    if not pat in _cache:
        res = translate(pat)
        if len(_cache) >= _MAXCACHE:
            _cache.clear()
        _cache[pat] = re.compile(res)
    match=_cache[pat].match
    if os.path is posixpath:
        # normcase on posix is NOP. Optimize it away from the loop.
        for name in names:
            m = match(name)
            if m:
                result.append((name, m.groups()))
    else:
        for name in names:
            m = match(os.path.normcase(name))
            if m:
                result.append((name, m.groups()))
    return result

def fnmatchcase(name, pat):
    """Test whether FILENAME matches PATTERN, including case.

    This is a version of fnmatch() which doesn't case-normalize
    its arguments.
    """

    if not pat in _cache:
        res = translate(pat)
        if len(_cache) >= _MAXCACHE:
            _cache.clear()
        _cache[pat] = re.compile(res)
    return _cache[pat].match(name) is not None

def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    i, n = 0, len(pat)
    res = ''
    while i < n:
        c = pat[i]
        i = i+1
        if c == '*':
            res = res + '(.*)'
        elif c == '?':
            res = res + '(.)'
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j+1
            if j < n and pat[j] == ']':
                j = j+1
            while j < n and pat[j] != ']':
                j = j+1
            if j >= n:
                res = res + '\\['
            else:
                stuff = pat[i:j].replace('\\','\\\\')
                i = j+1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                res = '%s([%s])' % (res, stuff)
        else:
            res = res + re.escape(c)
    return res + '\Z(?ms)'


"""Filename globbing utility."""

import sys
import os
import re


class Globber(object):

    listdir = staticmethod(os.listdir)
    isdir = staticmethod(os.path.isdir)
    islink = staticmethod(os.path.islink)
    exists = staticmethod(os.path.lexists)

    def walk(self, top, followlinks=False):
        """A simplified version of os.walk (code copied) that uses
        ``self.listdir``, and the other local filesystem methods.

        Because we don't care about file/directory distinctions, only
        a single list is returned.
        """
        try:
            names = self.listdir(top)
        except os.error:
            return

        items = []
        for name in names:
            items.append(name)

        yield top, items

        for name in items:
            new_path = os.path.join(top, name)
            if followlinks or not self.islink(new_path):
                for x in self.walk(new_path, followlinks):
                    yield x

    def glob(self, pathname, with_matches=False):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        """
        return list(self.iglob(pathname, with_matches))

    def iglob(self, pathname, with_matches=False):
        """Return an iterator which yields the paths matching a pathname
        pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        If ``with_matches`` is True, then for each matching path
        a 2-tuple will be returned; the second element if the tuple
        will be a list of the parts of the path that matched the individual
        wildcards.
        """
        result = self._iglob(pathname)
        if with_matches:
            return result
        return map(lambda s: s[0], result)

    def _iglob(self, pathname, rootcall=True):
        """Internal implementation that backs :meth:`iglob`.

        ``rootcall`` is required to differentiate between the user's call to
        iglob(), and subsequent recursive calls, for the purposes of resolving
        certain special cases of ** wildcards. Specifically, "**" is supposed
        to include the current directory for purposes of globbing, but the
        directory itself should never be returned. So if ** is the lastmost
        part of the ``pathname`` given the user to the root call, we want to
        ignore the current directory. For this, we need to know which the root
        call is.
        """

        # Short-circuit if no glob magic
        if not has_magic(pathname):
            if self.exists(pathname):
                yield pathname, ()
            return

        # If no directory part is left, assume the working directory
        dirname, basename = os.path.split(pathname)

        # If the directory is globbed, recurse to resolve.
        # If at this point there is no directory part left, we simply
        # continue with dirname="", which will search the current dir.
        if dirname and has_magic(dirname):
            # Note that this may return files, which will be ignored
            # later when we try to use them as directories.
            # Prefiltering them here would only require more IO ops.
            dirs = self._iglob(dirname, rootcall=False)
        else:
            dirs = [(dirname, ())]

        # Resolve ``basename`` expr for every directory found
        for dirname, dir_groups in dirs:
            for name, groups in self.resolve_pattern(
                dirname, basename, not rootcall):
                yield os.path.join(dirname, name), dir_groups + groups

    def resolve_pattern(self, dirname, pattern, globstar_with_root):
        """Apply ``pattern`` (contains no path elements) to the
        literal directory`` in dirname``.

        If pattern=='', this will filter for directories. This is
        a special case that happens when the user's glob expression ends
        with a slash (in which case we only want directories). It simpler
        and faster to filter here than in :meth:`_iglob`.
        """

        if isinstance(pattern, six.text_type) and not isinstance(dirname, six.text_type):
            dirname = six.u(dirname, sys.getfilesystemencoding() or
                                       sys.getdefaultencoding())

        # If no magic, short-circuit, only check for existence
        if not has_magic(pattern):
            if pattern == '':
                if self.isdir(dirname):
                    return [(pattern, ())]
            else:
                if self.exists(os.path.join(dirname, pattern)):
                    return [(pattern, ())]
            return []

        if not dirname:
            dirname = os.curdir

        try:
            if pattern == '**':
                # Include the current directory in **, if asked; by adding
                # an empty string as opposed to '.', be spare ourselves
                # having to deal with os.path.normpath() later.
                names = [''] if globstar_with_root else []
                for top, entries in self.walk(dirname):
                    _mkabs = lambda s: os.path.join(top[len(dirname)+1:], s)
                    names.extend(map(_mkabs, entries))
                    # Reset pattern so that fnmatch(), which does not understand
                # ** specifically, will only return a single group match.
                pattern = '*'
            else:
                names = self.listdir(dirname)
        except os.error:
            return []

        if pattern[0] != '.':
            # Remove hidden files by default, but take care to ensure
            # that the empty string we may have added earlier remains.
            # Do not filter out the '' that we might have added earlier
            names = filter(lambda x: not x or x[0] != '.', names)
        return fnmatch_filter(names, pattern)


default_globber = Globber()
glob = default_globber.glob
iglob = default_globber.iglob
del default_globber


magic_check = re.compile('[*?[]')

def has_magic(s):
    return magic_check.search(s) is not None
