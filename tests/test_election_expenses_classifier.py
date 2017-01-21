from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.election_expenses_classifier import ElectionExpensesClassifier


class TestElectionExpensesClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('tests/fixtures/election_expenses_classifier.csv',
                                   dtype={'name': np.str, 'legal_entity': np.str})
        self.subject = ElectionExpensesClassifier()

    def test_is_election_company(self):
        self.assertEqual(self.subject.predict(self.dataset)[0], True)

    def test_is_not_election_company(self):
        self.assertEqual(self.subject.predict(self.dataset)[1], False)

    def test_is_not_election_company_blabs(self):
        self.assertEqual(self.subject.predict(self.dataset)[1], False)
    # def test_is_valid_cnpj(self):
    #     self.assertEqual(self.subject.predict(self.dataset)[0], False)
