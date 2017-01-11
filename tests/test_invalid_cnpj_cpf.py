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
        self.assertEqual(self.subject.predict(self.dataset)[0], True)

    def test_is_invalid_cnpj(self):
        self.assertEqual(self.subject.predict(self.dataset)[1], False)

    def test_is_none(self):
        self.assertEqual(self.subject.predict(self.dataset)[2], False)

    def test_none_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[3], True)

    def test_valid_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[4], True)

    def test_invalid_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[5], True)

    def test_is_valid_cpf(self):
        self.assertEqual(self.subject.predict(self.dataset)[6], True)

    def test_is_invalid_cpf(self):
        self.assertEqual(self.subject.predict(self.dataset)[7], False)
