import json

from django.shortcuts import resolve_url
from django.test import TestCase

from jarbas.core.models import Document


class TestGet(TestCase):

    def setUp(self):
        Document.objects.create(
            document_id=42,
            congressperson_name='Roger That',
            congressperson_id=1,
            congressperson_document=2,
            term=1970,
            state='UF',
            party='Partido',
            term_id=3,
            subquota_number=4,
            subquota_description='Subquota description',
            subquota_group_id=5,
            subquota_group_description='Subquota group description',
            supplier='Acme',
            cnpj_cpf='11111111111111',
            document_number='6',
            document_type=7,
            issue_date='1970-01-01 00:00:00',
            document_value=8.90,
            remark_value=1.23,
            net_value=4.56,
            month=1,
            year=1970,
            installment=7,
            passenger='John Doe',
            leg_of_the_trip=8,
            batch_number=9,
            reimbursement_number=10,
            reimbursement_value=11.12,
            applicant_id=13
        )
        self.resp = self.client.get(resolve_url('api:document', 42))

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_content(self):
        content = json.loads(self.resp.content.decode('utf-8'))
        self.assertEqual('Roger That', content['congressperson_name'])
        self.assertEqual(4.56, content['net_value'])


class Test404(TestCase):

    def setUp(self):
        self.resp = self.client.get(resolve_url('api:document', 42))

    def test_status_code(self):
        self.assertEqual(404, self.resp.status_code)
