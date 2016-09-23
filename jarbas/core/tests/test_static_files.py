from io import StringIO
from os import path, remove

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import TestCase


class TestStatic(TestCase):

    def test_digitalocean(self):
        self.assertTrue(finders.find('digitalocean.png'))


class TestCompiledStatic(TestCase):

    def setUp(self):
        [remove(f) for f in paths('app.css', 'app.js')]

    def test_css(self):
        self.assertEqual(None, finders.find('app.css'))
        call_command('assets', 'build', 'sass', '--no-cache')
        self.assertTrue(finders.find('app.css'))

    def test_js(self):
        self.assertEqual(None, finders.find('app.js'))
        call_command('assets', 'build', 'elm', '--no-cache')
        self.assertTrue(finders.find('app.js'))


class TestDownloadedStatic(TestCase):

    def setUp(self):
        [remove(f) for f in paths('ceap-datasets.html')]

    def test_ceap_datasets(self):
        self.assertEqual(None, finders.find('ceap-datasets.html'))
        call_command('ceapdatasets', stdout=StringIO())
        self.assertTrue(finders.find('ceap-datasets.html'))


def paths(*files):
    for name in files:
        filepath = path.join(settings.ASSETS_ROOT, name)
        if path.exists(filepath):
            yield filepath
