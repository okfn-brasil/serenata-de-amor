import shutil
import os
from tempfile import mkdtemp
from unittest import TestCase

import pandas as pd

from rosie.federal_senate.adapter import Adapter as subject_class
from rosie.federal_senate.adapter import COLUMNS as ADAPTER_COLUMNS

FIXTURE_PATH = os.path.join('rosie',
                            'federal_senate',
                            'tests',
                            'fixtures',
                            'federal_senate_reimbursements.xz')


class TestAdapter(TestCase):

    def setUp(self):
        self.temp_path = mkdtemp()
        subject = subject_class(self.temp_path)
        subject.dataset_path = FIXTURE_PATH
        self.dataset = subject.dataset

    def tearDown(self):
        shutil.rmtree(self.temp_path)

    def test_renamed_columns(self):
        adapter_keys = ADAPTER_COLUMNS.keys()
        dataset_keys = self.dataset.columns
        self.assertTrue(set(adapter_keys).issubset(set(dataset_keys)))

    def test_created_document_type_column_successfully(self):
        self.assertIn('document_type', self.dataset.columns)

    def test_document_type_value_is_simple_receipt(self):
        self.assertEqual(self.dataset['document_type'].all(), 'simple_receipt')

    def test_dataset_is_a_pandas_DataFrame(self):
        self.assertIsInstance(self.dataset, pd.core.frame.DataFrame)

    def test_droped_all_null_values(self):
        self.assertTrue(self.dataset['recipient_id'].all())
