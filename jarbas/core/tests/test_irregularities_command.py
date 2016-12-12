from io import StringIO
from unittest.mock import patch

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


class TestUpdate(TestCommand):

    @patch.object(Reimbursement.objects, 'filter')
    @patch('jarbas.core.management.commands.irregularities.print')
    def test_update(self, p, filter):
        self.command.count = 999
        self.command.update([({'filter': 0}, {'content': 1})])
        filter.assert_called_once_with(filter=0)
        filter.return_value.update.assert_called_once_with(content=1)
        p.assert_called_once_with('1,000 reimbursements updated.', end='\r')
        self.assertEqual(1000, self.command.count)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.update')
    def test_handler_without_options(self, update, irregularities):
        self.command.handle(source=False)
        update.assert_called_once_with(irregularities)
        self.assertIsNone(self.command.date)
        self.assertFalse(self.command.source)

    @patch('jarbas.core.management.commands.irregularities.Command.irregularities')
    @patch('jarbas.core.management.commands.irregularities.Command.update')
    def test_handler_with_options(self, update, irregularities):
        self.command.handle(source='0', dataset_version='1')
        update.assert_called_once_with(irregularities)
        self.assertEqual('1', self.command.date)
        self.assertEqual('0', self.command.source)


class TestFileLoader(TestCommand):

    @patch('jarbas.core.management.commands.irregularities.lzma')
    @patch('jarbas.core.management.commands.irregularities.csv.DictReader')
    @patch('jarbas.core.management.commands.irregularities.Command.serialize')
    @patch('jarbas.core.management.commands.irregularities.Command.get_dataset')
    def test_irregularities_property(self, get_dataset, serialize, rows, lzma):
        lzma.return_value = StringIO()
        rows.return_value = range(42)
        list(self.command.irregularities)
        self.assertEqual(42, serialize.call_count)
