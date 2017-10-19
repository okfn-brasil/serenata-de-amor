from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.chamber_of_deputies.classifiers import ElectionExpensesClassifier


class TestElectionExpensesClassifier(TestCase):

    def setUp(self):
        self.dataframe = pd.read_csv('rosie/chamber_of_deputies/tests/fixtures/election_expenses_classifier.csv',
                                   dtype={'name': np.str, 'legal_entity': np.str})
        self.election_expenser_classifier = ElectionExpensesClassifier()

    def test_is_election_company(self):
        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[0], True)

    def test_is_not_election_company(self):
        prediction_result = self.election_expenser_classifier.predict(self.dataframe)

        self.assertEqual(prediction_result[1], False)

    def test_fit(self):
        self.assertEqual(self.election_expenser_classifier.fit(self.dataframe), self.election_expenser_classifier)

    def test_tranform(self):
        self.assertEqual(self.election_expenser_classifier.transform(), self.election_expenser_classifier)
