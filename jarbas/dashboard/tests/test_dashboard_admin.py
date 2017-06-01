from collections import namedtuple
from unittest.mock import MagicMock

from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.dashboard.admin import ReimbursementModelAdmin, SubuotaListfilter


Request = namedtuple('Request', ('method',))
ReimbursementMock = namedtuple('Reimbursement', ('cnpj_cpf'))


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

    def test_format_document(self):
        obj1 = ReimbursementMock('12345678901234')
        obj2 = ReimbursementMock('12345678901')
        obj3 = ReimbursementMock('2345678')
        self.assertEqual('12.345.678/9012-34', self.ma._format_document(obj1))
        self.assertEqual('123.456.789-01', self.ma._format_document(obj2))
        self.assertEqual('2345678', self.ma._format_document(obj3))


class TestSubuotaListfilter(TestCase):

    def setUp(self):
        self.qs = MagicMock()
        self.list_filter = MagicMock()

    def test_queryset_without_subquota(self):
        self.list_filter.value.return_value = None
        SubuotaListfilter.queryset(self.list_filter, MagicMock(), self.qs)
        self.qs.filter.assert_not_called()

    def test_queryset_with_subquota(self):
        self.list_filter.value.return_value = 42
        SubuotaListfilter.queryset(self.list_filter, MagicMock(), self.qs)
        self.qs.filter.assert_called_once_with(subquota_id=42)
