from datetime import date
from io import StringIO
from unittest.mock import patch

from django.test import TestCase

from jarbas.core.management.commands.companies import Command
from jarbas.core.models import Activity, Company
from jarbas.core.tests import sample_company_data


class TestCommand(TestCase):

    def setUp(self):
        self.command = Command()


class TestSerializer(TestCommand):

    def test_to_email(self):
        expected = 'jane@example.com'
        self.assertEqual(self.command.to_email('abc'), None)
        self.assertEqual(self.command.to_email('jane@example.com'), expected)

    def test_serializer(self):
        company = {
            'email': 'ahoy',
            'opening': '31/12/1969',
            'situation_date': '31/12/1969',
            'special_situation_date': '31/12/1969',
            'latitude': '3.1415',
            'longitude': '-42'
        }
        expected = {
            'email': None,
            'opening': date(1969, 12, 31),
            'situation_date': date(1969, 12, 31),
            'special_situation_date': date(1969, 12, 31),
            'latitude': 3.1415,
            'longitude': -42.0
        }
        self.assertEqual(self.command.serialize(company), expected)


class TestCreate(TestCommand):

    @patch.object(Activity.objects, 'update_or_create')
    def test_save_activities(self, update_or_create):
        company = {
            'main_activity_code': '42',
            'main_activity': 'Ahoy'
        }
        for num in range(1, 100):
            company['secondary_activity_{}_code'.format(num)] = 100 + num
            company['secondary_activity_{}'.format(num)] = str(num)

        main, secondaries = self.command.save_activities(company)
        self.assertEqual(100, update_or_create.call_count)
        self.assertIsInstance(main, list)
        self.assertIsInstance(secondaries, list)
        self.assertEqual(1, len(main))
        self.assertEqual(99, len(secondaries))

    @patch('jarbas.core.management.commands.companies.lzma')
    @patch('jarbas.core.management.commands.companies.csv.DictReader')
    @patch('jarbas.core.management.commands.companies.Command.save_activities')
    @patch('jarbas.core.management.commands.companies.Command.serialize')
    @patch('jarbas.core.management.commands.companies.Command.print_count')
    @patch.object(Company.objects, 'create')
    def test_save_companies(self, create, print_count, serialize, save_activities, rows, lzma):
        self.command.count = 0
        lzma.return_value = StringIO()
        rows.return_value = [sample_company_data]
        serialize.return_value = dict(ahoy=42)
        save_activities.return_value = ([3], [14, 15])
        self.command.path = 'companies.xz'
        self.command.save_companies()
        create.assert_called_with(ahoy=42)
        create.return_value.main_activity.add.assert_called_with(3)
        self.assertEqual(2, create.return_value.secondary_activity.add.call_count)


class TestConventionMethods(TestCommand):

    @patch('jarbas.core.management.commands.companies.print')
    @patch('jarbas.core.management.commands.companies.LoadCommand.drop_all')
    @patch('jarbas.core.management.commands.companies.Command.save_companies')
    @patch('jarbas.core.management.commands.companies.Command.print_count')
    def test_handler_without_options(self, print_count, save_companies, drop_all, print_):
        print_count.return_value = 0
        self.command.handle(dataset='companies.xz')
        print_.assert_called_with('Starting with 0 companies')
        self.assertEqual(1, save_companies.call_count)
        self.assertEqual(1, print_count.call_count)
        self.assertEqual('companies.xz', self.command.path)
        drop_all.assert_not_called()

    @patch('jarbas.core.management.commands.companies.print')
    @patch('jarbas.core.management.commands.companies.Command.drop_all')
    @patch('jarbas.core.management.commands.companies.Command.save_companies')
    @patch('jarbas.core.management.commands.companies.Command.print_count')
    def test_handler_with_options(self, print_count, save_companies, drop_all, print_):
        print_count.return_value = 0
        self.command.handle(dataset='companies.xz', drop=True)
        print_.assert_called_with('Starting with 0 companies')
        self.assertEqual(2, drop_all.call_count)
        self.assertEqual(1, save_companies.call_count)
