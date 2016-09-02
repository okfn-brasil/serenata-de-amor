import os
import re
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import namedtuple
from urllib.error import HTTPError
from urllib.request import urlretrieve

from humanize import naturalsize
import numpy as np
import pandas as pd

Receipt = namedtuple('Receipt', ['path', 'url'])


class FetchReceipts:

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REGEX = r'^[\d-]{11}(current-year|last-year|previous-years).xz$'

    def __init__(self, target, limit=None):
        """
        :param target: (str) path to the directory where images will be saved
        :param limit: (int) limit the amount of files to save
        """

        # check if target directory exists
        if not os.path.exists(target):
            raise RuntimeError('Directory {} does not exist'.format(target))
            sys.exit()

        # check if target directory is a directory (not a file)
        if not os.path.isdir(target):
            raise RuntimeError('{} is a file, not a directory'.format(target))
            sys.exit()

        # dtype to be used by pandas (inside self.parse)
        self.dtype = {
            'document_id': np.str,
            'congressperson_id': np.str,
            'congressperson_document': np.str,
            'term_id': np.str,
            'cnpj_cpf': np.str,
            'reimbursement_number': np.str
        }

        # save receipts
        self.limit = limit
        self.target = target
        self.progress = {
            'count': 0,
            'size': 0,
            'errors': list(),
            'skipped': list()
        }
        for receipt in self.receipts:
            if not self.limit or self.progress['count'] < self.limit:
                self.save(receipt)
            else:
                break

        # print errors
        if self.progress['errors']:
            errors = self.progress['errors']
            print('\n==> {} receipts could not be saved:'.format(len(errors)))
            for index, url in enumerate(errors):
                print('    {}. {}'.format(index + 1, url))

        # print skipped files (already existing)
        if self.progress['skipped']:
            skipped = self.progress['skipped']
            msg = '\n==> {} receipts were skipped, probably they already exist'
            print(msg.format(len(skipped)))
            for index, url in enumerate(skipped):
                print('    {}. {}'.format(index + 1, url))


    @property
    def datasets(self):
        """List generator with the full path of each CSV/dataset."""
        for file_name in os.listdir(self.DATA_DIR):
            if re.compile(self.REGEX).match(file_name):
                yield os.path.join(self.DATA_DIR, file_name)

    @property
    def receipts(self):
        """
        List generator with Receipt named tuples containing the path of the
        receipt image (to be used when saving it, for example) and the URL of
        the receipt at the Lower House servers.
        """
        for dataset in self.datasets:
            data = pd.read_csv(dataset, parse_dates=[16], dtype=self.dtype)
            for row in data.itertuples():
                yield Receipt(self.receipt_path(row), self.receipt_url(row))

    def save(self, receipt):
        """Get a receipt named tuple and save it to the target directory"""
        os.makedirs(os.path.dirname(receipt.path), exist_ok=True)
        if not os.path.exists(receipt.path):
            try:
                file_name, header = urlretrieve(receipt.url, receipt.path)
                self.progress['count'] += 1
                self.progress['size'] += int(header['Content-Length'])
                raw_msg = '==> Downloaded {} files ({})                       '
                msg = raw_msg.format(
                    self.progress['count'],
                    naturalsize(self.progress['size'])
                )
                print(msg, end='\r')
            except HTTPError:
                self.progress['errors'].append(receipt.url)
        else:
            self.progress['skipped'].append(receipt.url)

    def receipt_path(self, row):
        """
        Given a Pandas DataFrame row as a NamedTuple (see `itertuples` method),
        it returns the absolute path to the receipt, path to be used when
        saving the file.
        """
        return os.path.join(
            os.path.abspath(self.target),
            str(row.applicant_id),
            str(row.year),
            str(row.document_id) + '.pdf'
        )

    @staticmethod
    def receipt_url(row):
        """
        Given a Pandas DataFrame row as a NamedTuple (see `itertuples` method),
        it returns the URL of this receipt at the Lower House server.
        """
        base = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/'
        recipe = '{base}{applicant_id}/{year}/{document_id}.pdf'
        return recipe.format(
            base=base,
            applicant_id=row.applicant_id,
            year=row.year,
            document_id=row.document_id
        )


if __name__ == '__main__':

    # set argparse
    description = """
    This script downloads the receipt images from the Lower House server.

    Be aware that downloading everything might use more than 1 TB of disk
    space.  Because of that you have to specify one `target` directory (where
    to save the files) and optionally you can specify with `--limit` the number
    of images to be downloaded.

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

    # run
    FetchReceipts(args.target, args.limit)
