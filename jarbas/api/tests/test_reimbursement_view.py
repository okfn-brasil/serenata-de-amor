from json import loads

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data


class TestListApi(TestCase):

    def setUp(self):

        data = [
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy()
        ]

        data[1]['document_id'] = 42 * 2
        data[2]['applicant_id'] = 13 * 3
        data[2]['document_id'] = 42 * 3
        data[3]['year'] = 1983
        data[3]['applicant_id'] = 13 * 4
        data[3]['document_id'] = 42 * 4

        for d in data:
            Reimbursement.objects.create(**d)

        self.all = resolve_url('api:reimbursement-list')
        self.by_year = resolve_url('api:reimbursement-by-year-list', year=1970)
        self.by_applicant = resolve_url('api:reimbursement-by-applicant-list', year=1970, applicant_id=13)

    def test_status(self):
        urls = (self.all, self.by_year, self.by_applicant)
        for resp in map(lambda url: self.client.get(url), urls):
            with self.subTest():
                self.assertEqual(200, resp.status_code)

    def test_content_general(self):
        self.assertEqual(4, Reimbursement.objects.count())
        self.assertEqual(4, self._count_results(self.all))

    def test_content_by_year(self):
        self.assertEqual(3, self._count_results(self.by_year))

    def test_content_by_applicant_id(self):
        self.assertEqual(2, self._count_results(self.by_applicant))

    def _count_results(self, url):
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        return len(content.get('results', 0))
