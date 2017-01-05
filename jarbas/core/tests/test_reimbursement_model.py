from unittest.mock import patch

from django.db.utils import IntegrityError
from django.test import TestCase
from requests.exceptions import ConnectionError

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


class TestManager(TestReimbursement):

    def test_same_day(self):
        data1 = sample_reimbursement_data.copy()
        data1['document_id'] = 42 * 2
        data1['issue_date'] = '1970-12-31'
        Reimbursement.objects.create(**data1)

        data2 = sample_reimbursement_data.copy()
        data2['document_id'] = 42 * 3
        data2['issue_date'] = '1970-12-31'
        Reimbursement.objects.create(**data2)

        data3 = sample_reimbursement_data.copy()
        data3['document_id'] = 42 * 4
        data3['issue_date'] = '1970-12-31'
        Reimbursement.objects.create(**data3)

        unique_id = dict(
            year=1970,
            applicant_id=13,
            document_id=84
        )
        qs = Reimbursement.objects.same_day(**unique_id)
        self.assertEqual(2, qs.count())

    def test_same_day_error(self):
        with self.assertRaises(TypeError):
            Reimbursement.objects.same_day(year=2016, document_id=42)


class TestCustomMethods(TestReimbursement):

    def test_as_list(self):
        self.assertIsNone(Reimbursement.as_list(''))
        self.assertEqual(['1', '2'], Reimbursement.as_list('1,2'))
        self.assertEqual([1, 2], Reimbursement.as_list('1,2', int))

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

    def test_repr(self):
        obj = Reimbursement.objects.create(**self.data)
        expected = (
            'Reimbursement('
            'year=1970, '
            'applicant_id=13, '
            'document_id=42)'
        )
        self.assertEqual(expected, obj.__repr__())


class TestReceipt(TestCase):

    def setUp(self):
        self.obj = Reimbursement.objects.create(**sample_reimbursement_data)
        self.expected_receipt_url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/13/1970/42.pdf'

    def test_url_is_none(self):
        self.assertIsNone(self.obj.receipt_url)
        self.assertFalse(self.obj.receipt_fetched)

    @patch('jarbas.core.models.head')
    def test_get_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        self.assertEqual(self.expected_receipt_url, self.obj.get_receipt_url())
        self.assertEqual(self.expected_receipt_url, self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_called_once_with(self.expected_receipt_url)

    @patch('jarbas.core.models.head')
    def test_get_non_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 404
        self.assertIsNone(self.obj.get_receipt_url())
        self.assertIsNone(self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_called_once_with(self.expected_receipt_url)

    @patch('jarbas.core.models.head')
    def test_get_non_existing_url_with_error(self, mocked_head):
        mocked_head.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            self.obj.get_receipt_url()

    @patch('jarbas.core.models.head')
    def test_get_fetched_existing_url(self, mocked_head):
        self.obj.receipt_fetched = True
        self.obj.receipt_url = '42'
        self.obj.save()
        self.assertEqual('42', self.obj.get_receipt_url())
        self.assertEqual('42', self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_not_called()

    @patch('jarbas.core.models.head')
    def test_get_fetched_non_existing_url(self, mocked_head):
        self.obj.receipt_fetched = True
        self.obj.receipt_url = None
        self.obj.save()
        self.assertIsNone(self.obj.get_receipt_url())
        self.assertIsNone(self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_not_called()

    @patch('jarbas.core.models.head')
    def test_force_get_receipt_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        self.obj.receipt_fetched = True
        self.obj.receipt_url = None
        self.obj.save()
        self.assertEqual(
            self.expected_receipt_url,
            self.obj.get_receipt_url(force=True)
        )
        self.assertEqual(self.expected_receipt_url, self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_called_once_with(self.expected_receipt_url)

    @patch('jarbas.core.models.head')
    def test_bulk_get_receipt_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        updated = self.obj.get_receipt_url(bulk=True)
        self.assertIsInstance(updated, Reimbursement)
        self.assertIsInstance(updated.receipt_url, str)
        self.assertTrue(updated.receipt_fetched)
