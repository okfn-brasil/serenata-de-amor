from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.chamber_of_deputies.classifiers import ElectionExpensesClassifier


class TestElectionExpensesClassifier(TestCase):

    def setUp(self):
        self.election_expenser_classifier = ElectionExpensesClassifier()

    def test_legal_entity_is_a_election_company(self):
        self.dataframe = self._create_dataframe([[
            'CARLOS ALBERTO DA SILVA',
            'ELEICAO 2006 CARLOS ALBERTO DA SILVA DEPUTADO',
            '409-0 - CANDIDATO A CARGO POLITICO ELETIVO'
        ]])

        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[0], True)

    def test_legal_entity_is_not_election_company(self):
        self.dataframe = self._create_dataframe([[
            'PAULO ROGERIO ROSSETO DE MELO',
            'POSTO ROTA 116 DERIVADOS DE PETROLEO LTDA',
            '401-4 - EMPRESA INDIVIDUAL IMOBILIARIA'
        ]])

        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[0], False)

    def test_fit_just_for_formality_because_its_never_used(self):
        empty_dataframe = pd.DataFrame()
        self.assertTrue(self.election_expenser_classifier.fit(empty_dataframe) is None)

    def test_transform_just_for_formality_because_its_never_used(self):
        self.assertTrue(self.election_expenser_classifier.transform() is None)

    def _create_dataframe(self, dataframe_data):
        return pd.DataFrame(data=dataframe_data, columns=['congressperson_name', 'name', 'legal_entity'])
