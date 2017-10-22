from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.chamber_of_deputies.tasks import (
    create_or_update_reimbursement,
    serialize_reimbursement
)


class TestCreateOrUpdateTask(TestCase):

    def setUp(self):
        self.csv_row_as_dict = {
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
            'issue_date': '01/01/1970',
            'leg_of_the_trip': '8',
            'month': '1',
            'net_values': '1.99,2.99',
            'party': 'Partido',
            'passenger': 'John Doe',
            'reimbursement_numbers': '10,11',
            'reimbursement_values': '12.13,14.15',
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
            'reimbursement_value_total': 'NaN',
            'year': '1970'
        }

    def test_serializer(self):
        expected = {
            'applicant_id': 13,
            'batch_number': 9,
            'cnpj_cpf': '11111111111111',
            'congressperson_document': 2,
            'congressperson_id': 1,
            'congressperson_name': 'Roger That',
            'document_id': 42,
            'document_number': '6',
            'document_type': 7,
            'document_value': 8.90,
            'installment': 7,
            'issue_date': '1970-01-01',
            'leg_of_the_trip': '8',
            'month': 1,
            'net_values': '1.99,2.99',
            'party': 'Partido',
            'passenger': 'John Doe',
            'reimbursement_numbers': '10,11',
            'reimbursement_values': '12.13,14.15',
            'remark_value': 1.23,
            'state': 'UF',
            'subquota_description': 'Subquota description',
            'subquota_group_description': 'Subquota group desc',
            'subquota_group_id': 5,
            'subquota_id': 4,
            'supplier': 'Acme',
            'term': 1970,
            'term_id': 3,
            'total_net_value': 4.56,
            'total_reimbursement_value': None,
            'year': 1970,
            'probability': None,
            'suspicions': None
        }
        self.maxDiff = 2 ** 10
        data = self.csv_row_as_dict.copy()
        self.assertEqual(expected, serialize_reimbursement(data))

    def test_create(self):
        self.assertEqual(0, Reimbursement.objects.count())
        data = self.csv_row_as_dict.copy()
        create_or_update_reimbursement(data)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_update(self):
        self.assertEqual(0, Reimbursement.objects.count())

        data = self.csv_row_as_dict.copy()
        serialized = serialize_reimbursement(data)
        serialized['search_vector'] = None
        mixer.blend(Reimbursement, **serialized)
        self.assertEqual(1, Reimbursement.objects.count())

        create_or_update_reimbursement(self.csv_row_as_dict)
        self.assertEqual(1, Reimbursement.objects.count())
