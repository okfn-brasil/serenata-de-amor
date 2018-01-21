import re
from webassets.filter import (
    Filter,
    register_filter
)


class ReplaceFilter(Filter):
    """
        A filter that allows arbitrary search/replace of strings using a source
        regex and a replacement string. Unlike cssrewrite this works on strings
        which are not paths and can be used as an output filter.

        Usage:

            replace_static_urls = ReplaceFilter(
                pattern=r'\s*{{\s*STATIC_URL\s*}}\s*',
                repl=settings.STATIC_URL,
            )
    """

    name = 'replace'
    max_debug_level = None

    def __init__(self, pattern=None, repl=None, as_output=True, **kwargs):
        self.pattern = pattern
        self.repl = repl
        self.as_output = as_output

        super(ReplaceFilter, self).__init__(**kwargs)

    def unique(self):
        """ Return a hashable representation of the parameters to allow different instances of this filter. """
        return self.pattern, self.repl

    def _process(self, _in, out, **kwargs):
        out.write(re.sub(self.pattern, self.repl, _in.read()))

    def output(self, _in, out, **kwargs):
        if self.as_output:
            self._process(_in, out, **kwargs)
        else:
            out.write(_in.read())

    def input(self, _in, out, **kwargs):
        if self.as_output:
            out.write(_in.read())
        else:
            self._process(_in, out, **kwargs)


register_filter(ReplaceFilter)
