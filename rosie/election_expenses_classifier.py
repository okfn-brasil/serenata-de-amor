import unicodedata

import numpy as np
from sklearn.base import TransformerMixin


class ElectionExpensesClassifier(TransformerMixin):

    def fit(self, X):
        return self

    def transform(self, X=None):
        return self

    def predict(self, X):
        return X['legal_entity'] == '409-0 - CANDIDATO A CARGO POLITICO ELETIVO'
