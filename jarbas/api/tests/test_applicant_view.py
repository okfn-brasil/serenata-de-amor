from json import loads

from django.core.cache import cache
from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data


class TestApplicant(TestCase):

    def setUp(self):
        Reimbursement.objects.create(**sample_reimbursement_data)
        self.url = resolve_url('api:applicant-list')

    def test_status_code(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_contents(self):
        expected = [
            dict(congressperson_name='John Doe', applicant_id=42),
            dict(congressperson_name='Roger That', applicant_id=13)
        ]

        cache.clear()
        secondary_data = sample_reimbursement_data.copy()
        secondary_data['applicant_id'] = 42
        secondary_data['congressperson_name'] = 'John Doe'
        Reimbursement.objects.create(**secondary_data)
        resp = self.client.get(self.url)

        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(2, content['count'])
        self.assertEqual(expected, content['results'])

    def test_contents_with_filter(self):
        expected = [
            dict(congressperson_name='John Doe', applicant_id=42)
        ]

        secondary_data = sample_reimbursement_data.copy()
        secondary_data['applicant_id'] = 42
        secondary_data['congressperson_name'] = 'John Doe'
        Reimbursement.objects.create(**secondary_data)
        resp = self.client.get(self.url + '?q=doe')

        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(1, content['count'])
        self.assertEqual(expected, content['results'])

    def test_content_non_duplicate_name(self):
        expected = [
            dict(congressperson_name='Roger That', applicant_id=13)
        ]
        secondary_data = sample_reimbursement_data.copy()
        secondary_data['year'] = 1971
        Reimbursement.objects.create(**secondary_data)
        resp = self.client.get(self.url)

        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(1, content['count'])
        self.assertEqual(expected, content['results'])
