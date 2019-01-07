from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase


class TestHealthCheck(TestCase):

    def test_status(self):
        resp = self.client.get(resolve_url('healthcheck'))
        self.assertEqual(200, resp.status_code)
