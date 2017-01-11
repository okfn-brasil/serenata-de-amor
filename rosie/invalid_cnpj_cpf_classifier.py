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
        return np.r_[self._X.apply(self.__is_valid, axis=1)]

    def __is_valid(self, row):
        return (row['document_type'] == 2) | cpfcnpj.validate(row['cnpj_cpf'])
