from django.test import TestCase
from jarbas.core.models import Document, Receipt
from jarbas.core.tests import sample_document_data


class TestCreate(TestCase):

    def test_create(self):
        self.assertEqual(0, Receipt.objects.count())
        document = Document.objects.create(**sample_document_data)
        Receipt.objects.create(
            url='http://jarbas.datasciencebr.com',
            fetched=True,
            document=document
        )
        first = Document.objects.first()
        self.assertEqual('http://jarbas.datasciencebr.com', first.receipt.url)
