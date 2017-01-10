from pycpfcnpj import cpfcnpj


class InvalidCnpjCpfClassifier():

    def validate_cnpj_cpf(self, cnpj_or_cpf):
        cnpj_or_cpf = str(cnpj_or_cpf)
        return (cnpj_or_cpf == None) | cpfcnpj.validate(cnpj_or_cpf)
