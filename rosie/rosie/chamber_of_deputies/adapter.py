import logging
import os
from datetime import date
from pathlib import Path
import re

import numpy as np
import pandas as pd
from urllib.error import HTTPError

from serenata_toolbox.chamber_of_deputies.reimbursements import Reimbursements
from serenata_toolbox.datasets import fetch


class Adapter:

    COMPANIES_DATASET = '2016-09-03-companies.xz'
    RENAME_COLUMNS = {
        'subquota_description': 'category',
        'total_net_value': 'net_value',
        'cnpj_cpf': 'recipient_id',
        'supplier': 'recipient'
    }
    DTYPE = {
        'applicant_id': np.str,
        'cnpj_cpf': np.str,
        'congressperson_id': np.str,
        'subquota_number': np.str
    }

    def __init__(self, path, starting_year):
        self.path = path
        self.starting_year = starting_year
        self.log = logging.getLogger(__name__)
        next_year = date.today().year + 1
        self.years = range(self.starting_year, next_year)

    @property
    def dataset(self):
        self.update_datasets()
        df = self.reimbursements.merge(
            self.companies,
            how='left',
            left_on='cnpj_cpf',
            right_on='cnpj'
        )
        self.prepare_dataset(df)
        self.log.info('Dataset ready! Rosie starts her analysis now :)')
        return df

    @property
    def companies(self):
        self.log.info('Loading companies')
        path = Path(self.path) / self.COMPANIES_DATASET
        df = pd.read_csv(path, dtype={'cnpj': np.str}, low_memory=False)
        df['cnpj'] = df['cnpj'].str.replace(r'\D', '')
        return df

    @property
    def reimbursements(self):
        years_pattern = ",".join(map(str, list(self.years)))
        paths = (
            str(path) for path in Path(self.path).glob(f"*reimbursements-[{years_pattern}]*.csv")
        )
        df = pd.DataFrame()

        for path in paths:
            self.log.info(f'Loading reimbursements from {path}')
            year_df = pd.read_csv(path, dtype=self.DTYPE, low_memory=False)
            df = df.append(year_df)

        return df

    def update_datasets(self):
        self.update_companies()
        self.update_reimbursements()

    def update_companies(self):
        self.log.info('Updating companies')
        os.makedirs(self.path, exist_ok=True)
        file_name = f"{self.path}/{self.COMPANIES_DATASET}"
        if not os.path.isfile(file_name):
            fetch(self.COMPANIES_DATASET, self.path)

    def update_reimbursements(self):
        for year in self.years:
            self.log.info(f'Updating reimbursements from {year}')
            try:
                Reimbursements(year, self.path)()
            except HTTPError as e:
                self.log.error(f'Could not update Reimbursements from year {year}: {e} - {e.filename}')

    def prepare_dataset(self, df):
        self.rename_categories(df)
        self.coerce_dates(df)
        self.rename_columns(df)

    def rename_columns(self, df):
        self.log.info('Renaming columns to Serenata de Amor standard')
        df.rename(columns=self.RENAME_COLUMNS, inplace=True)

    def rename_categories(self, df):
        self.log.info('Categorizing reimbursements')

        # There's no documented type for `3`, `4` and `5`, thus we assume it's
        # an input error until we hear back from Chamber of Deputies
        types = ('bill_of_sale', 'simple_receipt', 'expense_made_abroad')
        converters = {number: None for number in range(3, 6)}
        df['document_type'].replace(converters, inplace=True)
        df['document_type'] = df['document_type'].astype('category')
        df['document_type'].cat.rename_categories(types, inplace=True)

        # Some classifiers expect a more broad category name for meals
        rename = {'Congressperson meal': 'Meal'}
        df['subquota_description'] = df['subquota_description'].replace(rename)
        df['is_party_expense'] = df['congressperson_id'].isnull()

    def coerce_dates(self, df):
        for field, fmt in (('issue_date', '%Y-%m-%d'), ('situation_date', '%d/%m/%Y')):
            self.log.info(f'Coercing {field} column to date data type')
            df[field] = pd.to_datetime(df[field], format=fmt, errors='coerce')
