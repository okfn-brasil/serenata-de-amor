from django.test import TestCase

from jarbas.chamber_of_deputies.serializers import clean_cnpj_cpf


class TestCleanCnpjCpf(TestCase):
    def test_should_return_cnpj_cpf_without_mask(self):
        self.assertEqual('12345678901234', clean_cnpj_cpf('12.345.678/9012-34'))
        self.assertEqual('12345678901234', clean_cnpj_cpf('12345678901234'))
        self.assertEqual('02002002002', clean_cnpj_cpf('020.020.020-02'))
        self.assertEqual('02002002002', clean_cnpj_cpf('02002002002'))
