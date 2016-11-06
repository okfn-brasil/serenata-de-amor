from datetime import datetime

from django.test import TestCase

from jarbas.core.management.commands.loadsuppliers import Command


class TestStaticMethods(TestCase):

    def setUp(self):
        self.command = Command()

    def test_to_float(self):
        self.assertEqual(self.command.to_float(1), 1.0)
        self.assertEqual(self.command.to_float('abc'), None)

    def test_to_email(self):
        expected = 'jane@example.com'
        self.assertEqual(self.command.to_email('abc'), None)
        self.assertEqual(self.command.to_email('jane@example.com'), expected)

    def test_get_file_name(self):
        expected = '1970-01-01-ahoy.xz'
        with self.settings(AMAZON_S3_SUPPLIERS_DATE='1970-01-01'):
            self.assertEqual(self.command.get_file_name('ahoy'), expected)

    def test_to_date(self):
        expected = '1991-07-22'
        self.assertEqual(self.command.to_date('22/7/91'), expected)
        self.assertEqual(self.command.to_date('22/13/91'), None)
        self.assertEqual(self.command.to_date('aa/7/91'), None)
