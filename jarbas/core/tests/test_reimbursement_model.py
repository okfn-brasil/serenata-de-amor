from django.db.utils import IntegrityError
from django.test import TestCase
from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data


class TestCreate(TestCase):

    def setUp(self):
        self.data = sample_reimbursement_data

    def test_create(self):
        self.assertEqual(0, Reimbursement.objects.count())
        Reimbursement.objects.create(**self.data)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_unique_year_applicant_document(self):
        Reimbursement.objects.create(**self.data)
        with self.assertRaises(IntegrityError):
            Reimbursement.objects.create(**self.data)
