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


class TestCreate(TestCommand):

    @patch.object(Command, 'print_count')
    @patch('jarbas.core.management.commands.reimbursements.print')
    @patch('jarbas.core.management.commands.reimbursements.create_or_update_reimbursement')
    def test_create_or_update(self, create, print_, print_count):
        reimbursements = (
            dict(ahoy=42, document_id=1),
            dict(ahoy=84, document_id=2)
        )
        self.command.create_or_update(reimbursements)
        create.delay.assert_has_calls((call(r) for r in reimbursements))


class TestMarkNonUpdated(TestCommand):

    @patch.object(Reimbursement.objects, 'filter')
    def test_mark_available_in_latest_dataset(self, filter_):
        self.command.started_at = 42
        self.command.mark_not_updated_reimbursements()
        filter_.assert_called_once_with(last_update__lt=self.command.started_at)
        filter_.return_value.update.assert_called_once_with(available_in_latest_dataset=False)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.reimbursements.Command.reimbursements')
    @patch('jarbas.core.management.commands.reimbursements.Command.create_or_update')
    @patch('jarbas.core.management.commands.reimbursements.Command.mark_not_updated_reimbursements')
    def test_handler_without_options(self, mark, create, reimbursements):
        reimbursements.return_value = (1, 2, 3)
        self.command.handle(dataset='reimbursements.xz')
        create.assert_called_once_with(reimbursements)
        self.assertEqual('reimbursements.xz', self.command.path)
        mark.assert_called_once_with()

    @patch('jarbas.core.management.commands.reimbursements.Command.reimbursements')
    @patch('jarbas.core.management.commands.reimbursements.Command.create_or_update')
    @patch('jarbas.core.management.commands.reimbursements.Command.drop_all')
    @patch('jarbas.core.management.commands.reimbursements.Command.mark_not_updated_reimbursements')
    def test_handler_with_options(self, mark, drop_all, create, reimbursements):
        self.command.handle(dataset='reimbursements.xz', drop=True)
        drop_all.assert_called_once_with(Reimbursement)
        create.assert_called_once_with(reimbursements)
        mark.assert_called_once_with()


class TestFileLoader(TestCommand):

    @patch('jarbas.core.management.commands.reimbursements.lzma')
    @patch('jarbas.core.management.commands.reimbursements.csv.DictReader')
    @patch('jarbas.core.management.commands.reimbursements.Command.serialize')
    def test_reimbursement_property(self, serializer, row, lzma):
        lzma.return_value = StringIO()
        row.return_value = dict(ahoy=42)
        self.command.path = 'reimbursements.xz'
        list(self.command.reimbursements)
        self.assertEqual(1, serializer.call_count)
