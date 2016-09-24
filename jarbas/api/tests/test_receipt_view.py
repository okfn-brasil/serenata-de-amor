import json
from unittest.mock import patch

from django.shortcuts import resolve_url as r
from django.test import TestCase

from jarbas.core.models import Document
from jarbas.core.tests import sample_document_data


class TestGetReceipt(TestCase):

    def setUp(self):
        Document.objects.create(**sample_document_data)
        self.receipt_url = Document.objects.first().fetch_receipt()
        self.url = r('api:receipt-detail', pk=Document.objects.first().pk)

    @patch('jarbas.core.models.Document.fetch_receipt')
    def test_existing_receipt(self, mock_fetch_receipt):
        mock_fetch_receipt.return_value = self.receipt_url
        resp = self.client.get(self.url)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(self.receipt_url, content['url'])

    @patch('jarbas.core.models.Document.fetch_receipt')
    def test_non_existing_receipt(self, mock_fetch_receipt):
        mock_fetch_receipt.return_value = None
        resp = self.client.get(self.url)
        content = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(None, content['url'])

    def test_non_existing_document(self):
        url = r('api:receipt-detail', pk=42)
        resp = self.client.get(url)
        self.assertEqual(404, resp.status_code)
