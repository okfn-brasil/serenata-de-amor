import unicodedata

import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin
from sklearn.cluster import KMeans


class MealPriceOutlierClassifier(TransformerMixin):
    """
    Meal Price Outlier classifier.

    Dataset
    -------
    applicant_id : string column
        A personal identifier code for every person making expenses.

    category : category column
        Category of the expense. The model will be applied just in rows where
        the value is equal to "Meal".

    net_value : float column
        The value of the expense.

    recipient_id : string column
        A CNPJ (Brazilian company ID) or CPF (Brazilian personal tax ID).
    """

    HOTEL_REGEX = r'hote(?:(?:ls?)|is)'
    CLUSTER_KEYS = ['mean', 'std']
    COLS = ['applicant_id',
            'category',
            'net_value',
            'recipient',
            'recipient_id']

    def fit(self, X):
        _X = X[self.__applicable_rows(X)]
        companies = _X.groupby('recipient_id').apply(self.__company_stats) \
            .reset_index()
        companies = companies[self.__applicable_company_rows(companies)]

        self.cluster_model = KMeans(n_clusters=3)
        self.cluster_model.fit(companies[self.CLUSTER_KEYS])
        companies['cluster'] = self.cluster_model.predict(companies[self.CLUSTER_KEYS])
        self.clusters = companies.groupby('cluster') \
            .apply(self.__cluster_stats) \
            .reset_index()
        self.clusters['threshold'] = \
            self.clusters['mean'] + 4 * self.clusters['std']
        return self

    def transform(self, X=None):
        pass

    def predict(self, X):
        _X = X[self.COLS].copy()
        companies = _X[self.__applicable_rows(_X)] \
            .groupby('recipient_id').apply(self.__company_stats) \
            .reset_index()
        companies['cluster'] = \
            self.cluster_model.predict(companies[self.CLUSTER_KEYS])
        companies = pd.merge(companies,
                             self.clusters[['cluster', 'threshold']],
                             how='left')
        _X = pd.merge(_X, companies[['recipient_id', 'threshold']], how='left')
        known_companies = companies[self.__applicable_company_rows(companies)]
        known_thresholds = known_companies \
            .groupby('recipient_id') \
            .apply(lambda x: x['mean'] + 3 * x['std']) \
            .reset_index() \
            .rename(columns={0: 'cnpj_threshold'})
        _X = pd.merge(_X, known_thresholds, how='left')
        if 'cnpj_threshold' in _X.columns:
            _X.loc[_X['cnpj_threshold'].notnull(),
                   'threshold'] = _X['cnpj_threshold']
        _X['y'] = 1
        is_outlier = self.__applicable_rows(_X) & \
            _X['threshold'].notnull() & \
            (_X['net_value'] > _X['threshold'])
        _X.loc[is_outlier, 'y'] = -1
        return _X['y']

    def __applicable_rows(self, X):
        return (X['category'] == 'Meal') & \
            (X['recipient_id'].str.len() == 14) & \
            (~X['recipient'].fillna('').apply(self.__normalize_string).str.contains(self.HOTEL_REGEX))

    def __applicable_company_rows(self, companies):
        return (companies['congresspeople'] > 3) & (companies['records'] > 20)

    def __company_stats(self, X):
        stats = {'mean': np.mean(X['net_value']),
                 'std': np.std(X['net_value']),
                 'congresspeople': len(np.unique(X['applicant_id'])),
                 'records': len(X)}
        return pd.Series(stats)

    def __cluster_stats(self, X):
        stats = {'mean': np.mean(X['mean']),
                 'std': np.mean(X['std'])}
        return pd.Series(stats)

    def __normalize_string(self, string):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
