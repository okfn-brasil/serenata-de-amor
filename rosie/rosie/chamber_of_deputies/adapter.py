import logging
import os
import re
from datetime import date
from functools import partial
from pathlib import Path

import dask.dataframe as dd
import numpy as np
import pandas as pd

from serenata_toolbox.chamber_of_deputies.reimbursements import Reimbursements
from serenata_toolbox.datasets import fetch


class Adapter:

    STARTING_YEAR = 2009
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
        'congressperson_document': np.str,
        'congressperson_id': np.str,
        'leg_of_the_trip': np.str,
        'party': np.str,
        'passenger': np.str,
        'remark_value': np.float,
        'remark_value': np.str,
        'subquota_group_description': np.str,
        'subquota_number': np.str,
        'term': np.str,
        'term_id': np.str,
        'total_value': np.float
    }

    def __init__(self, path, years=None):
        self.log = logging.getLogger(__name__)
        self.path = path

        if not years:
            next_year = date.today().year + 1
            years = range(self.STARTING_YEAR, next_year)

        self.years = tuple(reversed(years))

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
        return df.compute()

    @property
    def companies(self):
        self.log.info('Loading companies')
        path = Path(self.path) / self.COMPANIES_DATASET
        converters = {'cnpj': partial(re.sub, r'\D', '')}
        return dd.read_csv(path, encoding='utf-8', converters=converters)

    @property
    def reimbursements(self):
        df = None
        for year in self.years:
            path = str(Path(self.path) / f'reimbursements-{year}.csv')
            self.log.info(f'Loading reimbursements from {path}')
            year_df = dd.read_csv(path, dtype=self.DTYPE, encoding='utf-8')
            df = year_df if df is None else df.append(year_df)

        return df

    def update_datasets(self):
        self.update_companies()
        self.update_reimbursements()

    def update_companies(self):
        self.log.info('Updating companies')
        os.makedirs(self.path, exist_ok=True)
        fetch(self.COMPANIES_DATASET, self.path)

    def update_reimbursements(self):
        for year in self.years:
            self.log.info(f'Updating reimbursements from {year}')
            Reimbursements(year, self.path)()

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
        for field in ('issue_date', 'situation_date'):
            self.log.info(f'Coercing `{field}` fields to date data type')
            df[field] = pd.to_datetime(df[field], errors='coerce')
