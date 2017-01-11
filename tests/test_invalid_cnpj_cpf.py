from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.invalid_cnpj_cpf_classifier import InvalidCnpjCpfClassifier


class TestInvalidCnpjCpfClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('tests/fixtures/invalid_cnpj_cpf_classifier.csv',
                                   dtype={'cnpj_cpf': np.str})
        self.subject = InvalidCnpjCpfClassifier()

    def test_is_valid_cnpj(self):
        value = self.dataset.iloc[0]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        self.assertEqual(validation, True)

    def test_is_invalid_cnpj(self):
        value = self.dataset.iloc[1]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        self.assertEqual(validation, False)

    def test_is_none(self):
        value = self.dataset.iloc[2]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        self.assertEqual(validation, False)

    def test_is_abroad(self):
        value = self.dataset.iloc[3]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        if not validation:
            document_type = self.dataset.iloc[3]['document_type']
            self.assertEqual(document_type, 2)

    def test_is_valid_cpf(self):
        value = self.dataset.iloc[4]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        self.assertEqual(validation, True)

    def test_is_invalid_cpf(self):
        value = self.dataset.iloc[1]['cnpj_cpf']
        validation = self.subject.validate_cnpj_cpf(value)
        self.assertEqual(validation, False)
