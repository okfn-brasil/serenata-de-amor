from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from jarbas.dashboard.sites import DashboardSite, dashboard

User = get_user_model()


class TestDashboardSite(TestCase):

    def setUp(self):
        self.site = dashboard

    def test_init(self):
        self.assertEqual({}, dict(self.site.actions))
        self.assertEqual({}, dict(self.site._global_actions))
        self.assertEqual('dashboard', self.site.name)

    @patch.object(User.objects, 'get')
    @patch.object(Permission.objects, 'get')
    @patch.object(ContentType.objects, 'get_for_model')
    def test_get_user_with_existing_user(self, get_for_model, permission_get, user_get):
        User.objects.create_user('dashboard', password='dashboard')
        with patch.object(User.objects, 'create_user') as create_user:
            self.site.get_user()

        user_get.assert_called_once_with(username='dashboard')
        create_user.assert_not_called()
        permission_get.assert_not_called()
        get_for_model.assert_not_called()

    @patch.object(User.objects, 'get', side_effect=(User.DoesNotExist, True))
    @patch.object(User.objects, 'create_user')
    @patch.object(Permission.objects, 'get')
    @patch.object(ContentType.objects, 'get_for_model')
    def test_get_user_without_existing_user(self, get_for_model, permission_get, create_user, user_get):
        self.site.get_user()
        self.assertEqual(2, user_get.call_count)
        self.assertEqual(1, create_user.call_count)
        self.assertEqual(1, permission_get.call_count)
        self.assertEqual(1, get_for_model.call_count)

    def test_valid_url(self):
        valid, invalid = MagicMock(), MagicMock()
        valid.regex.pattern = '/whatever/'
        invalid.regex.pattern = '/whatever/add/'
        self.assertTrue(self.site.valid_url(valid))
        self.assertFalse(self.site.valid_url(invalid))

    @patch.object(DashboardSite, 'get_urls')
    @patch.object(DashboardSite, 'valid_url')
    def test_urls(self, valid_url, get_urls):
        valid_url.side_effect = (True, False, True)
        get_urls.return_value = range(3)
        expected = [0, 2], 'admin', 'dashboard'
        self.assertEqual(expected, self.site.urls)

    def test_has_permission_get(self):
        request = MagicMock()
        request.method = 'GET'
        self.assertTrue(self.site.has_permission(request))
        self.assertIsInstance(request.user, User)

    def test_has_permission_post(self):
        request = MagicMock()
        request.method = 'POST'
        self.assertFalse(self.site.has_permission(request))
        self.assertIsInstance(request.user, MagicMock)

