from django.test import TestCase
from jarbas.core.models import Document
from jarbas.core.tests import sample_document_data


class TestCreate(TestCase):

    def setUp(self):
        self.data = sample_document_data

    def test_create(self):
        self.assertEqual(0, Document.objects.count())
        Document.objects.create(**self.data)
        self.assertEqual(1, Document.objects.count())

    def test_create_without_date(self):
        self.assertEqual(0, Document.objects.count())
        new_data = self.data.copy()
        new_data['issue_date'] = None
        Document.objects.create(**new_data)
        self.assertEqual(1, Document.objects.count())

    def test_get_receipt_url(self):
        document = Document(**self.data)
        expected = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/13/1970/42.pdf'
        self.assertEqual(expected, document.get_receipt_url())
