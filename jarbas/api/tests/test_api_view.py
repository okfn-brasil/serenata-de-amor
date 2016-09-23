import json

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Document
from jarbas.core.tests import sample_document_data


class TestApi(TestCase):

    url = resolve_url('api:document-list') + '?document_id=42'

    def setUp(self):
        Document.objects.create(**sample_document_data)


class TestGetDocuments(TestApi):

    def setUp(self):
        super().setUp()
        self.resp = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_content(self):
        content = json.loads(self.resp.content.decode('utf-8'))
        first_row = content['results'][0]
        self.assertEqual(1, content['count'])
        self.assertEqual('Roger That', first_row['congressperson_name'])
        self.assertEqual(4.56, float(first_row['net_value']))


class TestGetNonExistentDocument(TestApi):

    def setUp(self):
        self.resp = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_content(self):
        content = json.loads(self.resp.content.decode('utf-8'))
        self.assertEqual(0, content['count'])
