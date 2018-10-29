from django.test import TestCase

from jarbas.federal_senate.models import Reimbursement


class TestReimbursement(TestCase):

    def setUp(self):
        self.data = dict(
            document_id='214',
            year=2013,
            month=5,
            date='2013-10-05',
            congressperson_name='MOZARILDO CAVALCANTI',
            expense_type='Publicity of parliamentary activity',
            expense_details='Despesas com divulgação da atividade parlamentar do Senador Mozarildo Cavalcanti',
            supplier='Editora Zenite Ltda.',
            cnpj_cpf='08509060000146',
            reimbursement_value=300,
            probability=0.5,
            suspicions={'invalid_cnpj_cpf': {'is_suspect': True, 'probability': 1.0}},
        )


class TestCreate(TestReimbursement):

    def test_create(self):
        self.assertEqual(0, Reimbursement.objects.count())
        Reimbursement.objects.create(**self.data)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_last_update(self):
        reimbursement = Reimbursement.objects.create(**self.data)
        created_at = reimbursement.last_update
        reimbursement.year = 1971
        reimbursement.save()
        self.assertGreater(reimbursement.last_update, created_at)

    def test_optional_fields(self):
        optional = (
            'document_id',
            'congressperson_name',
            'expense_type',
            'expense_details',
            'cnpj_cpf',
            'reimbursement_value',
            'probability',
            'suspicions'
        )
        new_data = {k: v for k, v in self.data.items() if k not in optional}
        Reimbursement.objects.create(**new_data)
        self.assertEqual(1, Reimbursement.objects.count())
