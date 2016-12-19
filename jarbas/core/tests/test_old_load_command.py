from unittest.mock import Mock, patch

from django.test import TestCase

from jarbas.core.management.commands import OldLoadCommand


class TestFileLoader(TestCase):

    def setUp(self):
        self.cmd = OldLoadCommand()
        self.cmd.date = '1970-01-01'

    @patch('jarbas.core.management.commands.OldLoadCommand.load_remote')
    @patch('jarbas.core.management.commands.print')
    def test_get_database(self, print_, load_remote):
        self.cmd.source = None
        self.cmd.get_dataset('dataset')
        load_remote.assert_called_once_with('dataset')

    @patch('jarbas.core.management.commands.os.path.exists')
    @patch('jarbas.core.management.commands.print')
    def test_get_database_with_source(self, print_, exists):
        exists.return_value = True
        self.cmd.source = '/whatever/works'
        expected = '/whatever/works/1970-01-01-dataset.xz'
        self.assertEqual(expected, self.cmd.get_dataset('dataset'))
        print_.assert_called_once_with('Loading ' + expected)

    @patch('jarbas.core.management.commands.os.path.exists')
    @patch('jarbas.core.management.commands.print')
    def test_get_database_with_wrong_source(self, print_, exists):
        exists.return_value = False
        self.cmd.source = '/whatever/works'
        expected = '/whatever/works/1970-01-01-dataset.xz'
        self.assertIsNone(self.cmd.get_dataset('dataset'))
        print_.assert_called_once_with(expected + ' not found')

class TestLocalMethods(TestCase):

    def setUp(self):
        self.cmd = OldLoadCommand()
        self.source = '/whatever/works'
        self.name = 'dataset'

    def test_get_path(self):
        self.cmd.date = None
        expected = '/whatever/works/1970-01-01-dataset.xz'
        with self.settings(AMAZON_S3_DATASET_DATE='1970-01-01'):
            result = self.cmd.get_path(self.source, self.name)
            self.assertEqual(expected, result)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.os.path.exists')
    def test_load_local_exists(self, mock_exists, mock_print):
        self.cmd.date = None
        mock_exists.return_value = True
        self.assertIsInstance(self.cmd.load_local(self.source, self.name), str)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.os.path.exists')
    def test_load_local_fail(self, mock_exists, mock_print):
        self.cmd.date = None
        mock_exists.return_value = False
        self.assertFalse(self.cmd.load_local(self.source, self.name))


class TestRemoteMethods(TestCase):

    def setUp(self):
        self.cmd = OldLoadCommand()
        self.name = 'companies'
        self.url = 'https://south.amazonaws.com/jarbas/1970-01-01-companies.xz'
        self.custom_settings = {
            'AMAZON_S3_COMPANIES_DATE': '1970-01-01',
            'AMAZON_S3_REGION': 'south',
            'AMAZON_S3_BUCKET': 'jarbas'
        }

    def test_get_url(self):
        self.cmd.date = None
        with self.settings(**self.custom_settings):
            result = self.cmd.get_url(self.name)
            self.assertEqual(self.url, result)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.urlretrieve')
    def test_load_remote(self, mock_urlretrieve, mock_print):
        self.cmd.date = None
        with self.settings(**self.custom_settings):
            result = self.cmd.load_remote(self.name)
            self.assertEqual(self.url, mock_urlretrieve.call_args[0][0])
            self.assertIsInstance(result, str)


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        mock = Mock()
        OldLoadCommand().add_arguments(mock)
        self.assertEqual(3, mock.add_argument.call_count)