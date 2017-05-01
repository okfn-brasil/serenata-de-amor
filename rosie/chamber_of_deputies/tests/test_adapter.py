import shutil
import os
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import patch
from shutil import copy2

import pandas as pd

from rosie.chamber_of_deputies.adapter import Adapter as subject_class
from rosie.chamber_of_deputies.adapter import COLUMNS as ADAPTER_COLUMNS


class TestAdapter(TestCase):

    def setUp(self):
        self.temp_path = mkdtemp()
        self.fixtures_path = os.path.join('rosie', 'chamber_of_deputies', 'tests', 'fixtures')
        copies = (
            ('companies.xz', subject_class.COMPANIES_DATASET),
            ('reimbursements.xz', 'reimbursements.xz')
        )
        for source, target in copies:
            copy2(os.path.join(self.fixtures_path, source), os.path.join(self.temp_path, target))
        self.subject = subject_class(self.temp_path)

    def tearDown(self):
        shutil.rmtree(self.temp_path)

    @patch('rosie.chamber_of_deputies.adapter.CEAPDataset')
    @patch('rosie.chamber_of_deputies.adapter.fetch')
    def test_get_performs_a_left_merge_between_reimbursements_and_companies(self, fetch, ceap):
        self.assertEqual(5, len(self.subject.dataset))
        self.assertEqual(1, self.subject.dataset['legal_entity'].isnull().sum())

    @patch('rosie.chamber_of_deputies.adapter.CEAPDataset')
    @patch('rosie.chamber_of_deputies.adapter.fetch')
    def test_prepare_dataset(self, fetch, ceap):
        """
        * Rename columns.
        * Make `document_type` a category column.
        * Rename values for subquota_description.
        """
        dataset = self.subject.dataset
        self.assertTrue(set(ADAPTER_COLUMNS.keys()).issubset(set(dataset.columns)))
        document_types = ['bill_of_sale', 'simple_receipt', 'expense_made_abroad']
        self.assertEqual(document_types,
                         dataset['document_type'].cat.categories.tolist())
        fixture = pd.read_csv(os.path.join(self.fixtures_path, 'reimbursements.xz'))
        meal_rows = fixture \
            .query('subquota_description == "Congressperson meal"')['subquota_description'].index
        self.assertEqual(['Meal'],
                         dataset.loc[meal_rows, 'subquota_description'].unique().tolist())
