from io import StringIO
from os import path, remove, rename
from unittest.mock import patch

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import TestCase


class TestStatic(TestCase):

    def test_digitalocean(self):
        self.assertTrue(finders.find('digitalocean.png'))


class TestDownloadedStatic(TestCase):

    def setUp(self):
        file_path = path.join(
            settings.BASE_DIR,
            'jarbas',
            'layers',
            'static',
            'ceap-datasets.html'
        )
        if path.exists(file_path):
            remove(file_path)

    @patch('jarbas.chamber_of_deputies.management.commands.ceapdatasets.urlretrieve')
    def test_ceap_datasets(self, mock_urlretrieve):

        # backup existing file if exists
        original = path.join(settings.CORE_STATIC_DIR, 'ceap-datasets.html')
        backup = original + '.bkp'
        if path.exists(original):
            rename(original, backup)

        # test
        self.assertEqual(None, finders.find('ceap-datasets.html'))
        call_command('ceapdatasets', stdout=StringIO())
        self.assertTrue(finders.find('ceap-datasets.html'))

        # restore existing file backup
        if path.exists(backup):
            remove(backup, original)
