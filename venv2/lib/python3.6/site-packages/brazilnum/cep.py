
from __future__ import absolute_import
from collections import namedtuple

from .util import clean_id

"""
Functions for working with Brazilian zipcodes.

"""


CEP = namedtuple('CEP', ['cep', 'region', 'subregion', 'sector', 'subsector',
                         'division', 'suffix'])


def format_cep(cep):
    """Applies typical 00000-000 formatting to CEP."""
    cep = clean_id(cep)
    dig = len(cep)

    if dig == 4 or dig == 5:
        cep = '0'*(5-dig) + cep + '000'
    elif dig == 7 or dig == 8:
        cep = '0'*(8-dig) + cep
    else:
        raise ValueError('Invalid CEP code: {0}'.format(cep))

    return '{0}-{1}'.format(cep[:-3], cep[-3:])


def parse_cep(cep, numeric=True):
    """Split CEP into region, sub-region, sector, subsector, division."""
    fmtcep = format_cep(cep)
    if numeric:
        cep = int(fmtcep.replace('-', ''))
        geo = [int(fmtcep[:i]) for i in range(1, 6)]
        suffix = int(fmtcep[-3:])
    else:
        cep = fmtcep
        geo = [fmtcep[:i] for i in range(1, 6)]
        suffix = fmtcep[-3:]

    return CEP(cep, geo[0], geo[1], geo[2], geo[3], geo[4], suffix)
