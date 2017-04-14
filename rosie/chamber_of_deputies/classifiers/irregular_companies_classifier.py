import unicodedata

import numpy as np
from sklearn.base import TransformerMixin


class IrregularCompaniesClassifier(TransformerMixin):

    def fit(self, X):
        return self

    def transform(self, X=None):
        return self

    def predict(self, X):
        statuses = ['BAIXADA', 'NULA', 'SUSPENSA', 'INAPTA']
        self._X = X.apply(self.__compare_date, axis=1)
        return np.r_[self._X & X['situation'].isin(statuses)]

    def __compare_date(self, row):
        return (row['situation_date'] < row['issue_date'])
