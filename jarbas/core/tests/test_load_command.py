from unittest.mock import Mock, patch
from django.test import TestCase

from jarbas.core.management.commands import LoadCommand
from jarbas.core.models import Activity
from jarbas.core.tests import sample_activity_data


class TestStaticMethods(TestCase):

    def setUp(self):
        self.cmd = LoadCommand()

    def test_get_file_name(self):
        expected = '1970-01-01-ahoy.xz'
        with self.settings(AMAZON_S3_DATASET_DATE='1970-01-01'):
            self.assertEqual(expected, self.cmd.get_file_name('ahoy'))

    def test_get_model_name(self):
        self.assertEqual('Activity', self.cmd.get_model_name(Activity))


class TestPrintCount(TestCase):

    def setUp(self):
        self.cmd = LoadCommand()

    @patch('jarbas.core.management.commands.print')
    def test_print_no_records(self, mock_print):
        self.cmd.print_count(Activity)
        arg = 'Current count: 0 Activitys                                    '
        kwargs = {'end': '\r'}
        mock_print.assert_called_with(arg, **kwargs)

    @patch('jarbas.core.management.commands.print')
    def test_print_with_records(self, mock_print):
        Activity.objects.create(**sample_activity_data)
        self.cmd.print_count(Activity)
        arg = 'Current count: 1 Activitys                                    '
        kwargs = {'end': '\r'}
        mock_print.assert_called_with(arg, **kwargs)

    @patch('jarbas.core.management.commands.print')
    def test_print_with_permanent_keyword_arg(self, mock_print):
        self.cmd.print_count(Activity, permanent=True)
        arg = 'Current count: 0 Activitys                                    '
        kwargs = {'end': '\n'}
        mock_print.assert_called_with(arg, **kwargs)


class TestDropAll(TestCase):

    def test_drop_all(self):
        self.assertEqual(0, Activity.objects.count())
        Activity.objects.create(**sample_activity_data)
        self.assertEqual(1, Activity.objects.count())
        LoadCommand().drop_all(Activity)
        self.assertEqual(0, Activity.objects.count())


class TestLocalMethods(TestCase):

    def setUp(self):
        self.cmd = LoadCommand()
        self.source = '/whatever/works'
        self.name = 'ahoy'

    def test_get_path(self):
        expected = '/whatever/works/1970-01-01-ahoy.xz'
        with self.settings(AMAZON_S3_DATASET_DATE='1970-01-01'):
            result = self.cmd.get_path(self.source, self.name)
            self.assertEqual(expected, result)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.os.path.exists')
    def test_load_local_exists(self, mock_exists, mock_print):
        mock_exists.return_value = True
        self.assertIsInstance(self.cmd.load_local(self.source, self.name), str)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.os.path.exists')
    def test_load_local_fail(self, mock_exists, mock_print):
        mock_exists.return_value = False
        self.assertFalse(self.cmd.load_local(self.source, self.name))


class TestRemoteMethods(TestCase):

    def setUp(self):
        self.cmd = LoadCommand()
        self.name = 'ahoy'
        self.url = 'https://south.amazonaws.com/jarbas/1970-01-01-ahoy.xz'
        self.custom_settings = {
            'AMAZON_S3_DATASET_DATE': '1970-01-01',
            'AMAZON_S3_REGION': 'south',
            'AMAZON_S3_BUCKET': 'jarbas'
        }

    def test_get_url(self):
        with self.settings(**self.custom_settings):
            result = self.cmd.get_url(self.name)
            self.assertEqual(self.url, result)

    @patch('jarbas.core.management.commands.print')
    @patch('jarbas.core.management.commands.urlretrieve')
    def test_load_remote(self, mock_urlretrieve, mock_print):
        with self.settings(**self.custom_settings):
            result = self.cmd.load_remote(self.name)
            self.assertEqual(self.url, mock_urlretrieve.call_args[0][0])
            self.assertIsInstance(result, str)


class TestAddArguments(TestCase):

    def test_add_arguments(self):
        mock = Mock()
        LoadCommand().add_arguments(mock)
        self.assertEqual(2, mock.add_argument.call_count)