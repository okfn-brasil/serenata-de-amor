import datetime
from unittest import TestCase

import pandas as pd

from rosie.chamber_of_deputies.classifiers.irregular_companies_classifier import IrregularCompaniesClassifier


class TestIrregularCompaniesClassifier(TestCase):

    SITUATIONS = [('ABERTA', False), ('BAIXADA', True), ('NULA', True), ('INAPTA', True), ('SUSPENSA', True)]

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
        for situation in self.SITUATIONS:
            self.assertEqual(
                self.subject.predict(self._get_company_dataset({
                    'situation': situation[0]
                }))[0], situation[1])

    STATUS = [
        (datetime.date(2013, 1, 30), datetime.date(2013, 1, 1), False),
        (datetime.date(2013, 1, 1), datetime.date(2013, 1, 30), True)
    ]

    def test_if_company_is_suspended(self):
        for status in self.STATUS:
            self.assertEqual(
                self.subject.predict(self._get_company_dataset({
                    'situation': 'SUSPENSA',
                    'situation_date': status[0],
                    'issue_date': status[1],
                }))[0], status[2])

