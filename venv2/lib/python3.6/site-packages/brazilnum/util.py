
import re

"""
Helper functions for validating identifiers.

"""

NONDIGIT = re.compile(r'[^0-9]')


def clean_id(identifier):
    """Remove non-numeric characters from input."""
    if isinstance(identifier, int):
        return str(identifier)
    return NONDIGIT.sub('', identifier)


def pad_id(identifier, fmt):
    """Pad an identifier with leading zeros."""
    if not isinstance(identifier, int):
        identifier = clean_id(identifier)

        if identifier == '':
            identifier = 0
        else:
            identifier = int(identifier)

    return fmt % identifier
