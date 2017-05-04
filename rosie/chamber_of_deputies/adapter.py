import os

import numpy as np
import pandas as pd
from serenata_toolbox.chamber_of_deputies.chamber_of_deputies_dataset import ChamberOfDeputiesDataset
from serenata_toolbox.datasets import fetch


COLUMNS = {
    'category': 'subquota_description',
    'net_value': 'total_net_value',
    'recipient_id': 'cnpj_cpf',
    'recipient': 'supplier',
}


class Adapter:
    COMPANIES_DATASET = '2016-09-03-companies.xz'

    def __init__(self, path):
        self.path = path

    @property
    def dataset(self):
        self.update_datasets()
        self.get_reimbursements()
        companies = self.get_companies()
        self._dataset = self._dataset.merge(companies,
                                            how='left',
                                            left_on='cnpj_cpf',
                                            right_on='cnpj')
        self.prepare_dataset()
        return self._dataset

    def prepare_dataset(self):
        self.rename_columns()
        self.rename_categories()

    def rename_columns(self):
        columns = {v: k for k, v in COLUMNS.items()}
        self._dataset.rename(columns=columns, inplace=True)

    def rename_categories(self):
        # There's no documented type for `3`, thus we assume it's an input error
        self._dataset['document_type'].replace({3: None}, inplace=True)
        self._dataset['document_type'] = self._dataset['document_type'].astype(
            'category')
        types = ['bill_of_sale', 'simple_receipt', 'expense_made_abroad']
        self._dataset['document_type'].cat.rename_categories(
            types, inplace=True)
        # Classifiers expect a more broad category name for meals
        self._dataset['category'] = self._dataset['category'].replace(
            {'Congressperson meal': 'Meal'})
        self._dataset['is_party_expense'] = \
            self._dataset['congressperson_id'].isnull()

    def update_datasets(self):
        os.makedirs(self.path, exist_ok=True)
        chamber_of_deputies = ChamberOfDeputiesDataset(self.path)
        chamber_of_deputies.fetch()
        chamber_of_deputies.convert_to_csv()
        chamber_of_deputies.translate()
        chamber_of_deputies.clean()
        fetch(self.COMPANIES_DATASET, self.path)

    def get_reimbursements(self):
        path = os.path.join(self.path, 'reimbursements.xz')
        self._dataset = pd.read_csv(path,
                                    dtype={'applicant_id': np.str,
                                           'cnpj_cpf': np.str,
                                           'congressperson_id': np.str,
                                           'subquota_number': np.str},
                                    low_memory=False)
        self._dataset['issue_date'] = pd.to_datetime(
            self._dataset['issue_date'], errors='coerce')
        return self._dataset

    def get_companies(self):
        path = os.path.join(self.path, self.COMPANIES_DATASET)
        dataset = pd.read_csv(path, dtype={'cnpj': np.str}, low_memory=False)
        dataset['cnpj'] = dataset['cnpj'].str.replace(r'\D', '')
        dataset['situation_date'] = pd.to_datetime(
            dataset['situation_date'], errors='coerce')
        return dataset
