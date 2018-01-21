#!/usr/bin/env python

from __future__ import absolute_import

import random
from collections import namedtuple

from .util import clean_id, pad_id

"""
Functions for working with Brazilian company identifiers (CNPJ).

"""

CNPJ_FIRST_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_SECOND_WEIGHTS = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ = namedtuple('CNPJ', ['cnpj', 'firm', 'establishment', 'check', 'valid'])


def validate_cnpj(cnpj, autopad=True):
    """Check whether CNPJ is valid. Optionally pad if too short."""
    cnpj = clean_id(cnpj)

    # all complete CNPJ are 14 digits long
    if len(cnpj) < 14:
        if not autopad:
            return False
        cnpj = pad_cnpj(cnpj)

    elif len(cnpj) > 14:
        return False

    # 0 is invalid; smallest valid CNPJ is 191
    if cnpj == '00000000000000':
        return False

    digits = [int(k) for k in cnpj[:13]]  # identifier digits
    # validate the first check digit
    cs = sum(w * k for w, k in zip(CNPJ_FIRST_WEIGHTS, digits[:-1])) % 11
    cs = 0 if cs < 2 else 11 - cs
    if cs != int(cnpj[12]):
        return False  # first check digit is not correct
    # validate the second check digit
    cs = sum(w * k for w, k in zip(CNPJ_SECOND_WEIGHTS, digits)) % 11
    cs = 0 if cs < 2 else 11 - cs
    if cs != int(cnpj[13]):
        return False  # second check digit is not correct
    # both check digits are correct
    return True


def cnpj_check_digits(cnpj):
    """Find two check digits needed to make a CNPJ valid."""
    cnpj = clean_id(cnpj)
    if len(cnpj) < 12:
        raise ValueError('CNPJ must have at least 12 digits: {0}'.format(cnpj))
    digits = [int(k) for k in cnpj[:13]]
    # find the first check digit
    cs = sum(w * k for w, k in zip(CNPJ_FIRST_WEIGHTS, digits)) % 11
    check = 0 if cs < 2 else 11 - cs
    # find the second check digit
    digits.append(check)
    cs = sum(w * k for w, k in zip(CNPJ_SECOND_WEIGHTS, digits)) % 11
    if cs < 2:
        return check, 0
    return check, 11 - cs


def cnpj_from_firm_id(firm, establishment='0001', formatted=False):
    """Takes first 8 digits of a CNPJ (firm identifier) and builds a valid,
       complete CNPJ by appending an establishment identifier and calculating
       necessary check digits.
    """
    cnpj = clean_id('{0}{1}'.format(firm, establishment))
    checks = ''.join([str(k) for k in cnpj_check_digits(cnpj)])
    if not formatted:
        return cnpj + checks
    else:
        return format_cnpj(cnpj + checks)


def format_cnpj(cnpj):
    """Applies typical 00.000.000/0000-00 formatting to CNPJ."""
    cnpj = pad_cnpj(cnpj)
    fmt = '{0}.{1}.{2}/{3}-{4}'
    return fmt.format(cnpj[:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:])


def pad_cnpj(cnpj, validate=False):
    """Takes a CNPJ and pads it with leading zeros."""
    padded = pad_id(cnpj, '%0.014i')
    if validate:
        return padded, validate_cnpj(padded)
    return padded


def parse_cnpj(cnpj, formatted=True):
    """Split CNPJ into firm, establishment, and check digits, and validate."""
    cnpj, valid = pad_cnpj(cnpj, validate=True)
    estbl, check = cnpj[8:12], cnpj[12:]
    if formatted:
        cnpj = format_cnpj(cnpj)
        firm = cnpj[:10]
        return CNPJ(cnpj, firm, estbl, check, valid)
    else:
        firm = cnpj[:8]
        check = tuple(int(k) for k in check)
        return CNPJ(int(cnpj), int(firm), int(estbl), check, valid)


def random_cnpj(formatted=True):
    """Create a random, valid CNPJ identifier."""
    firm = random.randint(10000000, 99999999)
    establishment = random.choice(['0001', '0002', '0003', '0004', '0005'])
    cnpj = cnpj_from_firm_id(firm, establishment)
    if formatted:
        return format_cnpj(cnpj)
    return cnpj
