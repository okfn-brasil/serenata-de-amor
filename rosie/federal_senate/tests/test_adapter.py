import shutil
import os
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import patch
from shutil import copy2

import pandas as pd

from rosie.federal_senate.adapter import Adapter as subject_class
from rosie.federal_senate.adapter import COLUMNS as ADAPTER_COLUMNS

class TestAdapter(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_path = mkdtemp()
        cls.fixtures_path = os.path.join('rosie', 'federal_senate', 'tests', 'fixtures')
        copy_name = 'federal_senate_reimbursements.xz'
        cls.temp_fixture_path = os.path.join(cls.temp_path, copy_name)
        copy2(os.path.join(cls.fixtures_path, copy_name), cls.temp_fixture_path)
        cls.subject = subject_class(cls.temp_path)
        cls.dataset = cls.subject.dataset

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_path)

    def test_renamed_columns(self):
        self.assertTrue(set(ADAPTER_COLUMNS.keys()).issubset(set(self.dataset.columns)))

    def test_created_document_type_column_successfully(self):
        self.assertIn('document_type', self.dataset.columns)

    def test_document_type_value_is_simple_receipt(self):
        self.assertEqual(self.dataset['document_type'].all(), 'simple_receipt')

    def test_dataset_is_a_pandas_DataFrame(self):
        self.assertIsInstance(self.dataset, pd.core.frame.DataFrame)
