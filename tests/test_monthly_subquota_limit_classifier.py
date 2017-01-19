from unittest import TestCase

import numpy as np
import pandas as pd
from rosie.monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier


class TestMonthlySubquotaLimitClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('tests/fixtures/monthly_subquota_limit_classifier.csv',
                                   dtype={'subquota_number': np.str})
        self.subject = MonthlySubquotaLimitClassifier()
        self.subject.fit_transform(self.dataset)
        self.prediction = self.subject.predict(self.dataset)

    def test_predict_false_when_not_in_date_range(self):
        self.assertEqual(False, self.prediction[0])
        self.assertEqual(False, self.prediction[1])
        self.assertEqual(False, self.prediction[9])
        self.assertEqual(False, self.prediction[10])

    def test_predict_false_when_under_the_limit(self):
        self.assertEqual(False, self.prediction[2])
        self.assertEqual(False, self.prediction[3])

    def test_predict_false_when_exactly_on_the_limit(self):
        self.assertEqual(False, self.prediction[4])
        self.assertEqual(False, self.prediction[5])

    def test_predict_true_when_over_the_limit(self):
        self.assertEqual(False, self.prediction[6])
        self.assertEqual(True, self.prediction[7])
        self.assertEqual(True, self.prediction[8])
