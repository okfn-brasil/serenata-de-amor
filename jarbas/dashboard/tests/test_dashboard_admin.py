from collections import namedtuple
from unittest.mock import MagicMock

from django.test import TestCase

from jarbas.core.models import Reimbursement
from jarbas.dashboard.admin import (
    ReceiptUrlWidget,
    ReimbursementModelAdmin,
    SubquotaWidget,
    SubuotaListfilter,
    SuspiciousWidget,
)


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


class TestCustomWidgets(TestCase):

    def test_subquota_widget(self):
        widget = SubquotaWidget()
        rendered = widget.render('Name', 'Flight ticket issue')
        self.assertIn('Emissão bilhete aéreo', rendered)

    def test_suspicious_widget_with_one_suspicion(self):
        widget = SuspiciousWidget()
        json_value = '{"invalid_cnpj_cpf": true}'
        rendered = widget.render('Name', json_value)
        self.assertIn('CPF ou CNPJ inválidos', rendered)
        self.assertNotIn('<br>', rendered)

    def test_suspicious_widget_with_two_suspicions(self):
        widget = SuspiciousWidget()
        json_value = '{"invalid_cnpj_cpf": true, "election_expenses": true}'
        rendered = widget.render('Name', json_value)
        self.assertIn('CPF ou CNPJ inválidos', rendered)
        self.assertIn('<br>', rendered)
        self.assertIn('Gasto com campanha eleitoral', rendered)

    def test_suspicious_widget_with_new_suspicion(self):
        widget = SuspiciousWidget()
        json_value = '{"whatever": true, "invalid_cnpj_cpf": true}'
        rendered = widget.render('Name', json_value)
        self.assertIn('CPF ou CNPJ inválidos', rendered)
        self.assertIn('<br>', rendered)
        self.assertIn('whatever', rendered)

    def test_suspicious_widget_without_suspicion(self):
        widget = SuspiciousWidget()
        json_value = 'null'
        rendered = widget.render('Name', json_value)
        self.assertEqual('', rendered)

    def test_receipt_url_widget(self):
        widget = ReceiptUrlWidget()
        url = 'https://jarbas.serenatadeamor.org'
        rendered = widget.render('Name', url)
        self.assertIn('href="{}"'.format(url), rendered)
        self.assertIn('>{}</a>'.format(url), rendered)

    def test_receipt_url_widget_without_url(self):
        widget = ReceiptUrlWidget()
        rendered = widget.render('Name', '')
        self.assertEqual('', rendered)
