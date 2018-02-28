import numpy as np
from sklearn.base import TransformerMixin
from brutils import cpf, cnpj


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
    def fit(self, dataframe):
        return self

    def transform(self, dataframe=None):
        return self

    def predict(self, dataframe):
        def is_invalid(row):
            valid_cpf = cpf.validate(str(row['recipient_id']).zfill(11))
            valid_cnpj = cnpj.validate(str(row['recipient_id']).zfill(14))
            good_doctype = row['document_type'] in ('bill_of_sale', 'simple_receipt', 'unknown')
            return good_doctype and (not (valid_cpf or valid_cnpj))
        return np.r_[dataframe.apply(is_invalid, axis=1)]
