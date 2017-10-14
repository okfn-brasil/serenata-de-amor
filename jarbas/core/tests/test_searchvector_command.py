from unittest.mock import patch

from django.test import TestCase

from jarbas.chamber_of_deputies.management.commands.searchvector import Command
from jarbas.chamber_of_deputies.models import Reimbursement


class TestCommandHandler(TestCase):

    @patch.object(Reimbursement.objects, 'update')
    @patch('jarbas.chamber_of_deputies.management.commands.searchvector.print')
    def test_handler(self, print_, update):
        command = Command()
        command.handle()
        self.assertEqual(2, print_.call_count)
        self.assertEqual(1, update.call_count)
