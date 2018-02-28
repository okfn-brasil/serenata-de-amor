import os
import shutil
from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd

from rosie.chamber_of_deputies import settings
from rosie.chamber_of_deputies.adapter import Adapter
from rosie.core import Core


class TestChamberOfDeputies(TestCase):

    def setUp(self):
        row = pd.Series({'applicant_id': 444,
                         'document_id': 999,
                         'year': 2016})
        self.dataset = pd.DataFrame().append(row, ignore_index=True)
        self.temp_dir = mkdtemp()
        self.classifier = MagicMock()
        self.classifier.__name__ = 'MockedClassifier'

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch.object(Adapter, 'dataset', new_callable=PropertyMock)
    @patch('rosie.core.joblib')
    def test_load_trained_model_trains_model_when_not_persisted(self, _, dataset):
        dataset.return_value = self.dataset
        adapter = Adapter(self.temp_dir)
        subject = Core(settings, adapter)
        subject.load_trained_model(self.classifier)
        self.classifier.return_value.fit.assert_called_once_with(self.dataset)

    @patch.object(Adapter, 'dataset', new_callable=PropertyMock)
    @patch('rosie.core.joblib')
    def test_load_trained_model_doesnt_train_model_when_already_persisted(self, _, dataset):
        dataset.return_value = self.dataset
        adapter = Adapter(self.temp_dir)
        subject = Core(settings, adapter)
        Path(os.path.join(subject.data_path, 'mockedclassifier.pkl')).touch()
        model = subject.load_trained_model(self.classifier)
        model.fit.assert_not_called()
