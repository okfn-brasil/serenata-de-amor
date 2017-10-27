from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.chamber_of_deputies.classifiers import ElectionExpensesClassifier


class TestElectionExpensesClassifier(TestCase):

    def setUp(self):
        self.election_expenser_classifier = ElectionExpensesClassifier()

    def test_legal_entity_is_a_election_company(self):
        self.dataframe = pd.read_csv('rosie/chamber_of_deputies/tests/fixtures/election_expenses_classifier.csv',
                                     dtype={'name': np.str, 'legal_entity': np.str})

        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[0], True)

    def test_legal_entity_is_not_election_company(self):
        self.dataframe = pd.read_csv('rosie/chamber_of_deputies/tests/fixtures/election_expenses_classifier.csv',
                                      dtype={'name': np.str, 'legal_entity': np.str})

        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[1], False)

    def test_fit_just_for_formality_because_its_never_used(self):
        empty_dataframe = pd.DataFrame()
        self.assertTrue(self.election_expenser_classifier.fit(empty_dataframe) is None)

    def test_transform_just_for_formality_because_its_never_used(self):
        self.assertTrue(self.election_expenser_classifier.transform() is None)
