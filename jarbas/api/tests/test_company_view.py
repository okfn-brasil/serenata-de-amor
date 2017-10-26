import re
import json

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Activity, Company
from jarbas.core.tests import sample_activity_data, sample_company_data


class TestApi(TestCase):

    def setUp(self):
        activity = Activity.objects.create(**sample_activity_data)
        self.company = Company.objects.create(**sample_company_data)
        self.company.main_activity.add(activity)
        self.company.save()
        cnpj = re.compile(r'\D').sub('', self.company.cnpj)
        self.url = resolve_url('core:company-detail', cnpj)


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


class TestGetNonExistentCompany(TestApi):

    def setUp(self):
        url = resolve_url('core:company-detail', '42424242424242')
        self.resp = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(404, self.resp.status_code)
