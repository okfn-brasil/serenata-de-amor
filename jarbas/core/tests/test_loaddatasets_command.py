from django.test import TestCase

from jarbas.core.management.commands.loaddatasets import Command


class TestSerializer(TestCase):

    def setUp(self):
        self.command = Command()

    def test_force_int(self):
        self.assertEqual(self.command.force_int('1'), 1)
        self.assertEqual(self.command.force_int('1.0'), 1)
        with self.assertRaises(ValueError):
            self.command.force_int('abc')

    def test_serializer(self):
        expected = {
            'document_id': 1,
            'congressperson_id': 1,
            'congressperson_document': 1,
            'term': 1,
            'term_id': 1,
            'subquota_number': 1,
            'subquota_group_id': 1,
            'document_type': 1,
            'month': 1,
            'year': 1,
            'installment': 1,
            'batch_number': 1,
            'reimbursement_number': 1,
            'applicant_id': 1,
            'document_value': 1.1,
            'remark_value': 1.1,
            'net_value': 1.1,
            'reimbursement_value': 1.1,
            'issue_date': None,
        }

        document = {
            'document_id': '1',
            'congressperson_id': '1',
            'congressperson_document': '1',
            'term': '1',
            'term_id': '1',
            'subquota_number': '1',
            'subquota_group_id': '1',
            'document_type': '1',
            'month': '1',
            'year': '1',
            'installment': '1',
            'batch_number': '1',
            'reimbursement_number': '1',
            'applicant_id': '1',
            'document_value': '1.1',
            'remark_value': '1.1',
            'net_value': '1.1',
            'reimbursement_value': '1.1',
            'issue_date': '',
        }
        self.assertEqual(self.command.serialize(document), expected)
