from django.shortcuts import resolve_url
from django.test import TestCase


class TestAdminGet(TestCase):

    def test_status_code(self):
        resp = self.client.get(resolve_url('admin:index'), follow=True)
        self.assertEqual(200, resp.status_code)
