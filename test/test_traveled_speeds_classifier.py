from unittest import TestCase, main
from rosie.traveled_speeds_classifier import TraveledSpeedsClassifier
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
import sklearn


class TestTraveledSpeedsClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('test/reimbursements_and_companies.csv',
                                   index_col='id',
                                   dtype={'cnpj_cpf': np.str})
        self.subject = TraveledSpeedsClassifier()
        self.subject.fit(self.dataset)

    def test_it_works(self):
        self.assertEqual(4, 2 + 2)

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
        self.assertEqual(1, prediction[12])

    def test_predict_considers_non_meal_reibursement_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        prediction = self.subject.predict(self.dataset)
        self.assertEqual(1, prediction[9])

    def test_predict_uses_learned_thresholds_from_fit_dataset(self):
        subject = TraveledSpeedsClassifier(contamination=.6)
        subject.fit(self.dataset)
        assert_array_equal(
            np.repeat(-1, 6), subject.predict(self.dataset[11:17]))

    def test_predict_limits_the_number_of_outliers_with_contamination_param(self):
        subject = TraveledSpeedsClassifier(contamination=.6)
        subject.fit(self.dataset)
        self.assertEqual(15, (subject.predict(self.dataset) == -1).sum())

    def test_predict_validates_range_of_values_for_contamination_param(self):
        with self.assertRaises(ValueError):
            TraveledSpeedsClassifier(contamination=0)
        with self.assertRaises(ValueError):
            TraveledSpeedsClassifier(contamination=1)


if __name__ == '__main__':
    unittest.main()
