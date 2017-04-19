import os.path
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import patch
from shutil import copy2

from rosie.chamber_of_deputies import settings
from rosie.chamber_of_deputies.adapter import Adapter


class TestDataset(TestCase):

    def setUp(self):
        temp_path = mkdtemp()
        copy2('rosie/chamber_of_deputies/tests/fixtures/companies.xz',
              os.path.join(temp_path, settings.COMPANIES_DATASET))
        copy2('rosie/chamber_of_deputies/tests/fixtures/reimbursements.xz', temp_path)
        self.subject = Adapter(temp_path)

    @patch('rosie.chamber_of_deputies.adapter.CEAPDataset')
    @patch('rosie.chamber_of_deputies.adapter.fetch')
    def test_get_performs_a_left_merge_between_reimbursements_and_companies(self, _ceap_dataset, _fetch):
        dataset = self.subject.dataset()
        self.assertEqual(5, len(dataset))
        self.assertEqual(1, dataset['legal_entity'].isnull().sum())
