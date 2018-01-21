"""
    oauthlib
    ~~~~~~~~

    A generic, spec-compliant, thorough implementation of the OAuth
    request-signing logic.

    :copyright: (c) 2011 by Idan Gazit.
    :license: BSD, see LICENSE for details.
"""

__author__ = 'The OAuthlib Community'
__version__ = '2.0.7'


import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

logging.getLogger('oauthlib').addHandler(NullHandler())
