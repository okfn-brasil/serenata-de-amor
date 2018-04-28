from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.management.commands.searchvector import Command
from jarbas.chamber_of_deputies.models import Reimbursement


class TestCommandHandler(TestCase):

    def test_handler(self):
        mixer.cycle(3).blend(Reimbursement, search_vector=None)
        command = Command()
        command.handle(batch_size=2, silent=True)

        queryset = Reimbursement.objects.exclude(search_vector=None)
        self.assertEqual(3, queryset.count())
