import math

import numpy as np
from sklearn.base import TransformerMixin

from pycpfcnpj import cpfcnpj


class InvalidCnpjCpfClassifier(TransformerMixin):
    """
    Invalid CNPJ/CPF classifier.

    Validate a `recipient_id` field by calculating its expected check digit
    and verifying the authenticity of the provided ones.

    Dataset
    -------
    document_type : category column
        Validate rows with values 'bill_of_sale' or 'simple_receipt' or 'unknown'.
        'unknown' value is used on Federal Senate data.

    recipient_id : string column
        A CNPJ (Brazilian company ID) or CPF (Brazilian personal tax ID).
    """

    def fit(self, X):
        return self

    def transform(self, X=None):
        return self

    def predict(self, X):
        return np.r_[X.apply(self.__is_invalid, axis=1)]

    def __is_invalid(self, row):
        document_types = ['bill_of_sale', 'simple_receipt', 'unknown']
        return (row['document_type'] in document_types) \
            & (not cpfcnpj.validate(str(row['recipient_id'])))
