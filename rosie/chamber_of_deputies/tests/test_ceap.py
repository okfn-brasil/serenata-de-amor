import os.path
from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd

from rosie.chamber_of_deputies.classifiers import ChamberOfDeputies


class TestChamberOfDeputies(TestCase):

    def setUp(self):
        row = pd.Series({'applicant_id': 444,
                         'document_id': 999,
                         'subquota_description': 'Congressperson meal',
                         'cnpj_cpf': '67661714000111',
                         'supplier': 'B Restaurant',
                         'total_net_value': 178,
                         'year': 2016})
        self.dataset = pd.DataFrame().append(row, ignore_index=True)
        self.subject = ChamberOfDeputies(self.dataset, mkdtemp())

    @patch('rosie.chamber_of_deputies.classifiers.joblib')
    def test_load_trained_model_trains_model_when_not_persisted(self, _):
        model = self.subject.load_trained_model(MagicMock)
        model.fit.assert_called_once_with(self.dataset)

    @patch('rosie.chamber_of_deputies.classifiers.joblib')
    def test_load_trained_model_doesnt_train_model_when_already_persisted(self, _):
        Path(os.path.join(self.subject.data_path, 'magicmock.pkl')).touch()
        model = self.subject.load_trained_model(MagicMock)
        model.fit.assert_not_called()
