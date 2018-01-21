"""Unfortunately, Sphinx's autodoc module does not allow us to extract
the docstrings from the various environment config properties and
displaying them under a custom title. Instead, it will always put the
docstrings under a "Environment.foo" header.

This module is a hack to work around the issue while avoiding to duplicate
the actual docstrings.
"""

from webassets import Environment

class docwrap(object):
    def __init__(self, object, append=None):
        self.__doc__ = object.__doc__ if object else ''
        if append:
            # Add to the docstring, maintaining the proper indentation
            # so that the reST will be formatted correctly.
            try:
                last_line = self.__doc__.splitlines()[-1]
                indent = last_line[-len(last_line.lstrip()):]
                append = "\n".join(map(lambda s: indent+s, append.splitlines()))
            except IndexError:
                pass
            self.__doc__ += append


ASSETS_DEBUG = Environment.debug
ASSETS_CACHE = Environment.cache
ASSETS_AUTO_BUILD = Environment.auto_build
ASSETS_URL_EXPIRE = Environment.url_expire
ASSETS_MANIFEST = Environment.manifest
ASSETS_VERSIONS = Environment.versions
ASSETS_URL = docwrap(Environment.url, """\n\nBy default, ``STATIC_URL``
will be used for this, or the older ``MEDIA_URL`` setting.""")
ASSETS_ROOT = docwrap(Environment.directory, """\n\nBy default,
``STATIC_ROOT`` will be used for this, or the older ``MEDIA_ROOT``
setting.""")
