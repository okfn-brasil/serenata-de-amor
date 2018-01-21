from __future__ import absolute_import
import logging
import logging.handlers

from webassets.filter import Filter


__all__ = ('CSSUtils',)


class CSSUtils(Filter):
    """Minifies CSS by removing whitespace, comments etc., using the Python
    `cssutils <http://cthedot.de/cssutils/>`_ library.

    Note that since this works as a parser on the syntax level, so invalid
    CSS input could potentially result in data loss.
    """

    name = 'cssutils'

    def setup(self):
        import cssutils
        self.cssutils = cssutils

        # cssutils is unaware of many new CSS3 properties,
        # vendor-prefixes etc., and logs many non-fatal warnings
        # about them. These diagnostic messages are rather
        # useless, so disable everything that's non-fatal.
        cssutils.log.setLevel(logging.FATAL)

    def output(self, _in, out, **kw):
        sheet = self.cssutils.parseString(_in.read())
        self.cssutils.ser.prefs.useMinified()
        out.write(sheet.cssText.decode('utf-8'))
