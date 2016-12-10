from django.core.cache import cache
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings


class TestGet(TestCase):

    def setUp(self):
        self.resp = self.client.get(resolve_url('home'))

    def test_status_code(self):
        self.assertEqual(200, self.resp.status_code)

    def test_template(self):
        cache.clear()
        resp = self.client.get(resolve_url('home'))
        self.assertTemplateUsed(resp, 'frontend/home.html')

    def test_contents(self):
        expected = '<title>Jarbas | Serenata de Amor</title>'
        self.assertIn(expected, self.resp.content.decode('utf-8'))

    @override_settings(GOOGLE_STREET_VIEW_API_KEY=42)
    def test_google_api_key(self):
        cache.clear()
        resp = self.client.get(resolve_url('home'))
        expected = "googleStreetViewApiKey: '42'"
        self.assertIn(expected, resp.content.decode('utf-8'))
