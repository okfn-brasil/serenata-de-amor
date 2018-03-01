from collections import namedtuple
from datetime import date
from itertools import chain
from unittest import TestCase

import pandas as pd

from rosie.chamber_of_deputies.classifiers import IrregularCompaniesClassifier


Status = namedtuple('Status', ('situation_date', 'issue_date', 'expected'))


class TestIrregularCompaniesClassifier(TestCase):

    SUSPICIOUS_SITUATIONS = (
        'BAIXADA',
        'NULA',
        'INAPTA',
        'SUSPENSA',
    )

    SITUATIONS = chain(SUSPICIOUS_SITUATIONS, ('ABERTA',))

    STATUS = (
        Status(date(2013, 1, 30), date(2013, 1, 1), False),
        Status(date(2013, 1, 1), date(2013, 1, 30), True)
    )

    def setUp(self):
        self.subject = IrregularCompaniesClassifier()

    def _get_company_dataset(self, **kwargs):
        base_company = {
            'recipient_id': '02989654001197',
            'situation_date': date(2013, 1, 3),
            'issue_date': date(2013, 1, 30),
            'situation': '',
        }
        base_company.update(kwargs)
        dataset = pd.DataFrame([base_company])
        return dataset

    def test_is_regular_company(self):
        for situation in self.SITUATIONS:
            company = self._get_company_dataset(situation=situation)
            expected = situation in self.SUSPICIOUS_SITUATIONS
            result, *_ = self.subject.predict(company)
            with self.subTest():
                self.assertEqual(result, expected, msg=company)

    def test_if_company_is_suspended(self):
        for status in self.STATUS:
            company = self._get_company_dataset(
                situation='SUSPENSA',
                situation_date=status.situation_date,
                issue_date=status.issue_date,
            )
            result, *_ = self.subject.predict(company)
            with self.subTest():
                self.assertEqual(result, status.expected, msg=company)
