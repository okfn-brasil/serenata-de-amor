import shutil
import os
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import patch
from shutil import copy2

from rosie.chamber_of_deputies.adapter import Adapter


class TestDataset(TestCase):

    def setUp(self):
        self.temp_path = mkdtemp()
        fixtures = os.path.join('rosie', 'chamber_of_deputies', 'tests', 'fixtures')
        copies = (
            ('companies.xz', Adapter.COMPANIES_DATASET),
            ('reimbursements.xz', 'reimbursements.xz')
        )
        for source, target in copies:
            copy2(os.path.join(fixtures, source), os.path.join(self.temp_path, target))
        self.subject = Adapter(self.temp_path)

    def tearDown(self):
        shutil.rmtree(self.temp_path)

    @patch('rosie.chamber_of_deputies.adapter.CEAPDataset')
    @patch('rosie.chamber_of_deputies.adapter.fetch')
    def test_get_performs_a_left_merge_between_reimbursements_and_companies(self, fetch, ceap):
        self.assertEqual(5, len(self.subject.dataset))
        self.assertEqual(1, self.subject.dataset['legal_entity'].isnull().sum())
