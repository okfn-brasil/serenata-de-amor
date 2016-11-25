from datetime import date
from io import StringIO
from unittest.mock import MagicMock, call, patch

from django.test import TestCase

from jarbas.core.management.commands.loaddatasets import Command
from jarbas.core.models import Document


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestSerializer(TestCommand):

    def test_force_int(self):
        self.assertEqual(self.command.force_int('1'), 1)
        self.assertEqual(self.command.force_int('1.0'), 1)
        with self.assertRaises(ValueError):
            self.command.force_int('abc')

    def test_to_number(self):
        self.assertEqual(self.command.to_number('1', float), 1.0)
        self.assertEqual(self.command.to_number('1', int), 1)
        self.assertEqual(self.command.to_number('1.2', float), 1.2)
        self.assertEqual(self.command.to_number('1.2', int), 1)
        self.assertEqual(self.command.to_number('NaN', int), 0)
        self.assertEqual(self.command.to_number('', int), 0)
        with self.assertRaises(TypeError):
            self.command.to_number('1')
        with self.assertRaises(ValueError):
            self.command.to_number('abc', int)

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
            'issue_date': date(2012, 8, 20),
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
            'issue_date': '2012-08-20 00:00:00',
        }
        self.assertEqual(self.command.serialize(document), expected)


class TestFileLoader(TestCommand):

    def test_get_suffix(self):
        name = '1980-01-01-current-year.xz'
        self.assertEqual(self.command.get_suffix(name), 'current-year')
        self.assertEqual(self.command.get_suffix(''), None)

    @patch('jarbas.core.management.commands.loaddatasets.LoadCommand.load_local')
    def test_get_load_local(self, super_load_local):
        list(self.command.load_local('ahoy'))
        expected = (
            call('ahoy', 'current-year'),
            call('ahoy', 'last-year'),
            call('ahoy', 'previous-years')
        )
        super_load_local.assert_has_calls(expected)

    @patch('jarbas.core.management.commands.loaddatasets.LoadCommand.load_remote')
    def test_get_load_remote(self, super_load_remote):
        list(self.command.load_remote())
        expected = (
            call('current-year'),
            call('last-year'),
            call('previous-years')
        )
        super_load_remote.assert_has_calls(expected)

    @patch('jarbas.core.management.commands.loaddatasets.lzma')
    @patch('jarbas.core.management.commands.loaddatasets.csv.DictReader')
    @patch('jarbas.core.management.commands.loaddatasets.Document')
    @patch('jarbas.core.management.commands.loaddatasets.Command.serialize')
    def test_documents_from(self, serializer, document, row, lzma):
        lzma.return_value = StringIO()
        row.return_value = dict(ahoy=42)
        list(self.command.documents_from(range(0, 3)))
        self.assertEqual(3, document.call_count)


class TestBulkCreate(TestCommand):

    @patch.object(Document.objects, 'bulk_create')
    @patch('jarbas.core.management.commands.loaddatasets.Command.print_count')
    def test_bulk_create_by(self, print_count, bulk_create):
        self.command.bulk_create_by(range(0, 10), 3)
        expected = (
            call([0, 1, 2]),
            call([3, 4, 5]),
            call([6, 7, 8]),
            call([9])
        )
        bulk_create.assert_has_calls(expected)
        self.assertEqual(4, print_count.call_count)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.loaddatasets.print')
    @patch('jarbas.core.management.commands.loaddatasets.Command.load_remote')
    @patch('jarbas.core.management.commands.loaddatasets.Command.documents_from')
    @patch('jarbas.core.management.commands.loaddatasets.Command.bulk_create_by')
    def test_handler_without_options(self, bulk_create_by, documents_from, load_remote, print_):
        documents_from.return_value = (1, 2, 3)
        self.command.handle(batch_size=42, source=False)
        print_.assert_called_once_with('Starting with 0 documents')
        self.assertEqual(1, load_remote.call_count)
        bulk_create_by.assert_called_once_with((1, 2, 3), 42)

    @patch('jarbas.core.management.commands.loaddatasets.print')
    @patch('jarbas.core.management.commands.loaddatasets.Command.load_local')
    @patch('jarbas.core.management.commands.loaddatasets.Command.documents_from')
    @patch('jarbas.core.management.commands.loaddatasets.Command.bulk_create_by')
    @patch('jarbas.core.management.commands.loaddatasets.Command.drop_all')
    def test_handler_with_options(self, drop_all, bulk_create_by, documents_from, load_local, print_):
        documents_from.return_value = (1, 2, 3)
        self.command.handle(batch_size=42, source='ahoy', drop=True)
        print_.assert_called_once_with('Starting with 0 documents')
        self.assertEqual(1, load_local.call_count)
        drop_all.assert_called_once_with(Document)
        bulk_create_by.assert_called_once_with((1, 2, 3), 42)

    @patch('jarbas.core.management.commands.loaddatasets.LoadCommand.add_arguments')
    def test_add_arguments(self, super_add_arguments):
        parser = MagicMock()
        self.command.add_arguments(parser)
        self.assertEqual(1, parser.add_argument.call_count)
        super_add_arguments.assert_called_once_with(parser)
