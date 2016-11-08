from unittest.mock import patch

from django.test import TestCase
from jarbas.core.models import Document, Receipt
from jarbas.core.tests import sample_document_data


class TestCreate(TestCase):

    def setUp(self):
        self.document = Document.objects.create(**sample_document_data)
        self.receipt_data = {
            'url': 'http://jarbas.dsbr',
            'fetched': True,
            'document': self.document
        }
        base_url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/'
        self.expected_url = base_url + '13/1970/42.pdf'

    def test_create(self):
        self.assertEqual(0, Receipt.objects.count())
        Receipt.objects.create(**self.receipt_data)
        self.assertEqual(1, Receipt.objects.count())

    def test_relationship(self):
        Receipt.objects.create(**self.receipt_data)
        self.assertEqual('http://jarbas.dsbr', self.document.receipt.url)

    def test_get_url(self):
        receipt = Receipt.objects.create(**self.receipt_data)
        self.assertEqual(self.expected_url, receipt.get_url())

    @patch('jarbas.core.models.head')
    def test_fetch_url_for_fetched_url(self, mock_head):
        receipt = Receipt.objects.create(**self.receipt_data)
        self.assertEqual(receipt.url, receipt.fetch_url())
        mock_head.assert_not_called()

    @patch('jarbas.core.models.head')
    def test_fetch_url_for_non_fetched_url_and_existing_url(self, mock_head):
        mock_head.return_value.status_code = 200
        receipt = Receipt.objects.create(
            url=None,
            fetched=False,
            document=self.document
        )
        self.assertEqual(False, receipt.fetched)
        self.assertEqual(self.expected_url, receipt.get_url())
        self.assertEqual(self.expected_url, receipt.fetch_url())
        self.assertEqual(True, receipt.fetched)
        mock_head.assert_called_once_with(self.expected_url)

    @patch('jarbas.core.models.head')
    def test_fetch_url_for_non_fetched_url_nor_existing_url(self, mock_head):
        mock_head.return_value.status_code = 404
        receipt = Receipt.objects.create(
            url=None,
            fetched=False,
            document=self.document
        )
        self.assertEqual(False, receipt.fetched)
        self.assertEqual(self.expected_url, receipt.get_url())
        self.assertEqual(None, receipt.fetch_url())
        self.assertEqual(True, receipt.fetched)
        mock_head.assert_called_once_with(self.expected_url)
