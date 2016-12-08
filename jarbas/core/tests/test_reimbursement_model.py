from django.db.utils import IntegrityError
from django.test import TestCase
from jarbas.core.models import Reimbursement
from jarbas.core.tests import sample_reimbursement_data


class TestReimbursement(TestCase):

    def setUp(self):
        self.data = sample_reimbursement_data


class TestCreate(TestReimbursement):

    def test_create(self):
        self.assertEqual(0, Reimbursement.objects.count())
        Reimbursement.objects.create(**self.data)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_unique_together(self):
        Reimbursement.objects.create(**self.data)
        with self.assertRaises(IntegrityError):
            Reimbursement.objects.create(**self.data)

    def test_optional_fields(self):
        optional = (
            'total_reimbursement_value',
            'congressperson_id',
            'congressperson_name',
            'congressperson_document',
            'subquota_group_id',
            'subquota_group_description',
            'cnpj_cpf',
            'issue_date',
            'remark_value',
            'installment',
            'reimbursement_values',
            'passenger',
            'leg_of_the_trip',
            'probability',
            'suspicions'
        )
        new_data = {k: v for k, v in self.data.items() if k not in optional}
        Reimbursement.objects.create(**new_data)
        self.assertEqual(1, Reimbursement.objects.count())


class TestCustomMethods(TestReimbursement):

    def test_all_reimbursemenet_values(self):
        Reimbursement.objects.create(**self.data)
        reimbursement = Reimbursement.objects.first()
        self.assertEqual(
            [12.13, 14.15],
            list(reimbursement.all_reimbursement_values)
        )

    def test_all_numbers(self):
        Reimbursement.objects.create(**self.data)
        reimbursement = Reimbursement.objects.first()
        self.assertEqual(
            [10, 11],
            list(reimbursement.all_reimbursement_numbers)
        )

    def test_all_net_values(self):
        Reimbursement.objects.create(**self.data)
        reimbursement = Reimbursement.objects.first()
        self.assertEqual(
            [1.99, 2.99],
            list(reimbursement.all_net_values)
        )
