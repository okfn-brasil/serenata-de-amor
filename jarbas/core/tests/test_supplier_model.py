from django.test import TestCase
from jarbas.core.models import Activity, Supplier
from jarbas.core.tests import sample_activity_data, sample_supplier_data


class TestCreate(TestCase):

    def setUp(self):
        self.activity = Activity.objects.create(**sample_activity_data)
        self.data = sample_supplier_data

    def test_create(self):
        self.assertEqual(0, Supplier.objects.count())
        supplier = Supplier.objects.create(**self.data)
        supplier.main_activity.add(self.activity)
        supplier.secondary_activity.add(self.activity)
        supplier.save()
        self.assertEqual(1, Supplier.objects.count())
        self.assertEqual(1, supplier.main_activity.count())
        self.assertEqual(1, supplier.secondary_activity.count())
