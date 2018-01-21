#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import absolute_import

from .util import clean_id

"""
Functions for working with Brazilian municipality (municipio) codes.

"""

MUNI_WEIGHTS = [1, 2, 1, 2, 1, 2]

# there are 9 IBGE municipal codes with invalid check digits;
# see, http://www.sefaz.al.gov.br/nfe/notas_tecnicas/NT2008.004.pdf
SHIM = {
    '2201919': 9,  # Bom Princípio do Piauí, PI
    '2201988': 8,  # Brejo do Piauí, PI
    '2202251': 1,  # Canavieira, PI
    '2611533': 3,  # Quixaba, PE
    '3117836': 6,  # Cônego Marinho, MG
    '3152131': 1,  # Ponto Chique, MG
    '4305871': 1,  # Coronel Barros, RS
    '5203939': 9,  # Buriti de Goiás, GO
    '5203962': 2,  # Buritinópolis, GO
}


def validate_muni(muni):
    """Check whether municipio code is valid."""
    muni = clean_id(muni)
    # municipal codes are 7 digits long, and cannot start with 0
    if len(muni) != 7:
        return False

    if muni[0] == '0':
        return False

    digits = [int(k) for k in muni]
    valid = _muni_check(digits[:-1]) == digits[-1]
    return valid or muni in SHIM  # need to check exceptions list


def muni_check_digit(muni):
    """Find check digit needed to make a valid municipio code."""
    muni = clean_id(muni)
    if len(muni) < 6:
        raise ValueError('Municipio must have at least 6 digits: {0}'
                         .format(muni))
    if muni in SHIM:
        return SHIM[muni]

    digits = [int(k) for k in muni[:7]]
    return _muni_check(digits)


def _muni_check(digits):
    """Calculate check digit from iterable of integers."""
    digmul = (w * k for w, k in zip(MUNI_WEIGHTS, digits))
    digsum = sum(n if n < 10 else 1 + (n % 10) for n in digmul)
    modulo = digsum % 10
    return 0 if modulo == 0 else 10 - modulo
