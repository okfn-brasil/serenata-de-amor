from datetime import date

from django.test import TestCase

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.chamber_of_deputies.tasks import serialize


class TestCreateOrUpdateTask(TestCase):

    def setUp(self):
        self.data = {
            'applicant_id': '13',
            'batch_number': '9',
            'cnpj_cpf': '11111111111111',
            'congressperson_document': '2',
            'congressperson_id': '1',
            'congressperson_name': 'Roger That',
            'document_id': '42',
            'document_number': '6',
            'document_type': '7',
            'document_value': '8.90',
            'installment': '7',
            'issue_date': '2014-02-12T00:00:00',
            'leg_of_the_trip': '8',
            'month': '1',
            'party': 'Partido',
            'passenger': 'John Doe',
            'numbers': '[\'10\', \'11\']',
            'remark_value': '1.23',
            'state': 'UF',
            'subquota_description': 'Subquota description',
            'subquota_group_description': 'Subquota group desc',
            'subquota_group_id': '5',
            'subquota_number': '4',
            'supplier': 'Acme',
            'term': '1970',
            'term_id': '3',
            'total_net_value': '4.56',
            'year': '1970'
        }
        self.serialized = Reimbursement(
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
            issue_date=date(2014, 2, 12),
            leg_of_the_trip='8',
            month=1,
            party='Partido',
            passenger='John Doe',
            numbers=['10', '11'],
            remark_value=1.23,
            state='UF',
            subquota_description='Subquota description',
            subquota_group_description='Subquota group desc',
            subquota_group_id=5,
            subquota_number=4,
            supplier='Acme',
            term=1970,
            term_id=3,
            total_net_value=4.56,
            total_value=None,
            year=1970
        )

    def test_serialize(self):
        data = self.data.copy()
        result = serialize(data)
        expected = self.serialized
        for field_object in Reimbursement._meta.fields:
            field = field_object.name
            with self.subTest():
                self.assertEqual(
                    getattr(expected, field),
                    getattr(result, field)
                )
