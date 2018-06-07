import shutil
from datetime import date
from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import call, patch

import pandas as pd
from freezegun import freeze_time

from rosie.chamber_of_deputies.adapter import Adapter


FIXTURES = Path() / 'rosie' / 'chamber_of_deputies' / 'tests' / 'fixtures'


class TestAdapter(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_path = mkdtemp()
        to_copy = (
            'companies.xz',
            'reimbursements-2009.csv',
            'reimbursements-2010.csv',
            'reimbursements-2011.csv',
            'reimbursements-2012.csv',
            'reimbursements-2016.csv'
        )
        for source in to_copy:
            target = source
            if source == 'companies.xz':
                target = Adapter.COMPANIES_DATASET
            shutil.copy2(FIXTURES / source, Path(cls.temp_path) / target)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_path)

    def setUp(self):
        with patch.object(Adapter, 'update_datasets'):
            adapter = Adapter(self.temp_path)
            adapter.log.disabled = True
            self.dataset = adapter.dataset


    def test_load_all_years(self):
        self.assertEqual(6, len(self.dataset))

    def test_merge(self):
        self.assertEqual(1, self.dataset['legal_entity'].isnull().sum())

    def test_rename_columns(self):
        for column in Adapter.RENAME_COLUMNS.values():
            with self.subTest():
                self.assertIn(column, self.dataset.columns)

    def test_document_type_categories(self):
        categories = ('bill_of_sale', 'simple_receipt', 'expense_made_abroad')
        expected = set(categories)
        types = set(self.dataset['document_type'].cat.categories.tolist())
        self.assertEqual(expected, types)

    def test_meal_category(self):
        meals = self.dataset[self.dataset.category == 'Meal']
        self.assertEqual(1, len(meals))

    def test_is_party_expense_category(self):
        party_expenses = self.dataset[self.dataset.is_party_expense == True]
        self.assertEqual(1, len(party_expenses))

    @freeze_time('2010-11-12')
    @patch('rosie.chamber_of_deputies.adapter.fetch')
    @patch('rosie.chamber_of_deputies.adapter.Reimbursements')
    def test_update(self, reimbursements, fetch):
        adapter = Adapter(self.temp_path)
        adapter.dataset  # triggers update methods

        reimbursements.assert_has_calls((
            call(2009, self.temp_path),
            call()(),
            call(2010, self.temp_path),
            call()()
        ))
        fetch.assert_called_once_with(Adapter.COMPANIES_DATASET, self.temp_path)

    @patch('rosie.chamber_of_deputies.adapter.fetch')
    @patch('rosie.chamber_of_deputies.adapter.Reimbursements')
    def test_coerce_dates(self, reimbursements, fetch):
        adapter = Adapter(self.temp_path)
        df = adapter.dataset
        self.assertIn(date(2011, 9, 6), [ts.date() for ts in df.situation_date])
        self.assertIn(date(2009, 6, 1), [ts.date() for ts in df.issue_date])
