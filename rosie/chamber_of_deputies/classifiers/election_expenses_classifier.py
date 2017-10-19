from sklearn.base import TransformerMixin


class ElectionExpensesClassifier(TransformerMixin):
    """
    Election Expenses classifier.

    Check a `legal_entity` field for the presency of the political candidacy
    category in the Brazilian Federal Revenue.

    Dataset
    -------
    legal_entity : string column
        Brazilian Federal Revenue category of companies, preceded by its code.
    """

    def fit(self, dataframe):
        return self

    def transform(self, dataframe=None):
        return self

    def predict(self, dataframe):
        return dataframe['legal_entity'] == '409-0 - CANDIDATO A CARGO POLITICO ELETIVO'
