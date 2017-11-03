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
        cpf_or_cnpj = lambda doc: cpf.validate(str(doc).zfill(11)) or cnpj.validate(str(doc).zfill(14))
        good_doctype = lambda doctype: doctype in ('bill_of_sale', 'simple_receipt', 'unknown')
        is_invalid = lambda row: good_doctype(row['document_type']) and (not cpf_or_cnpj(row['recipient_id']))

        return np.r_[dataframe.apply(is_invalid, axis=1)]
