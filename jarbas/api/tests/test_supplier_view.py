import re
import json

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Activity, Supplier
from jarbas.core.tests import sample_activity_data, sample_supplier_data


class TestApi(TestCase):

    def setUp(self):
        activity = Activity.objects.create(**sample_activity_data)
        self.supplier = Supplier.objects.create(**sample_supplier_data)
        self.supplier.main_activity.add(activity)
        self.supplier.save()
        cnpj = re.compile(r'\D').sub('', self.supplier.cnpj)
        self.url = resolve_url('api:company-detail', cnpj)


class TestGet(TestApi):

    def setUp(self):
        super().setUp()
        self.resp = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_content(self):
        response = json.loads(self.resp.content.decode('utf-8'))
        self.assertEqual(
            '42 - The answer to life, the universe, and everything',
            response['legal_entity']
        )
        self.assertEqual('42', response['main_activity'][0]['code'])
        self.assertIn('latitude', response)
        self.assertIn('longitude', response)


class TestGetNonExistentSupplier(TestApi):

    def setUp(self):
        url = resolve_url('api:company-detail', '42424242424242')
        self.resp = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(404, self.resp.status_code)


class TestOldURLRedirect(TestApi):

    def test_redirect(self):
        old_url = self.url.replace('company', 'supplier')
        resp = self.client.get(old_url, follow=True)
        self.assertRedirects(resp, self.url)
