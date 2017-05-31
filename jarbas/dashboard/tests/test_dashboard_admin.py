from collections import namedtuple
from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.dashboard.admin import ReimbursementModelAdmin


Request = namedtuple('Request', ('method',))


class TestDashboardSite(TestCase):

    def setUp(self):
        self.requests = map(Request, ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'))
        self.ma = ReimbursementModelAdmin(Reimbursement, 'dashboard')

    def test_has_add_permission(self):
        permissions = map(self.ma.has_add_permission, self.requests)
        self.assertNotIn(True, tuple(permissions))

    def test_has_change_permission(self):
        permissions = map(self.ma.has_change_permission, self.requests)
        expected = (True, False, False, False, False)
        self.assertEqual(expected, tuple(permissions))

    def test_has_delete_permission(self):
        permissions = map(self.ma.has_delete_permission, self.requests)
        self.assertNotIn(True, tuple(permissions))
