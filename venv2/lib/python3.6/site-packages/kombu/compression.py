"""Compression utilities."""
from __future__ import absolute_import, unicode_literals

from kombu.utils.encoding import ensure_bytes

import zlib

_aliases = {}
_encoders = {}
_decoders = {}

__all__ = ['register', 'encoders', 'get_encoder',
           'get_decoder', 'compress', 'decompress']


def register(encoder, decoder, content_type, aliases=[]):
    """Register new compression method.

    Arguments:
        encoder (Callable): Function used to compress text.
        decoder (Callable): Function used to decompress previously
            compressed text.
        content_type (str): The mime type this compression method
            identifies as.
        aliases (Sequence[str]): A list of names to associate with
            this compression method.
    """
    _encoders[content_type] = encoder
    _decoders[content_type] = decoder
    _aliases.update((alias, content_type) for alias in aliases)


def encoders():
    """Return a list of available compression methods."""
    return list(_encoders)


def get_encoder(t):
    """Get encoder by alias name."""
    t = _aliases.get(t, t)
    return _encoders[t], t


def get_decoder(t):
    """Get decoder by alias name."""
    return _decoders[_aliases.get(t, t)]


def compress(body, content_type):
    """Compress text.

    Arguments:
        body (AnyStr): The text to compress.
        content_type (str): mime-type of compression method to use.
    """
    encoder, content_type = get_encoder(content_type)
    return encoder(ensure_bytes(body)), content_type


def decompress(body, content_type):
    """Decompress compressed text.

    Arguments:
        body (AnyStr): Previously compressed text to uncompress.
        content_type (str): mime-type of compression method used.
    """
    return get_decoder(content_type)(body)


register(zlib.compress,
         zlib.decompress,
         'application/x-gzip', aliases=['gzip', 'zlib'])
try:
    import bz2
except ImportError:
    pass  # Jython?
else:
    register(bz2.compress,
             bz2.decompress,
             'application/x-bz2', aliases=['bzip2', 'bzip'])
