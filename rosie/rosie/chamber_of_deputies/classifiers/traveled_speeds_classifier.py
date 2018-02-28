from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin
from sklearn.utils.validation import check_is_fitted

from geopy.distance import vincenty as distance


class TraveledSpeedsClassifier(TransformerMixin):
    """
    Traveled Speeds classifier.

    Dataset
    -------
    applicant_id : category column
        A personal identifier code for every person making expenses.

    category : category column
        Category of the expense. The model will be applied just in rows where
        the value is equal to "Meal".

    is_party_expense : bool column
        If the row corresponds to a party expense or not. The model will be
        applied just in rows where the value is equal to `False`.

    issue_date : datetime column
        Date when the expense was made.

    latitude : float column
        Latitude of the place where the expense was made.

    longitude : float column
        Longitude of the place where the expense was made.
    """

    AGG_KEYS = ['applicant_id', 'issue_date']
    COLS = ['applicant_id',
            'category',
            'is_party_expense',
            'issue_date',
            'latitude',
            'longitude']

    def __init__(self, contamination=.001):
        if contamination in [0, 1]:
            raise ValueError('contamination must be greater than 0 and less than 1')

        self.contamination = contamination

    def fit(self, X):
        _X = self.__aggregate_dataset(X)
        self.polynomial = np.polyfit(_X['expenses'].astype(np.long),
                                     _X['distance_traveled'].astype(np.long),
                                     3)
        self._polynomial_fn = np.poly1d(self.polynomial)
        return self

    def transform(self, X=None):
        pass

    def predict(self, X):
        check_is_fitted(self, ['polynomial', '_polynomial_fn'])

        _X = X[self.COLS].copy()
        _X = self.__aggregate_dataset(_X)
        _X = self.__classify_dataset(_X)
        _X = pd.merge(X, _X, how='left', left_on=self.AGG_KEYS, right_on=self.AGG_KEYS)
        is_outlier = self.__applicable_rows(_X) & \
            (_X['expenses_threshold_outlier'] | _X['traveled_speed_outlier'])
        y = is_outlier.astype(np.int).replace({1: -1, 0: 1})
        return y

    def __aggregate_dataset(self, X):
        X = X[self.__applicable_rows(X)]
        distances_traveled = X.groupby(self.AGG_KEYS) \
            .apply(self.__calculate_sum_distances).reset_index() \
            .rename(columns={0: 'distance_traveled'})
        expenses = X.groupby(self.AGG_KEYS)['applicant_id'].agg(len) \
            .rename('expenses').reset_index()
        _X = pd.merge(distances_traveled, expenses,
                      left_on=self.AGG_KEYS,
                      right_on=self.AGG_KEYS)
        return _X

    def __classify_dataset(self, X):
        X['expected_distance'] = self._polynomial_fn(X['expenses'])
        X['diff_distance'] = abs(X['expected_distance'] - X['distance_traveled'])
        X['expenses_threshold_outlier'] = X['expenses'] > 8
        threshold = self.__threshold_for_contamination(X, self.contamination)
        X['traveled_speed_outlier'] = X['diff_distance'] > threshold
        return X

    def __applicable_rows(self, X):
        return (X['category'] == 'Meal') & \
            (-73.992222 < X['longitude']) & (X['longitude'] < -34.7916667) & \
            (-33.742222 < X['latitude']) & (X['latitude'] < 5.2722222) & \
            ~X['is_party_expense'] & \
            X[['latitude', 'longitude']].notnull().all(axis=1)

    def __calculate_sum_distances(self, X):
        coordinate_list = X[['latitude', 'longitude']].values
        edges = list(combinations(coordinate_list, 2))
        return np.sum([distance(edge[0][1:], edge[1][1:]).km for edge in edges])

    def __threshold_for_contamination(self, X, expected_contamination):
        possible_thresholds = range(1, int(X['expected_distance'].max()), 50)
        results = [(self.__contamination(X, t), t) for t in possible_thresholds]
        best_choice = min(results, key=lambda x: abs(x[0] - expected_contamination))
        return best_choice[1]

    def __contamination(self, X, threshold):
        return (X['diff_distance'] > threshold).sum() / \
            (len(X) - X['expenses_threshold_outlier'].sum())
