import numpy as np
from pycpfcnpj import cpfcnpj


class InvalidCnpjCpfClassifier():

    def validate_cnpj_cpf(self, cnpj_or_cpf):
        cnpj_or_cpf = str(cnpj_or_cpf)
        return (cnpj_or_cpf == None) | cpfcnpj.validate(cnpj_or_cpf)

    def fit(self, X):
        self.X = X
        self._X = self.X.copy()
        self.__create_columns()
        return self

    def transform(self, X=None):
        pass

    def __create_columns(self):
        cnpj_cpf_list = self._X['cnpj_cpf'].astype(np.str).replace('nan', None)
        self._X['valid_cnpj_cpf'] = np.vectorize(valid_cnpj_cpf)(cnpj_cpf_list)
