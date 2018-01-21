from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from jarbas.public_admin.sites import PublicAdminSite, public_admin

User = get_user_model()


class TestPublicAdminSite(TestCase):

    def setUp(self):
        self.site = public_admin

    def test_init(self):
        self.assertEqual({}, dict(self.site.actions))
        self.assertEqual({}, dict(self.site._global_actions))
        self.assertEqual('dashboard', self.site.name)

    def test_valid_url(self):
        valid, invalid = MagicMock(), MagicMock()
        valid.pattern.regex.pattern = '/whatever/'
        invalid.pattern.regex.pattern = '/whatever/add/'
        self.assertTrue(self.site.valid_url(valid))
        self.assertFalse(self.site.valid_url(invalid))

    @patch.object(PublicAdminSite, 'get_urls')
    @patch.object(PublicAdminSite, 'valid_url')
    def test_urls(self, valid_url, get_urls):
        valid_url.side_effect = (True, False, True)
        get_urls.return_value = range(3)
        expected = [0, 2], 'admin', 'dashboard'
        self.assertEqual(expected, self.site.urls)

    def test_has_permission_get(self):
        request = MagicMock()
        request.method = 'GET'
        self.assertTrue(self.site.has_permission(request))

    def test_has_permission_post(self):
        request = MagicMock()
        request.method = 'POST'
        self.assertFalse(self.site.has_permission(request))
