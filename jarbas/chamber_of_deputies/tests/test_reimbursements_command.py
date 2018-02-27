import os
from datetime import date
from unittest.mock import Mock, PropertyMock, call, patch

from django.conf import settings
from django.test import TestCase

from jarbas.chamber_of_deputies.management.commands.reimbursements import Command
from jarbas.chamber_of_deputies.models import Reimbursement


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestCreateBatches(TestCommand):

    @patch.object(Command, 'print_count')
    @patch.object(Reimbursement.objects, 'bulk_create')
    @patch.object(Command, 'reimbursements', new_callable=PropertyMock)
    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.print')
    def test_create_batches(self, print_, reimbursements, bulk_create, print_count):
        reimbursements.return_value = (1, 2, 3)
        self.command.batch_size = 2
        self.command.batch = []
        self.command.create_batches()
        bulk_create.assert_has_calls((
            call([1, 2]),
            call([3])
        ))


class TestConventionMethods(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.create_batches')
    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.drop_all')
    def test_handler_with_options(self, drop_all, create):
        self.command.handle(dataset='reimbursements.xz')
        self.assertEqual('reimbursements.xz', self.command.path)
        self.assertEqual(4096, self.command.batch_size)
        create.assert_called_once_with()
        drop_all.assert_called_once_with(Reimbursement)

    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.create_batches')
    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.drop_all')
    def test_handler_with_options(self, drop_all, create):
        self.command.handle(dataset='foobar.xz', batch_size=2)
        self.assertEqual('foobar.xz', self.command.path)
        self.assertEqual(2, self.command.batch_size)
        create.assert_called_once_with()
        drop_all.assert_called_once_with(Reimbursement)


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        parser = Mock()
        Command().add_arguments(parser)
        self.assertEqual(2, parser.add_argument.call_count)


class TestFileLoader(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.print')
    def test_reimbursement_property(self, print_):
        self.command.path = os.path.join(
            settings.BASE_DIR,
            'jarbas',
            'core',
            'tests',
            'fixtures',
            'reimbursements.xz'
        )
        result, *_ = tuple(self.command.reimbursements)
        expected = Reimbursement(
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
            net_values='1.99,2.99',
            party='Partido',
            passenger='John Doe',
            reimbursement_numbers='10,11',
            reimbursement_values='12.13,14.15',
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
            year=1970
        )
        for field_object in Reimbursement._meta.fields:
            field = field_object.name
            with self.subTest():
                self.assertEqual(
                    getattr(expected, field),
                    getattr(result, field)
                )
