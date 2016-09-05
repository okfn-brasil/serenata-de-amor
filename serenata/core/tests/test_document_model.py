from django.test import TestCase
from serenata.core.models import Document


class TestCreate(TestCase):

    def test_create(self):
        self.assertEqual(0, Document.objects.count())
        Document.objects.create(
            document_id=5621548,
            congressperson_name='ADELMO LEÃO',
            congressperson_id=74752,
            congressperson_document=248,
            term=2015,
            state='MG',
            party='PP',
            term_id=55,
            subquota_number=11,
            subquota_description='Postal services',
            subquota_group_id=0,
            subquota_group_description='NaN',
            supplier='Magnino Franquia e Serviços Ltda',
            cnpj_cpf='20574089000107',
            document_number=29022,
            document_type=1,
            issue_date='2015-02-26 00:00:00',
            document_value=190.05,
            remark_value=0,
            net_value=190.05,
            month=2,
            year=2015,
            installment=0,
            passenger='NaN',
            leg_of_the_trip=0,
            batch_number=1172687,
            reimbursement_number=4953,
            reimbursement_value=0,
            applicant_id=705,
        )
        self.assertEqual(1, Document.objects.count())
