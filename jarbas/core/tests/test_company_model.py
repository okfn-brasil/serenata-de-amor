from django.test import TestCase
from jarbas.core.models import Activity, Company
from jarbas.core.tests import sample_activity_data, sample_company_data


class TestCreate(TestCase):

    def setUp(self):
        self.activity = Activity.objects.create(**sample_activity_data)
        self.data = sample_company_data

    def test_create(self):
        self.assertEqual(0, Company.objects.count())
        company = Company.objects.create(**self.data)
        company.main_activity.add(self.activity)
        company.secondary_activity.add(self.activity)
        company.save()
        self.assertEqual(1, Company.objects.count())
        self.assertEqual(1, company.main_activity.count())
        self.assertEqual(1, company.secondary_activity.count())
