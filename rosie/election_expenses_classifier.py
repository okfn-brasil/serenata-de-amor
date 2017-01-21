import unicodedata

import numpy as np
from sklearn.base import TransformerMixin


class ElectionExpensesClassifier(TransformerMixin):

#     def fit(self, X):
#         return self
#
#     def transform(self, X=None):
#         return self
#
    def predict(self, X):
        self.X = X
        self._X = self.X.copy()
        return self.__applicable_rows(self._X)

    def __applicable_rows(self, X):
        return (self.X['legal_entity'] == '409-0 - CANDIDATO A CARGO POLITICO ELETIVO') | \
                (self.X['name'].astype(np.str).str.lower().str.contains(r'(eleic)[(ao)(oes)]'))

#
#     def __normalize_string(self, string):
#         nfkd_form = unicodedata.normalize('NFKD', string.lower())
#         return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
