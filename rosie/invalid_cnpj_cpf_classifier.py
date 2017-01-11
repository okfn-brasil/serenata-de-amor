import math

import numpy as np
from pycpfcnpj import cpfcnpj
from sklearn.base import TransformerMixin


class InvalidCnpjCpfClassifier(TransformerMixin):

    def fit(self, X):
        return self

    def transform(self, X=None):
        pass

    def predict(self, X):
        self._X = X.copy()
        self._X['cnpj_cpf'] = self._X['cnpj_cpf'].astype(np.str)
        return np.r_[self._X.apply(self.__is_invalid, axis=1)]

    def __is_invalid(self, row):
        return not ((row['document_type'] == 2) | cpfcnpj.validate(row['cnpj_cpf']))
