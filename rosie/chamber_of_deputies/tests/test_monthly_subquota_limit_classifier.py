from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.chamber_of_deputies.classifiers.monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier


class TestMonthlySubquotaLimitClassifier(TestCase):

    MONTHLY_SUBQUOTA_LIMIT_FIXTURE = 'rosie/chamber_of_deputies/tests/fixtures/monthly_subquota_limit_classifier.csv'

    def setUp(self):
        self.full_dataset = pd.read_csv(self.MONTHLY_SUBQUOTA_LIMIT_FIXTURE, dtype={'subquota_number': np.str})
        self.dataset = self.full_dataset[['applicant_id', 'subquota_number', 'issue_date', 'year', 'month', 'net_value']]
        self.result_dataset = self.full_dataset[['expected_prediction', 'test_case_description']]

        self.subject = MonthlySubquotaLimitClassifier()
        self.subject.fit_transform(self.dataset)
        self.prediction = self.subject.predict(self.dataset)

    def test_predictions(self):
        for index, row in self.result_dataset.iterrows():
            self.assertEqual(
                self.prediction[index],
                row['expected_prediction'],
                msg=row['test_case_description'])
