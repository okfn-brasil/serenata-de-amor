from django.test import TestCase

from jarbas.core.management.commands.loaddatasets import Command


class TestSerializer(TestCase):

    def setUp(self):
        self.command = Command()

    def test_force_int(self):
        self.assertEqual(self.command.force_int('1'), 1)
        self.assertEqual(self.command.force_int('1.0'), 1)
        with self.assertRaises(ValueError):
            self.command.force_int('abc')
