from json import loads

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.core.models import Company
from jarbas.chamber_of_deputies.tests import sample_reimbursement_data
from jarbas.core.tests import sample_company_data
from jarbas.chamber_of_deputies.serializers import format_cnpj


class TestSameDay(TestCase):

    def setUp(self):
        self.maxDiff = 2 ** 10
        cnpj = '12345678901234'

        company1 = sample_company_data.copy()
        company1['cnpj'] = format_cnpj(cnpj)
        company1['city'] = 'Atlantis'
        company1['state'] = 'WE'
        Company.objects.create(**company1)

        company2 = sample_company_data.copy()
        company2['cnpj'] = format_cnpj(cnpj[::-1])
        Company.objects.create(**company2)

        data1 = sample_reimbursement_data.copy()
        data1['document_id'] = 42 * 2
        data1['cnpj_cpf'] = cnpj
        Reimbursement.objects.create(**data1)

        data2 = sample_reimbursement_data.copy()
        data2['document_id'] = 42 * 3
        data2['cnpj_cpf'] = cnpj
        Reimbursement.objects.create(**data2)

        data3 = sample_reimbursement_data.copy()
        data3['document_id'] = 42 * 4
        data3['cnpj_cpf'] = cnpj[::-1]
        Reimbursement.objects.create(**data3)

        data4 = sample_reimbursement_data.copy()
        data4['document_id'] = 42 * 5
        data4['cnpj_cpf'] = '11111111111111'
        Reimbursement.objects.create(**data4)

        url = resolve_url('chamber_of_deputies:reimbursement-same-day', document_id=84)
        self.resp = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_contents(self):
        expected = (
            {
                'applicant_id': 13,
                'city': 'Atlantis, WE',
                'document_id': 126,
                'subquota_id': 4,
                'subquota_description': 'Subquota description',
                'supplier': 'Acme',
                'total_net_value': 4.56,
                'year': 1970
            },
            {
                'applicant_id': 13,
                'city': None,
                'document_id': 168,
                'subquota_id': 4,
                'subquota_description': 'Subquota description',
                'supplier': 'Acme',
                'total_net_value': 4.56,
                'year': 1970
            },
            {
                'applicant_id': 13,
                'city': None,
                'document_id': 210,
                'subquota_id': 4,
                'subquota_description': 'Subquota description',
                'supplier': 'Acme',
                'total_net_value': 4.56,
                'year': 1970
            }
        )
        content = loads(self.resp.content.decode('utf-8'))
        self.assertEqual(3, int(content['count']))
        for reimbursement in expected:
            with self.subTest():
                self.assertIn(reimbursement, content['results'])
