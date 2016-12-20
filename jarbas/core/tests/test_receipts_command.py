from unittest.mock import call, patch

from django.test import TestCase

from jarbas.core.management.commands.receipts import Command
from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data


class TestCommand(TestCase):


    @patch.object(Reimbursement, 'get_receipt_url')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_update(self, print_, get_receipt_url):
        Reimbursement.objects.create(**sample_reimbursement_data)
        command = Command()
        command.handle()
        self.assertEqual(1, get_receipt_url.call_count)
        self.assertEqual(1, command.count)
        print_.asset_has_calls([
            call('Loading…'),
            call('1 receipt URLs fetched…', end='\r'),
            call('1 receipt URLs fetched…', end='\n'),
            call('Done!'),
        ])
