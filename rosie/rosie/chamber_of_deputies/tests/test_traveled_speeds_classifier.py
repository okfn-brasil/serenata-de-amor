from unittest import TestCase

import numpy as np
import pandas as pd
import sklearn
from numpy.testing import assert_array_equal

from rosie.chamber_of_deputies.classifiers.traveled_speeds_classifier import TraveledSpeedsClassifier


class TestTraveledSpeedsClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('rosie/chamber_of_deputies/tests/fixtures/traveled_speeds_classifier.csv',
                                   dtype={'recipient_id': np.str})
        self.subject = TraveledSpeedsClassifier()
        self.subject.fit(self.dataset)

    def test_fit_learns_a_polynomial_for_regression(self):
        self.assertIsInstance(self.subject.polynomial, np.ndarray)

    def test_predict_doesnt_work_before_fitting_the_model(self):
        subject = TraveledSpeedsClassifier()
        with self.assertRaises(sklearn.exceptions.NotFittedError):
            subject.predict(self.dataset)

    def test_predict_returns_a_prediction_for_each_observation(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(len(prediction), len(self.dataset))

    def test_predict_considers_meal_reimbursements_in_days_with_more_than_8_outliers(self):
        prediction = self.subject.predict(self.dataset)
        assert_array_equal(np.repeat(-1, 9), prediction[:9])

    def test_predict_considers_non_meal_reibursement_an_inlier(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[14])

    def test_predict_considers_non_meal_reibursement_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[9])

    def test_predict_considers_meal_reibursement_without_congressperson_id_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[10])

    def test_predict_considers_meal_reibursement_without_latitude_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[11])

    def test_predict_considers_meal_reibursement_without_longitude_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[12])

    def test_predict_uses_learned_thresholds_from_fit_dataset(self):
        subject = TraveledSpeedsClassifier(contamination=.6)
        subject.fit(self.dataset)
        assert_array_equal(
            np.repeat(-1, 6), subject.predict(self.dataset[13:19]))

    def test_predict_limits_the_number_of_outliers_with_contamination_param(self):
        subject = TraveledSpeedsClassifier(contamination=.5)
        subject.fit(self.dataset)
        returned_contamination = \
            (subject.predict(self.dataset) == -1).sum() / len(self.dataset)
        self.assertLess(returned_contamination, .5)

    def test_predict_contamination_may_go_higher_than_expected_given_expenses_threshold(self):
        subject = TraveledSpeedsClassifier(contamination=.2)
        subject.fit(self.dataset)
        returned_contamination = \
            (subject.predict(self.dataset) == -1).sum() / len(self.dataset)
        self.assertGreater(returned_contamination, .2)

    def test_predict_validates_range_of_values_for_contamination_param(self):
        with self.assertRaises(ValueError):
            TraveledSpeedsClassifier(contamination=0)
        with self.assertRaises(ValueError):
            TraveledSpeedsClassifier(contamination=1)

    def test_is_company_coordinates_in_brazil(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[28])
