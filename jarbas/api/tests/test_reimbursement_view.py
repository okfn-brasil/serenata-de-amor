from datetime import date
from json import loads
from unittest.mock import patch

from django.core.cache import cache
from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data, suspicions


class TestListApi(TestCase):

    def setUp(self):

        data = [
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy(),
            sample_reimbursement_data.copy()
        ]

        data[1]['cnpj_cpf'] = '22222222222'
        data[1]['document_id'] = 42 * 2
        data[1]['issue_date'] = date(1969, 12, 31)
        data[1]['probability'] = None
        data[1]['subquota_id'] = 22

        data[2]['applicant_id'] = 13 * 3
        data[2]['cnpj_cpf'] = '22222222222'
        data[2]['document_id'] = 42 * 3
        data[2]['probability'] = 0.1
        data[2]['subquota_id'] = 22

        data[3]['applicant_id'] = 13 * 4
        data[3]['cnpj_cpf'] = '22222222222'
        data[3]['document_id'] = 42 * 4
        data[3]['probability'] = 0.9
        data[3]['subquota_id'] = 22
        data[3]['year'] = 1983
        data[3]['issue_date'] = '1970-02-01'

        for d in data:
            Reimbursement.objects.create(**d)

        url_name = 'api:reimbursement-list'
        self.all = resolve_url(url_name)
        self.by_year = resolve_url(url_name, year=1970)
        self.by_applicant = resolve_url(url_name, year=1970, applicant_id=13)

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

    def test_ordering(self):
        resp = self.client.get(self.all)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(4, len(content['results']))
        self.assertEqual('1969-12-31', content['results'][3]['issue_date'])

    def test_content_with_filters(self):
        url = self.all + (
            '?cnpj_cpf=22222222222'
            '&subquota_id=22'
            '&order_by=probability'
        )
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(3, len(content['results']))
        self.assertEqual(0.9, content['results'][0]['probability'])
        self.assertEqual(0.1, content['results'][1]['probability'])
        self.assertEqual(None, content['results'][2]['probability'])

    def test_content_with_date_filters(self):
        url = self.all + (
            '?issue_date_start=1970-01-01'
            '&issue_date_end=1970-02-01'
        )
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(2, len(content['results']))
        self.assertEqual(0.5, content['results'][0]['probability'])
        self.assertEqual(0.1, content['results'][1]['probability'])

    def test_more_than_one_document_query(self):
        extra = sample_reimbursement_data.copy()
        extra['document_id'] = 0
        Reimbursement.objects.create(**extra)
        url = self.all + '?document_id=42,84+126,+168'
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(4, len(content['results']))

    def _count_results(self, url):
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        return len(content.get('results', 0))


class TestRetrieveApi(TestCase):

    def setUp(self):
        Reimbursement.objects.create(**sample_reimbursement_data)
        unique_id = {'year': 1970, 'applicant_id': 13, 'document_id': 42}
        url = resolve_url('api:reimbursement-detail', **unique_id)
        self.resp = self.client.get(url)
        self.maxDiff = 2 ** 11

    def test_status(self):
        self.assertEqual(200, self.resp.status_code)

    def test_contents(self):
        contents = loads(self.resp.content.decode('utf-8'))
        expected = dict(
            applicant_id=13,
            batch_number=9,
            cnpj_cpf='11111111111111',
            congressperson_document=2,
            congressperson_id=1,
            congressperson_name='Roger That',
            document_id=42,
            document_number='6',
            document_type=7,
            document_value=8.90,
            installment=7,
            issue_date='1970-01-01',
            leg_of_the_trip='8',
            month=1,
            party='Partido',
            passenger='John Doe',
            all_reimbursement_numbers=[10, 11],
            all_reimbursement_values=[12.13, 14.15],
            all_net_values=[1.99, 2.99],
            remark_value=1.23,
            state='UF',
            subquota_description='Subquota description',
            subquota_group_description='Subquota group desc',
            subquota_group_id=5,
            subquota_id=4,
            supplier='Acme',
            term=1970,
            term_id=3,
            total_net_value=4.56,
            total_reimbursement_value=None,
            year=1970,
            probability=0.5,
            suspicions=suspicions,
            receipt=dict(fetched=False, url=None)
        )
        self.assertEqual(expected, contents)


class TestReceiptApi(TestCase):

    def setUp(self):
        self.obj = Reimbursement.objects.create(**sample_reimbursement_data)
        self.unique_id = {'year': 1970, 'applicant_id': 13, 'document_id': 42}
        self.url = resolve_url('api:reimbursement-receipt', **self.unique_id)
        self.expected_receipt_url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/13/1970/42.pdf'

    @patch('jarbas.core.models.head')
    def test_fetch_existing_receipt(self, mocked_head):
        mocked_head.return_value.status_code = 200
        resp = self.client.get(self.url)
        expected = dict(
            reimbursement=self.unique_id,
            url=self.expected_receipt_url
        )
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)

    @patch('jarbas.core.models.head')
    def test_fetch_non_existing_receipt(self, mocked_head):
        mocked_head.return_value.status_code = 404
        cache.clear()
        resp = self.client.get(self.url)
        expected = self.unique_id.copy()
        expected = dict(
            reimbursement=self.unique_id,
            url=None
        )
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)

    @patch('jarbas.core.models.head')
    def test_refetch_existing_receipt(self, mocked_head):
        self.obj.receipt_fetched = True
        self.obj.receipt_url = None
        self.obj.save()
        mocked_head.return_value.status_code = 200
        resp = self.client.get(self.url + '?force')
        expected = dict(
            reimbursement=self.unique_id,
            url=self.expected_receipt_url
        )
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)
