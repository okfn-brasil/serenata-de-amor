from io import StringIO
from unittest.mock import Mock, patch

from django.test import TestCase

from jarbas.core.management.commands.irregularities import Command
from jarbas.core.models import Reimbursement


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestSerializer(TestCommand):

    def test_serializer(self):
        expected = [
            {
                'applicant_id': 13,
                'document_id': 42,
                'year': 1970
            },
            {
                'probability': 0.38,
                'suspicions': {
                    'hypothesis_1': True,
                    'hypothesis_2': False
                }
            }
        ]
        input = {
            'applicant_id': '13',
            'document_id': '42',
            'hypothesis_1': 'True',
            'hypothesis_2': 'False',
            'probability': '0.38',
            'year': '1970'
        }
        self.assertEqual(list(self.command.serialize(input)), expected)

    def test_serializer_without_probability(self):
        expected = [
            {
                'applicant_id': 13,
                'document_id': 42,
                'year': 1970
            },
            {
                'probability': None,
                'suspicions': {
                    'hypothesis_1': True,
                    'hypothesis_2': False
                }
            }
        ]
        input = {
            'applicant_id': '13',
            'document_id': '42',
            'hypothesis_1': 'True',
            'hypothesis_2': 'False',
            'year': '1970'
        }
        self.assertEqual(list(self.command.serialize(input)), expected)


class TestMain(TestCommand):

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.update')
    @patch('jarbas.core.management.commands.irregularities.print')
    def test_main(self, print_, update, irregularities):
        irregularities.return_value = [({'filter': 0}, {'content': 1})]
        self.command.count = 999
        self.command.main()
        print_.assert_called_with('Preparing updates…')
        print_.assert_called_with('1,000 reimbursements updated.', end='\r')
        update.assert_called_once_with({'filter': 0}, {'content': 1})
        self.assertEqual(1000, self.command.count)

    @patch.object(Reimbursement.objects, 'filter')
    def test_update(self, filter):
        self.command.update({'filter': 0}, {'content': 1})
        filter.assert_called_once_with(filter=0)
        filter.return_value.update.assert_called_once_with(content=1)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.main')
    @patch('jarbas.core.management.commands.irregularities.os.path.exists')
    @patch('jarbas.core.management.commands.irregularities.print')
    def test_handler_without_options(self, print_, exists, main, irregularities):
        self.command.handle()
        main.assert_called_once_with()
        print_.assert_called_once_with('0 reimbursements updated.')
        self.assertEqual(self.command.path, 'irregularities.xz')

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.main')
    @patch('jarbas.core.management.commands.irregularities.os.path.exists')
    @patch('jarbas.core.management.commands.irregularities.print')
    def test_handler_with_options(self, print_, exists, main, irregularities):
        self.command.handle(irregularities_path='0')
        main.assert_called_once_with()
        print_.assert_called_once_with('0 reimbursements updated.')
        self.assertEqual('0', self.command.path)

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.main')
    @patch('jarbas.core.management.commands.irregularities.os.path.exists')
    def test_handler_with_non_existing_file(self, exists, main, irregularities):
        exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.command.handle()
        main.assert_not_called()


class TestFileLoader(TestCommand):

    @patch('jarbas.core.management.commands.irregularities.lzma')
    @patch('jarbas.core.management.commands.irregularities.csv.DictReader')
    @patch('jarbas.core.management.commands.irregularities.Command.serialize')
    @patch('jarbas.core.management.commands.irregularities.Command.get_dataset')
    def test_irregularities_property(self, get_dataset, serialize, rows, lzma):
        lzma.return_value = StringIO()
        rows.return_value = range(42)
        self.command.path = 'irregularities.xz'
        list(self.command.irregularities)
        self.assertEqual(42, serialize.call_count)


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        mock = Mock()
        Command().add_arguments(mock)
        self.assertEqual(1, mock.add_argument.call_count)
