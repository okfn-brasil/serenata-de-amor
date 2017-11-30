from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.chamber_of_deputies.classifiers.monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier


class TestMonthlySubquotaLimitClassifier(TestCase):
    '''Testing Monthly Subquota Limit Classifier.

    To include new test cases edit `MONTHLY_SUBQUOTA_LIMIT_FIXTURE_FILE`.
    Each test case must have the following fields (see existing test cases as examples):

    applicant_id:
        A personal identifier code for every person making expenses.
        Use the same number to group a test case that requires more than one
        expense request.

    subquota_number:
        A number to classify a category of expenses.

        Allowed values:
          3 -- Fuels and lubricants
          8 -- Security service provided by specialized company
        120 -- Automotive vehicle renting or charter
        122 -- Taxi, toll and parking
        137 -- Participation in course, talk or similar event

    issue_date:
        Date when the expense was made.

    year:
        The quota year matching the expense request.

    month:
        The quota month matching the expense request.

    net_value:
        The value of the expense.

    expected_prediction:
        True or False indicating if this test case must be classified as suspicious or not.

    test_case_description:
        Description of what is being tested in this test case (also showed when test fails)
    '''

    MONTHLY_SUBQUOTA_LIMIT_FIXTURE_FILE = 'rosie/chamber_of_deputies/tests/fixtures/monthly_subquota_limit_classifier.csv'

    def setUp(self):
        self.full_dataset = pd.read_csv(
            self.MONTHLY_SUBQUOTA_LIMIT_FIXTURE_FILE, dtype={'subquota_number': np.str})
        self.dataset = self.full_dataset[
            ['applicant_id', 'subquota_number', 'issue_date', 'year', 'month', 'net_value']]
        self.test_result_dataset = self.full_dataset[['expected_prediction', 'test_case_description']]

        self.subject = MonthlySubquotaLimitClassifier()
        self.subject.fit_transform(self.dataset)
        self.prediction = self.subject.predict(self.dataset)


    def test_predictions(self):
        for index, row in self.test_result_dataset.iterrows():
            self.assertEqual(
                self.prediction[index],
                row['expected_prediction'],
                msg='Line {0}: {1}'.format(row, row['test_case_description']))