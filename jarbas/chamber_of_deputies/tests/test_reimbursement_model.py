from unittest.mock import patch

from django.db.utils import IntegrityError
from django.test import TestCase
from requests.exceptions import ConnectionError

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.chamber_of_deputies.tests import sample_reimbursement_data


class TestReimbursement(TestCase):

    def setUp(self):
        self.data = sample_reimbursement_data


class TestCreate(TestReimbursement):

    def test_create(self):
        self.assertEqual(0, Reimbursement.objects.count())
        Reimbursement.objects.create(**self.data)
        self.assertEqual(1, Reimbursement.objects.count())

    def test_unique_document_id(self):
        Reimbursement.objects.create(**self.data)
        with self.assertRaises(IntegrityError):
            Reimbursement.objects.create(**self.data)

    def test_last_update(self):
        reimbursement = Reimbursement.objects.create(**self.data)
        created_at = reimbursement.last_update
        reimbursement.year = 1971
        reimbursement.save()
        self.assertGreater(reimbursement.last_update, created_at)

    def test_default_available_in_latest_dataset(self):
        reimbursement = Reimbursement.objects.create(**self.data)
        self.assertTrue(reimbursement.available_in_latest_dataset)

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

        qs = Reimbursement.objects.same_day_as(84)
        self.assertEqual(2, qs.count())

    def test_suspicions(self):
        data = self.data.copy()
        data['document_id'] = 42 * 2
        del data['suspicions']
        del data['probability']
        Reimbursement.objects.create(**self.data)
        Reimbursement.objects.create(**data)
        self.assertEqual(1, Reimbursement.objects.suspicions(True).count())

    def test_not_suspicions(self):
        data = self.data.copy()
        data['document_id'] = 42 * 2
        del data['suspicions']
        del data['probability']
        Reimbursement.objects.create(**self.data)
        Reimbursement.objects.create(**data)
        self.assertEqual(1, Reimbursement.objects.suspicions(False).count())

    def test_suspicions_filter(self):
        data = self.data.copy()
        data['document_id'] = 42 * 2
        del data['suspicions']
        del data['probability']
        Reimbursement.objects.create(**self.data)
        Reimbursement.objects.create(**data)
        suspects = Reimbursement.objects.suspicions(True)
        not_suspects = Reimbursement.objects.suspicions(False)
        intersection = suspects & not_suspects
        self.assertEqual(0, intersection.count())

    def test_has_receipt_url(self):
        # let's create a reimbursement with some receipt_url (self.data has none)
        data = self.data.copy()
        data['document_id'] = 42 * 2
        data['receipt_url'] = 'http://serenatadeamor.org/'

        # now let's save two reimbursements: one with and another one without receipt_url
        Reimbursement.objects.create(**data)
        Reimbursement.objects.create(**self.data)

        self.assertEqual(1, Reimbursement.objects.has_receipt_url(True).count())

    def test_has_no_receipt_url(self):
        # let's create a reimbursement with some receipt_url (self.data has none)
        data = self.data.copy()
        data['document_id'] = 42 * 2
        data['receipt_url'] = None

        # now let's save two reimbursements: one with and another one without receipt_url
        Reimbursement.objects.create(**data)

        self.assertEqual(1, Reimbursement.objects.has_receipt_url(False).count())

    def test_in_latest_dataset(self):
        data = self.data.copy()
        data['document_id'] = 42 * 2
        data['available_in_latest_dataset'] = False
        Reimbursement.objects.create(**data)
        Reimbursement.objects.create(**self.data)
        deleted = Reimbursement.objects.in_latest_dataset(False)
        self.assertEqual(1, deleted.count())

    def test_not_in_latest_dataset(self):
        data = self.data.copy()
        data['document_id'] = 42 * 2
        data['available_in_latest_dataset'] = False
        Reimbursement.objects.create(**data)
        Reimbursement.objects.create(**self.data)
        existing = Reimbursement.objects.in_latest_dataset(True)
        self.assertEqual(1, existing.count())

    def test_was_ordered(self):
        self.assertFalse(Reimbursement.objects.was_ordered())
        self.assertTrue(Reimbursement.objects.order_by('pk').was_ordered())


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
        expected = 'Reimbursement(document_id=42)'
        self.assertEqual(expected, obj.__repr__())

    def test_str(self):
        obj = Reimbursement.objects.create(**self.data)
        expected = 'Documento nº 42'
        self.assertEqual(expected, str(obj))


class TestReceipt(TestCase):

    def setUp(self):
        self.obj = Reimbursement.objects.create(**sample_reimbursement_data)
        self.expected_receipt_url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/13/1970/42.pdf'

    def test_url_is_none(self):
        self.assertIsNone(self.obj.receipt_url)
        self.assertFalse(self.obj.receipt_fetched)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_get_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        self.assertEqual(self.expected_receipt_url, self.obj.get_receipt_url())
        self.assertEqual(self.expected_receipt_url, self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_called_once_with(self.expected_receipt_url)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_get_non_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 404
        self.assertIsNone(self.obj.get_receipt_url())
        self.assertIsNone(self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_called_once_with(self.expected_receipt_url)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_get_non_existing_url_with_error(self, mocked_head):
        mocked_head.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            self.obj.get_receipt_url()

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_get_fetched_existing_url(self, mocked_head):
        self.obj.receipt_fetched = True
        self.obj.receipt_url = '42'
        self.obj.save()
        self.assertEqual('42', self.obj.get_receipt_url())
        self.assertEqual('42', self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_not_called()

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_get_fetched_non_existing_url(self, mocked_head):
        self.obj.receipt_fetched = True
        self.obj.receipt_url = None
        self.obj.save()
        self.assertIsNone(self.obj.get_receipt_url())
        self.assertIsNone(self.obj.receipt_url)
        self.assertTrue(self.obj.receipt_fetched)
        mocked_head.assert_not_called()

    @patch('jarbas.chamber_of_deputies.models.head')
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

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_bulk_get_receipt_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        updated = self.obj.get_receipt_url(bulk=True)
        self.assertIsInstance(updated, Reimbursement)
        self.assertIsInstance(updated.receipt_url, str)
        self.assertTrue(updated.receipt_fetched)
