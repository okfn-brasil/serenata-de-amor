from sklearn.base import TransformerMixin


ELECTION_LEGAL_ENTITY = '409-0 - CANDIDATO A CARGO POLITICO ELETIVO'

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
        pass

    def transform(self, dataframe=None):
        pass

    def predict(self, dataframe):
        return dataframe['legal_entity'] == ELECTION_LEGAL_ENTITY
