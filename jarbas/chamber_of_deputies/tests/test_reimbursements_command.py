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

    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.create_batches')
    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.Command.drop_all')
    def test_handler_with_options(self, drop_all, create):
        self.command.handle(dataset='foobar.xz', batch_size=2)
        self.assertEqual('foobar.xz', self.command.path)
        self.assertEqual(2, self.command.batch_size)
        create.assert_called_once_with()


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        parser = Mock()
        Command().add_arguments(parser)
        self.assertEqual(3, parser.add_argument.call_count)


class TestFileLoader(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.reimbursements.print')
    def test_reimbursement_property(self, print_):
        self.command.path = os.path.join(
            settings.BASE_DIR,
            'jarbas',
            'core',
            'tests',
            'fixtures',
            'reimbursements.csv'
        )
        result, *_ = tuple(self.command.reimbursements)
        expected = Reimbursement(
            applicant_id=3052,
            batch_number=1524175,
            cnpj_cpf='05634562000100',
            congressperson_document=365,
            congressperson_id=178982,
            congressperson_name='LUIZ LAURO FILHO',
            document_id=6657248,
            document_number='827719',
            document_type=4,
            document_value=195.47,
            installment=0,
            issue_date=date(2018, 8, 15),
            leg_of_the_trip='',
            month=8,
            party='PSB',
            passenger='',
            numbers=['6369'],
            remark_value=0.0,
            state='SP',
            subquota_description='Fuels and lubricants',
            subquota_group_description='Veículos Automotores',
            subquota_group_id=1,
            subquota_number=3,
            supplier='POSTO AVENIDA NOSSA SENHORA DE FÁTIMA CAMPINAS LTDA',
            term=2015,
            term_id=55,
            total_net_value=195.47,
            total_value='0',
            year=2018,
        )
        for field_object in Reimbursement._meta.fields:
            field = field_object.name
            with self.subTest():
                self.assertEqual(
                    getattr(expected, field),
                    getattr(result, field),
                    field,
                )
