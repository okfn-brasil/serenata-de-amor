from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd
from numpy.testing import assert_array_equal

from rosie.chamber_of_deputies.classifiers.meal_price_outlier_classifier import MealPriceOutlierClassifier


class TestMealPriceOutlierClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('rosie/chamber_of_deputies/tests/fixtures/meal_price_outlier_classifier.csv',
                                   dtype={'recipient_id': np.str})
        self.subject = MealPriceOutlierClassifier()
        self.subject.fit(self.dataset)

    @patch('rosie.chamber_of_deputies.classifiers.meal_price_outlier_classifier.KMeans')
    def test_predict_returns_a_prediction_for_each_observation(self, kmeans_mock):
        kmeans_mock.return_value.predict.return_value = np.ones(3)
        self.subject.fit(self.dataset)
        self.assertTrue(kmeans_mock.return_value.fit.called)

    def test_predict_outlier_for_common_cnpjs_when_value_is_greater_than_mean_plus_3_stds(self):
        row = pd.Series({'applicant_id': 444,
                         'category': 'Meal',
                         'recipient_id': '67661714000111',
                         'recipient': 'B Restaurant',
                         'net_value': 178})
        X = pd.DataFrame().append(row, ignore_index=True)
        prediction = self.subject.predict(X)
        self.assertEqual(-1, prediction[0])

    def test_predict_inlier_for_common_cnpjs_when_value_is_less_than_mean_plus_3_stds(self):
        row = pd.Series({'applicant_id': 444,
                         'category': 'Meal',
                         'recipient_id': '67661714000111',
                         'recipient': 'B Restaurant',
                         'net_value': 177})
        X = pd.DataFrame().append(row, ignore_index=True)
        prediction = self.subject.predict(X)
        self.assertEqual(1, prediction[0])

    def test_predict_outlier_for_non_common_cnpjs_when_value_is_greater_than_mean_plus_4_stds(self):
        row = pd.Series({'applicant_id': 444,
                         'category': 'Meal',
                         'recipient_id': '22412242000125',
                         'recipient': 'D Restaurant',
                         'net_value': 178})
        X = pd.DataFrame().append(row, ignore_index=True)
        prediction = self.subject.predict(X)
        self.assertEqual(-1, prediction[0])

    def test_predict_inlier_for_non_common_cnpjs_when_value_is_less_than_mean_plus_4_stds(self):
        row = pd.Series({'applicant_id': 444,
                         'category': 'Meal',
                         'recipient_id': '22412242000125',
                         'recipient': 'D Restaurant',
                         'net_value': 177})
        X = pd.DataFrame().append(row, ignore_index=True)
        prediction = self.subject.predict(X)
        self.assertEqual(1, prediction[0])

    def test_predict_inlier_for_non_meal_reimbursement_with_large_value(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[72])

    def test_predict_inlier_for_meal_reimbursement_with_small_value(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[73])

    def test_predict_inlier_for_reimbursement_with_small_value(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[7])

    def test_predict_inlier_for_meals_with_large_values_in_hotels(self):
        prediction = self.subject.predict(self.dataset)
        assert_array_equal(np.ones(3), prediction[4:7])

    def test_predict_inlier_for_meals_with_small_values_in_hotels(self):
        prediction = self.subject.predict(self.dataset)
        assert_array_equal(np.ones(3), prediction[1:4])

    def test_predict_inlier_for_meals_with_cpfs(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[0])

    def test_predict_inlier_non_meal_expenses_in_companies_also_selling_food(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[79])
