import json
from unittest.mock import patch

from django.shortcuts import resolve_url as r
from django.test import TestCase

from jarbas.core.models import Document, Receipt
from jarbas.core.tests import sample_document_data


class TestGetReceipt(TestCase):

    def setUp(self):
        document = Document.objects.create(**sample_document_data)
        Receipt.objects.create(document=document)
        self.url = r('api:receipt-detail', pk=document.pk)

    @patch('jarbas.core.models.Receipt.fetch_url')
    def test_existing_receipt(self, mock_fetch_url):
        expected = Receipt.objects.first().get_url()
        mock_fetch_url.return_value = expected
        resp = self.client.get(self.url)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content['url'])

    @patch('jarbas.core.models.Receipt.fetch_url')
    def test_non_existing_receipt(self, mock_fetch_url):
        mock_fetch_url.return_value = None
        resp = self.client.get(self.url)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(None, content['url'])

    def test_non_existing_document(self):
        url = r('api:receipt-detail', pk=42)
        resp = self.client.get(url)
        self.assertEqual(404, resp.status_code)
