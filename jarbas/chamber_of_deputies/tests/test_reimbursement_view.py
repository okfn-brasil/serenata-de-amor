from json import loads
from unittest.mock import patch
from urllib.parse import urlencode

from django.shortcuts import resolve_url
from django.test import TestCase
from freezegun import freeze_time
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.tests import get_sample_reimbursement_api_response
from jarbas.chamber_of_deputies.models import Reimbursement, Tweet
from jarbas.chamber_of_deputies.tests import random_tweet_status


def get_reimbursement(**kwargs):
    quantity = kwargs.pop('quantity', 1)
    kwargs['net_values'] = '1.99,2.99'
    kwargs['reimbursement_values'] = '200.00,500.00'
    kwargs['reimbursement_numbers'] = '2,3'
    if quantity == 1:
        return mixer.blend(Reimbursement, search_vector=None, **kwargs)
    return mixer.cycle(quantity).blend(Reimbursement, search_vector=None, **kwargs)


class TestListApi(TestCase):

    def setUp(self):
        get_reimbursement(quantity=3)
        self.url = resolve_url('chamber_of_deputies:reimbursement-list')

    def test_status(self):
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    def test_content_general(self):
        self.assertEqual(3, Reimbursement.objects.count())
        self.assertEqual(3, self._count_results(self.url))

    def test_ordering(self):
        """
        Ordering depends on year and issue_date, but by using mixer we don't
        know if year matches the issue date fields, so we cleanup first.
        """
        Reimbursement.objects.all().delete()
        get_reimbursement(quantity=3, year=1970)
        resp = self.client.get(self.url)
        content = loads(resp.content.decode('utf-8'))
        first = content['results'][0]
        last = content['results'][-1]
        self.assertEqual(3, len(content['results']))
        self.assertTrue(first['issue_date'] >= last['issue_date'])

    def test_content_with_cnpj_cpf_filter(self):
        search_data = (
            ('cnpj_cpf', '12345678901'),
            ('subquota_id', '22'),
            ('order_by', 'probability'),
            ('suspicions', '1'),
        )
        url = '{}?{}'.format(self.url, urlencode(search_data))
        target_result = get_reimbursement(cnpj_cpf='12345678901', subquota_id=22, suspicions=1)
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(1, len(content['results']))
        self.assertEqual(target_result.cnpj_cpf, content['results'][0]['cnpj_cpf'])

    def test_content_with_availability_in_latest_dataset(self):
        get_reimbursement(available_in_latest_dataset=False)
        url = self.url + '?in_latest_dataset=0'
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(1, len(content['results']))

    def test_content_with_date_filters(self):
        get_reimbursement(issue_date='1970-01-01')
        get_reimbursement(issue_date='1970-01-01')
        search_data = (
            ('issue_date_start', '1970-01-01'),
            ('issue_date_end', '1970-02-02'),
        )
        url = '{}?{}'.format(self.url, urlencode(search_data))
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(2, len(content['results']))

    def test_more_than_one_document_query(self):
        get_reimbursement(quantity=4, document_id=(id for id in (42, 84, 126, 168)))
        url = self.url + '?document_id=42,84+126,+168'
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(4, len(content['results']))

    def _count_results(self, url):
        resp = self.client.get(url)
        content = loads(resp.content.decode('utf-8'))
        return len(content.get('results', 0))


@freeze_time('1970-01-01 00:00:00')
class TestRetrieveApi(TestCase):

    def setUp(self):
        self.reimbursement = get_reimbursement()
        self.sample_response = get_sample_reimbursement_api_response(
            self.reimbursement
        )
        url = resolve_url('chamber_of_deputies:reimbursement-detail',
                          document_id=self.reimbursement.document_id)
        self.resp = self.client.get(url)
        self.maxDiff = 2 ** 11

    def test_status(self):
        self.assertEqual(200, self.resp.status_code)

    def test_contents(self):
        contents = loads(self.resp.content.decode('utf-8'))
        self.sample_response['rosies_tweet'] = None
        self.assertEqual(self.sample_response, contents)

    def test_contents_with_tweet(self):
        status = random_tweet_status()
        mixer.blend(Tweet, reimbursement=self.reimbursement, status=status)
        expected = self.sample_response
        expected['rosies_tweet'] = self.reimbursement.tweet.get_url()
        url = resolve_url('chamber_of_deputies:reimbursement-detail',
                          document_id=self.reimbursement.document_id)
        resp = self.client.get(url)
        contents = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, contents)

    def test_contents_with_receipt_text(self):
        expected = self.sample_response
        expected['rosies_tweet'] = None
        expected['receipt_text'] = self.reimbursement.receipt_text
        url = resolve_url('chamber_of_deputies:reimbursement-detail',
                          document_id=self.reimbursement.document_id)
        resp = self.client.get(url)
        contents = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, contents)


class TestReceiptApi(TestCase):

    def setUp(self):
        self.reimbursement = get_reimbursement(
            year=2017,
            applicant_id=1,
            document_id=20,
            receipt_url='http://www.camara.gov.br/cota-parlamentar/documentos/publ/1/2017/20.pdf'
        )
        self.reimbursement_no_receipt = get_reimbursement(receipt_url=None)
        self.url = resolve_url(
            'chamber_of_deputies:reimbursement-receipt',
            document_id=self.reimbursement.document_id
        )
        self.url_no_receipt = resolve_url(
            'chamber_of_deputies:reimbursement-receipt',
            document_id=self.reimbursement_no_receipt.document_id
        )

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_fetch_existing_receipt(self, mocked_head):
        mocked_head.return_value.status_code = 200
        resp = self.client.get(self.url)
        expected = dict(url=self.reimbursement.receipt_url)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_fetch_non_existing_receipt(self, mocked_head):
        mocked_head.return_value.status_code = 404
        resp = self.client.get(self.url_no_receipt)
        expected = dict(url=None)
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_refetch_existing_receipt(self, mocked_head):
        expected = dict(url=self.reimbursement.receipt_url)
        self.reimbursement.receipt_fetched = True
        self.reimbursement.receipt_url = None
        self.reimbursement.save()
        mocked_head.return_value.status_code = 200
        resp = self.client.get(self.url + '?force')
        content = loads(resp.content.decode('utf-8'))
        self.assertEqual(expected, content)
