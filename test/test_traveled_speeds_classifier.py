from unittest import TestCase, main, skip
from rosie.traveled_speeds_classifier import TraveledSpeedsClassifier

class TestTraveledSpeedsClassifier(TestCase):

    def setUp(self):
        self.subject = TraveledSpeedsClassifier()

    def test_it_works(self):
        self.assertEqual(4, 2 + 2)

    @skip('not implemented')
    def test_predict_returns_a_prediction_for_each_observation(self):
        pass

    @skip('not implemented')
    def test_predict_considers_meal_reimbursements_in_days_with_more_than_8_outliers(self):
        pass

    @skip('not implemented')
    def test_predict_considers_non_meal_reibursement_an_inlier(self):
        pass

    @skip('not implemented')
    def test_predict_considers_non_meal_reibursement_an_inlier_even_when_more_than_8_meal_reimbursements(self):
        pass

    @skip('not implemented')
    def test_predict_limits_the_number_of_outliers_with_contamination_param(self):
        pass

    @skip('not implemented')
    def test_predict_validates_range_of_values_for_contamination_param(self):
        pass




if __name__ == '__main__':
    unittest.main()
