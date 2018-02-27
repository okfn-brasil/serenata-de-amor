from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase


class TestHome(TestCase):

    def test_redirects(self):
        resp = self.client.get('/')
        self.assertRedirects(resp, settings.HOMES_REDIRECTS_TO)
