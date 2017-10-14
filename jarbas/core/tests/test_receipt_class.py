from unittest.mock import patch

from django.test import TestCase
from requests.exceptions import ConnectionError

from jarbas.chamber_of_deputies.models import Receipt


class TestReceipt(TestCase):

    def setUp(self):
        self.receipt = Receipt(1970, 13, 42)

    def test_url(self):
        expected = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/13/1970/42.pdf'
        self.assertEqual(expected, self.receipt.url)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 200
        self.assertTrue(self.receipt.exists)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_no_existing_url(self, mocked_head):
        mocked_head.return_value.status_code = 404
        self.assertFalse(self.receipt.exists)

    @patch('jarbas.chamber_of_deputies.models.head')
    def test_connection_error(self, mocked_head):
        mocked_head.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            self.receipt.exists
