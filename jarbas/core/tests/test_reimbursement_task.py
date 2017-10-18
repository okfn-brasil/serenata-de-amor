from django.forms.models import model_to_dict
from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.core.models import Reimbursement
from jarbas.core.tasks import create_or_update_reimbursement


class TestCreateOrUpdateTask(TestCase):

    def test_create(self):
        with mixer.ctx(commit=False):
            obj = mixer.blend(Reimbursement, search_vector=None)
            fixture = model_to_dict(obj)

        self.assertEqual(0, Reimbursement.objects.count())
        create_or_update_reimbursement(fixture)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_update(self):
        self.assertEqual(0, Reimbursement.objects.count())

        fixture = model_to_dict(mixer.blend(Reimbursement, search_vector=None))
        self.assertEqual(1, Reimbursement.objects.count())

        create_or_update_reimbursement(fixture)
        self.assertEqual(1, Reimbursement.objects.count())
