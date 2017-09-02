import datetime
from unittest import TestCase

import pandas as pd

from rosie.chamber_of_deputies.classifiers.irregular_companies_classifier import IrregularCompaniesClassifier


class TestIrregularCompaniesClassifier(TestCase):

    def setUp(self):
        self.subject = IrregularCompaniesClassifier()

    def _get_company_dataset(self, fields):
        base_company = {
            'recipient_id': '02989654001197',
            'situation_date': datetime.date(2013, 1, 3),
            'issue_date': datetime.date(2013, 1, 30),
            'situation': '',
        }
        for key, value in fields.items():
            base_company[key] = value
        dataset = pd.DataFrame([base_company, ])
        return dataset

    def test_is_regular_company(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'ABERTA'
            }))[0], False)

    def test_is_irregular_company_BAIXADA(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'BAIXADA'
            }))[0], True)

    def test_is_irregular_company_NULA(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'NULA'
            }))[0], True)

    def test_is_irregular_company_INAPTA(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'INAPTA'
            }))[0], True)

    def test_is_irregular_company_SUSPENSA(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'SUSPENSA'
            }))[0], True)

    def test_is_valid_if_suspended_after_expense(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'SUSPENSA',
                'situation_date': datetime.date(2013, 1, 30),
                'issue_date': datetime.date(2013, 1, 1),
            }))[0], False)

    def test_is_irregular_if_suspended_before_expense(self):
        self.assertEqual(
            self.subject.predict(self._get_company_dataset({
                'situation': 'SUSPENSA',
                'situation_date': datetime.date(2013, 1, 1),
                'issue_date': datetime.date(2013, 1, 30),
            }))[0], True)
