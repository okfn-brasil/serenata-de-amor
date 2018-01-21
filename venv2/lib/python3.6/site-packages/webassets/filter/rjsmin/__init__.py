from __future__ import absolute_import
try:
    import rjsmin
except ImportError:
    from . import rjsmin


from webassets.filter import Filter


__all__ = ('RJSMin',)


class RJSMin(Filter):
    """Minifies Javascript by removing whitespace, comments, etc.

    Uses the `rJSmin library <http://opensource.perlig.de/rjsmin/>`_,
    which is included with webassets. However, if you have the external
    package installed, it will be used instead. You may want to do this
    to get access to the faster C-extension.

    Supported configuration options:

    RJSMIN_KEEP_BANG_COMMENTS (boolean)
        Keep bang-comments (comments starting with an exclamation mark).
    """

    name = 'rjsmin'
    options = {
        'keep_bang_comments': 'RJSMIN_KEEP_BANG_COMMENTS',
    }

    def output(self, _in, out, **kw):
        keep = self.keep_bang_comments or False
        out.write(rjsmin.jsmin(_in.read(), keep_bang_comments=keep))
