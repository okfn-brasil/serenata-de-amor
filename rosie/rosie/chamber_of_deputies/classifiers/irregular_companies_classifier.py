import numpy as np
from sklearn.base import TransformerMixin


class IrregularCompaniesClassifier(TransformerMixin):
    """
    Irregular Companies classifier.

    Check for the official state of the company in the
    Brazilian Federal Revenue and reports for rows with companies unauthorized
    to sell products or services.

    Dataset
    -------
    issue_date : datetime column
        Date when the expense was made.

    situation : string column
        Situation of the company according to the Brazilian Federal Revenue.

    situation_date : datetime column
        Date when the situation was last updated.
    """

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
