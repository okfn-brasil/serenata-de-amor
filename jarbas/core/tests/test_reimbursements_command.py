from datetime import date
from io import StringIO
from unittest.mock import MagicMock, call, patch

from django.test import TestCase

from jarbas.core.management.commands.reimbursements import Command
from jarbas.core.models import Reimbursement


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestSerializer(TestCommand):

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
            'issue_date': date(1970, 1, 1),
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
        input = {
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
        self.maxDiff = 2 ** 10
        self.assertEqual(self.command.serialize(input), expected)


class TestBulkCreate(TestCommand):

    @patch('jarbas.core.management.commands.reimbursements.Command.bulk_create')
    def test_bulk_create_by(self, bulk_create):
        self.command.bulk_create_by(range(0, 10), 3)
        expected = (
            call([0, 1, 2]),
            call([3, 4, 5]),
            call([6, 7, 8]),
            call([9])
        )
        bulk_create.assert_has_calls(expected)

    @patch.object(Reimbursement.objects, 'bulk_create')
    @patch('jarbas.core.management.commands.reimbursements.Command.print_count')
    def test_bulk_create(self, print_count, bulk_create):
        self.command.count = 0
        self.command.bulk_create([1, 2, 3])
        bulk_create.assert_called_once_with([1, 2, 3])
        self.assertEqual(1, print_count.call_count)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.reimbursements.print')
    @patch('jarbas.core.management.commands.reimbursements.Command.reimbursements')
    @patch('jarbas.core.management.commands.reimbursements.Command.bulk_create_by')
    @patch('jarbas.core.management.commands.reimbursements.Command.print_count')
    def test_handler_without_options(self, print_count, bulk_create_by, reimbursements, print_):
        reimbursements.return_value = (1, 2, 3)
        self.command.handle(dataset='reimbursements.xz', batch_size=42)
        print_.assert_called_once_with('Starting with 0 reimbursements')
        bulk_create_by.assert_called_once_with(reimbursements, 42)
        self.assertEqual('reimbursements.xz', self.command.path)

    @patch('jarbas.core.management.commands.reimbursements.print')
    @patch('jarbas.core.management.commands.reimbursements.Command.reimbursements')
    @patch('jarbas.core.management.commands.reimbursements.Command.bulk_create_by')
    @patch('jarbas.core.management.commands.reimbursements.Command.drop_all')
    @patch('jarbas.core.management.commands.reimbursements.Command.print_count')
    def test_handler_with_options(self, print_count, drop_all, bulk_create_by, reimbursements, print_):
        self.command.handle(dataset='reimbursements.xz', batch_size=1, drop=True)
        print_.assert_called_once_with('Starting with 0 reimbursements')
        drop_all.assert_called_once_with(Reimbursement)
        bulk_create_by.assert_called_once_with(reimbursements, 1)

    @patch('jarbas.core.management.commands.reimbursements.LoadCommand.add_arguments')
    def test_add_arguments(self, super_add_arguments):
        parser = MagicMock()
        self.command.add_arguments(parser)
        self.assertEqual(1, parser.add_argument.call_count)
        super_add_arguments.assert_called_once_with(parser)


class TestFileLoader(TestCommand):

    @patch('jarbas.core.management.commands.reimbursements.lzma')
    @patch('jarbas.core.management.commands.reimbursements.csv.DictReader')
    @patch('jarbas.core.management.commands.reimbursements.Reimbursement')
    @patch('jarbas.core.management.commands.reimbursements.Command.serialize')
    def test_reimbursement_property(self, serializer, reimbursement, row, lzma):
        lzma.return_value = StringIO()
        row.return_value = dict(ahoy=42)
        self.command.path = 'reimbursements.xz'
        list(self.command.reimbursements)
        self.assertEqual(1, reimbursement.call_count)
