import unicodedata

import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin
from sklearn.cluster import KMeans


class MealPriceOutlierClassifier(TransformerMixin):


    HOTEL_REGEX = r'hote(?:(?:ls?)|is)'
    CLUSTER_KEYS = ['mean', 'std']

    def fit(self, X):
        _X = X[self.__applicable_rows(X)]
        companies = _X.groupby('cnpj_cpf').apply(self.__company_stats) \
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
        _X = X.copy()
        companies = _X[self.__applicable_rows(_X)] \
            .groupby('cnpj_cpf').apply(self.__company_stats) \
            .reset_index()
        companies['cluster'] = \
            self.cluster_model.predict(companies[self.CLUSTER_KEYS])
        companies = pd.merge(companies,
                             self.clusters[['cluster', 'threshold']],
                             how='left')
        _X = pd.merge(_X, companies[['cnpj_cpf', 'threshold']], how='left')
        known_companies = companies[self.__applicable_company_rows(companies)]
        known_thresholds = known_companies \
            .groupby('cnpj_cpf') \
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
            (_X['total_net_value'] > _X['threshold'])
        _X.loc[is_outlier, 'y'] = -1
        return _X['y']

    def __applicable_rows(self, X):
        return (X['subquota_description'] == 'Congressperson meal') & \
            (X['cnpj_cpf'].str.len() == 14) & \
            (~X['supplier'].apply(self.__normalize_string).str.contains(self.HOTEL_REGEX))

    def __applicable_company_rows(self, companies):
        return (companies['congresspeople'] > 3) & (companies['records'] > 20)

    def __company_stats(self, X):
        stats = {'mean': np.mean(X['total_net_value']),
                 'std': np.std(X['total_net_value']),
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
