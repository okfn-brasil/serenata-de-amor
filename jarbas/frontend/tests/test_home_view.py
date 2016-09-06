from django.shortcuts import resolve_url
from django.test import TestCase


class TestGet(TestCase):

    def test_status_code(self):
        resp = self.client.get(resolve_url('home'))
        self.assertEqual(200, resp.status_code)
