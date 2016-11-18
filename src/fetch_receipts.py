import os
import re
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from itertools import islice
from multiprocessing import Pool
from urllib.error import HTTPError
from urllib.request import urlretrieve

from humanize import naturalsize
import numpy as np
import pandas as pd


class Receipts:
    """Abstraction to a list of Receipts read from the datasets"""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REGEX = r'^[\d-]{11}(current-year|last-year|previous-years).xz$'

    def __init__(self, target):
        """
        :param target: (str) path to the directory to save the receipt image
        """
        self.target = target

    @property
    def datasets(self):
        """List generator with the full path of each CSV/dataset."""
        for file_name in os.listdir(self.DATA_DIR):
            if re.compile(self.REGEX).match(file_name):
                yield os.path.join(self.DATA_DIR, file_name)

    @property
    def all(self):
        """
        List generator with Receipt objects containing the path of the
        receipt image (to be used when saving it, for example) and the URL of
        the receipt at the Lower House servers.
        """
        dtype = {
            'document_id': np.str,
            'congressperson_id': np.str,
            'congressperson_document': np.str,
            'term_id': np.str,
            'cnpj_cpf': np.str,
            'reimbursement_number': np.str
        }
        for dataset in self.datasets:
            df = pd.read_csv(dataset, parse_dates=[16], dtype=dtype)
            rows = filter(self.is_valid, df.itertuples())
            yield from(Receipt(row, self.target) for row in rows)

    @staticmethod
    def is_valid(row):
        if str(row.document_id).lower() == 'nan':
            return False

        required_fields = (row.applicant_id, row.year, row.document_id)
        if any(map(pd.isnull, required_fields)):
            return False

        return True


class Receipt:

    def __init__(self, receipt, target):
        """
        :param receipt: a Pandas DataFrame row as a NamedTuple (see
        `itertuples` method)
        :param target: (str) path to the directory to save the receipt image
        """
        self.applicant_id = receipt.applicant_id
        self.year = receipt.year
        self.document_id = receipt.document_id
        self.target = target

    @property
    def path(self):
        """
        Returns the absolute path to the receipt (the path to be used when
        saving the file).
        """
        return os.path.join(
            os.path.abspath(self.target),
            str(self.applicant_id),
            str(self.year),
            str(self.document_id) + '.pdf'
        )

    @property
    def url(self):
        """
        Returns the URL of this receipt at the Lower House server.
        """
        base = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/'
        recipe = '{base}{applicant_id}/{year}/{document_id}.pdf'
        return recipe.format(
            base=base,
            applicant_id=self.applicant_id,
            year=self.year,
            document_id=self.document_id
        )


def run(target, limit=None):
    """
    :param target: (string) path to the directory to save the receipts images
    :param limit: (int) limit the amount of receipts to fecth (default: None)
    """
    progress = {
        'count': 0,
        'size': 0,
        'errors': list(),
        'skipped': list()
    }

    # check if target directory exists
    if not os.path.exists(target):
        raise RuntimeError('Directory {} does not exist'.format(target))
        sys.exit()

    # check if target directory is a directory (not a file)
    if not os.path.isdir(target):
        raise RuntimeError('{} is a file, not a directory'.format(target))
        sys.exit()

    # save receipts
    with Pool(processes=4) as pool:
        receipts = Receipts(target=target).all
        while True:
            receipts_slice = receipts
            if limit:
                receipts_slice = islice(receipts, limit - progress['count'])

            for status, receipt, meta in pool.imap(download, receipts_slice):
                progress = manage_progress(progress, status, receipt, meta)

            if not limit or progress['count'] >= limit:
                break

    return print_report(progress)


def manage_progress(progress, status, receipt, meta):
    """
    Given the current progress (dict) and the status, receipt and meta produced
    by `download` method, it returns a update version of the progress (dict)
    and print the current status for the user.
    """
    if status == 'ok':
        progress['count'] += 1
        progress['size'] += int(meta['Content-Length'])

    elif status == 'skipped':
        progress['skipped'].append(receipt.url)

    elif status == 'error':
        progress['errors'].append(receipt.url)

    raw_msg = '==> Downloaded {:,} files ({}). {}/{} skipped/errors           '
    msg = raw_msg.format(
        progress['count'],
        naturalsize(progress['size']),
        len(progress['skipped']),
        len(progress['errors'])
    )

    print(msg, end='\r')
    return progress


def download(receipt):
    """
    Downloads a receipt and returns a tuple.
    :param receipt: (Receipt) Receipt object
    :return: (tuple) containing:
        * a status message (str, 'ok', 'error' or 'skipped')
        * the Receipt object
        * meta information (responde header in case of success, error in case
          of error, or the receipt URL case it was skipped)
    """
    os.makedirs(os.path.dirname(receipt.path), exist_ok=True)
    if not os.path.exists(receipt.path):
        try:
            file_name, header = urlretrieve(receipt.url, receipt.path)
            return ('ok', receipt, header)
        except HTTPError as e:
            return ('error', receipt, repr(e))
    else:
        return 'skipped', receipt, receipt.url


def print_report(progress):
    """
    Display status information of the operation
    :param progress: (dict) progress info as created within `run` method
    """
    msg = '==> {:,} files downloaded ({})                                     '
    print(msg.format(progress['count'], naturalsize(progress['size'])))

    # print errors
    if progress['errors']:
        msg = '\n==> {:,} receipts could not be saved:'
        print(msg.format(len(progress['errors'])))
        for index, url in enumerate(progress['errors']):
            print('    {}. {}'.format(index + 1, url))

    # print skipped files (already existing)
    if progress['skipped']:
        msg = '\n==> {:,} receipts were skipped (probably they already exist)'
        print(msg.format(len(progress['skipped'])))
        for index, url in enumerate(progress['skipped']):
            print('    {}. {}'.format(index + 1, url))

if __name__ == '__main__':

    # set argparse
    description = """
    This script downloads the receipt images from the Lower House server.

    Be aware that downloading everything might use more than 1 TB of disk
    space.  Because of that you have to specify one `target` directory (where
    to save the files) and optionally you can run with `--limit` to limit the
    number of images to be downloaded.

    If the `target` directory exists and already has some saved receipts,
    these receipts will not be downloaded again (and they will not count when
    using `--limit` either).

    In other words, if you already have 42 receipts in your target folder,
    running the command with a limit of 8 will end up in a directory with 50
    files: the 42 you already had and 8 freshly downloaded ones.
    """
    parser = ArgumentParser(
        description=description,
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('target', help='Directory where images will be saved.')
    parser.add_argument('-l', '--limit', default=0, type=int,
                        help='Limit the number of receipts to be saved')
    args = parser.parse_args()

    run(args.target, args.limit)
