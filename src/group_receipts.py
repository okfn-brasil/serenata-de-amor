import datetime
import os
import re
import pandas as pd
import numpy as np


class Reimbursements:

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, 'data')

    DATE = datetime.date.today().strftime('%Y-%m-%d')
    FILE_BASE_NAME = '{}-reimbursements.xz'.format(DATE)

    CSV_PARAMS = {
        'compression': 'xz',
        'encoding': 'utf-8',
        'index': False
    }

    def find_newest_file(self, name):
        date_regex = re.compile('\d{4}-\d{2}-\d{2}')

        matches = (date_regex.findall(f) for f in os.listdir(self.DATA_PATH))
        dates = sorted(set([l[0] for l in matches if l]), reverse=True)

        for date in dates:
            filename = '{}-{}.xz'.format(date, name)
            filepath = os.path.join(self.DATA_PATH, filename)
            if os.path.isfile(filepath):
                return filepath
        return None

    def read_csv(self, name):
        newest_file = self.find_newest_file(name)
        if newest_file is None:
            msg = 'Could not find the dataset for {}.'.format(newest_file)
            raise TypeError(msg)

        print('Loading {}…'.format(newest_file))
        dtype = {
            'document_id': np.str,
            'congressperson_id': np.str,
            'congressperson_document': np.str,
            'term_id': np.str,
            'cnpj_cpf': np.str,
            'reimbursement_number': np.str
        }
        return pd.read_csv(newest_file, dtype=dtype)

    @property
    def receipts(self):
        print('Merging all datasets…')
        datasets = ('current-year', 'last-year', 'previous-years')
        dataset = pd.DataFrame()
        data = (self.read_csv(name) for name in datasets)
        dataset = pd.concat(data)
        return dataset

    def group(self, receipts):
        print('Dropping rows without document_value or reimbursement_number…')
        subset = ('document_value', 'reimbursement_number')
        receipts = receipts.dropna(subset=subset)

        print('Grouping dataset by applicant_id, document_id and year…')
        receipt_with_id = receipts[(~receipts['document_id'].isnull()) &
                                   (~receipts['year'].isnull()) &
                                   (~receipts['applicant_id'].isnull())]
        keys = ('applicant_id', 'year', 'document_id')
        grouped = receipt_with_id.groupby(keys)
        return grouped

    def write_reimbursement_file(self, receipts):
        print('Casting changes to a new DataFrame…')
        df = pd.DataFrame(data=receipts)

        print('Writing it to file…')
        filepath = os.path.join(self.DATA_PATH, self.FILE_BASE_NAME)
        df.to_csv(filepath, **self.CSV_PARAMS)

        print('Done.')


if __name__ == '__main__':
    reimbursements = Reimbursements()
    df = reimbursements.group(reimbursements.receipts)
    reimbursements.write_reimbursement_file(df)