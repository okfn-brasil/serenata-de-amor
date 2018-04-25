from django.contrib.staticfiles import finders
from django.test import TestCase


class TestStatic(TestCase):

    def test_digitalocean(self):
        self.assertTrue(finders.find('digitalocean.png'))
