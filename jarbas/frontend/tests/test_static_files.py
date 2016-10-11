from io import StringIO
from os import path, remove

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
            'frontend',
            'static',
            'ceap-datasets.html'
        )
        if path.exists(file_path):
            remove(file_path)

    def test_ceap_datasets(self):
        self.assertEqual(None, finders.find('ceap-datasets.html'))
        call_command('ceapdatasets', stdout=StringIO())
        self.assertTrue(finders.find('ceap-datasets.html'))
