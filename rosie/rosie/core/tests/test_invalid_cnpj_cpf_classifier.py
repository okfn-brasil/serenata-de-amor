from unittest import TestCase

import numpy as np
import pandas as pd

from rosie.core.classifiers import InvalidCnpjCpfClassifier


class TestInvalidCnpjCpfClassifier(TestCase):

    def setUp(self):
        self.dataset = pd.read_csv('rosie/core/tests/fixtures/invalid_cnpj_cpf_classifier.csv',
                                   dtype={'recipient_id': np.str})
        self.subject = InvalidCnpjCpfClassifier()

    def test_is_valid_cnpj(self):
        self.assertEqual(self.subject.predict(self.dataset)[0], False)

    def test_is_invalid_cnpj(self):
        self.assertEqual(self.subject.predict(self.dataset)[1], True)

    def test_is_none(self):
        self.assertEqual(self.subject.predict(self.dataset)[2], True)

    def test_none_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[3], False)

    def test_valid_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[4], False)

    def test_invalid_cnpj_cpf_abroad_is_valid(self):
        self.assertEqual(self.subject.predict(self.dataset)[5], False)

    def test_is_valid_cpf(self):
        self.assertEqual(self.subject.predict(self.dataset)[6], False)

    def test_is_invalid_cpf(self):
        self.assertEqual(self.subject.predict(self.dataset)[7], True)

    def test_invalid_document_type(self):
        self.assertEqual(self.subject.predict(self.dataset)[8], False)

    def test_fit(self):
        self.assertEqual(self.subject.fit(self.dataset), self.subject)

    def test_transform(self):
        self.assertEqual(self.subject.transform(), self.subject)
