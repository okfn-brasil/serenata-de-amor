from io import StringIO
from unittest.mock import Mock, call, patch

from django.test import TestCase

from jarbas.chamber_of_deputies.management.commands.receipts_text import Command
from jarbas.chamber_of_deputies.models import Reimbursement


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestSerializer(TestCommand):

    def test_serializer(self):
        expected = {
            'document_id': 42,
            'receipt_text': 'lorem ipsum',
        }

        input = {
            'document_id': '42',
            'text': 'lorem ipsum'
        }
        self.assertEqual(self.command.serialize(input), expected)

    def test_serializer_without_text(self):
        expected = {
            'document_id': 42,
            'receipt_text': None
        }

        input = {
            'document_id': '42',
        }
        self.assertEqual(self.command.serialize(input), expected)


class TestCustomMethods(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.receipts')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.schedule_update')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.update')
    def test_main(self, update, schedule_update, receipts):
        receipts.return_value = (range(21), range(21, 43))
        self.command.main()
        update.assert_has_calls([call()] * 2)
        schedule_update.assert_has_calls(call(i) for i in range(42))

    @patch.object(Reimbursement.objects, 'get')
    def test_schedule_update_existing_record(self, get):
        reimbursement = Reimbursement()
        get.return_value = reimbursement
        content = {
            'document_id': 42,
            'receipt_text': 'lorem ipsum'
        }
        self.command.queue = []
        self.command.schedule_update(content)
        get.assert_called_once_with(document_id=42)
        self.assertEqual(content['receipt_text'], reimbursement.receipt_text)

    @patch.object(Reimbursement.objects, 'get')
    def test_schedule_update_non_existing_record(self, get):
        get.side_effect = Reimbursement.DoesNotExist
        content = {'document_id': 42}
        self.command.queue = []
        self.command.schedule_update(content)
        get.assert_called_once_with(document_id=42)
        self.assertEqual([], self.command.queue)

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.bulk_update')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.print')
    def test_update(self, print_, bulk_update):
        self.command.count = 40
        self.command.queue = list(range(2))
        self.command.update()
        fields = ['receipt_text',]
        bulk_update.assert_called_with([0, 1], update_fields=fields)
        print_.assert_called_with('42 reimbursements updated.', end='\r')
        self.assertEqual(42, self.command.count)


class TestConventionMethods(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.receipts')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.main')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.os.path.exists')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.print')
    def test_handler_with_options(self, print_, exists, main, receipts):
        self.command.handle(dataset='receipts-texts.xz', batch_size=42)
        main.assert_called_once_with()
        print_.assert_called_once_with('0 reimbursements updated.')
        self.assertEqual(self.command.path, 'receipts-texts.xz')
        self.assertEqual(self.command.batch_size, 42)

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.receipts')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.main')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.os.path.exists')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.print')
    def test_handler_without_options(self, print_, exists, main, receipts):
        self.command.handle(dataset='receipts-texts.xz', batch_size=4096)
        main.assert_called_once_with()
        print_.assert_called_once_with('0 reimbursements updated.')
        self.assertEqual(self.command.path, 'receipts-texts.xz')
        self.assertEqual(self.command.batch_size, 4096)

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.receipts')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.main')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.os.path.exists')
    def test_handler_with_non_existing_file(self, exists, update, receipts):
        exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.command.handle(dataset='receipts-text.xz', batch_size=4096)
        update.assert_not_called()


class TestFileLoader(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.print')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.lzma')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.csv.DictReader')
    @patch('jarbas.chamber_of_deputies.management.commands.receipts_text.Command.serialize')
    def test_receipts(self, serialize, rows, lzma, print_):
        serialize.return_value = '.'
        lzma.return_value = StringIO()
        rows.return_value = range(42)
        self.command.batch_size = 10
        self.command.path = 'receipts-text.xz'
        expected = [['.'] * 10, ['.'] * 10, ['.'] * 10, ['.'] * 10, ['.'] * 2]
        self.assertEqual(expected, list(self.command.receipts()))
        self.assertEqual(42, serialize.call_count)


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        mock = Mock()
        Command().add_arguments(mock)
        self.assertEqual(2, mock.add_argument.call_count)
