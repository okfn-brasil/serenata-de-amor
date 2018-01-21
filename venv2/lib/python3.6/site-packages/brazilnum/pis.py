#!/usr/bin/env python

from __future__ import absolute_import

import re
from random import randint

from .util import clean_id, pad_id

"""
Functions for working with Brazilian PIS/PASEP identifiers.

"""

NONDIGIT = re.compile(r'[^0-9]')
PIS_WEIGHTS = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def validate_pis(pis, autopad=True):
    """Check whether PIS/PASEP is valid. Optionally pad if too short."""
    pis = clean_id(pis)

    # all complete PIS/PASEP are 11 digits long
    if len(pis) < 11:
        if not autopad:
            return False
        pis = pad_pis(pis)

    elif len(pis) > 11:
        return False

    if pis == '00000000000':
        return False

    return int(pis[-1]) == _pis_check(pis)


def pis_check_digit(pis):
    """Find check digit needed to make a PIS/PASEP valid."""
    pis = clean_id(pis)
    if len(pis) < 10:
        raise ValueError(
            'PIS/PASEP must be at least 10 digits: {0}'.format(pis))
    return _pis_check(pis)


def pis_check_digits(pis):
    """Alias for pis_check_digit function. PIS/PASEP uses single digit."""
    return pis_check_digit(pis)


def format_pis(pis):
    """Applies typical 000.0000.000-0 formatting to PIS/PASEP."""
    pis = pad_pis(pis)
    fmt = '{0}.{1}.{2}-{3}'
    return fmt.format(pis[:3], pis[3:7], pis[7:10], pis[10])


def pad_pis(pis, validate=False):
    """Takes a PIS/PASEP that had leading zeros and pads it."""
    padded = pad_id(pis, '%0.011i')
    if validate:
        return padded, validate_pis(padded)
    return padded


def random_pis(formatted=True):
    """Create a random, valid PIS identifier."""
    pis = randint(1000000000, 9999999999)
    pis = str(pis) + str(pis_check_digit(pis))
    if formatted:
        return format_pis(pis)
    return pis


def _pis_check(pis):
    """Calculate check digit from string."""
    digits = [int(k) for k in pis[:11]]
    # find check digit
    cs = sum(w * k for w, k in zip(PIS_WEIGHTS, digits)) % 11
    return 0 if cs < 2 else 11 - cs
