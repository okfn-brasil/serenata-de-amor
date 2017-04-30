import math

import numpy as np
from pycpfcnpj import cpfcnpj
from sklearn.base import TransformerMixin


class InvalidCnpjCpfClassifier(TransformerMixin):

    def fit(self, X):
        return self

    def transform(self, X=None):
        return self

    def predict(self, X):
        return np.r_[X.apply(self.__is_invalid, axis=1)]

    def __is_invalid(self, row):
        return (row['document_type'] in [0, 1]) & (not cpfcnpj.validate(str(row['recipient_id'])))
