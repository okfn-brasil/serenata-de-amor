from collections import namedtuple
from unittest.mock import MagicMock, patch

from django.test import TestCase

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.dashboard.admin import (
    ReceiptUrlWidget,
    ReimbursementModelAdmin,
    SubquotaWidget,
    SubquotaListFilter,
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

    def test_format_document_with_cnpj(self):
        obj = ReimbursementMock('12345678901234')
        self.assertEqual('12.345.678/9012-34', self.ma._format_document(obj))

    def test_format_document_with_cpf(self):
        obj = ReimbursementMock('12345678901')
        self.assertEqual('123.456.789-01', self.ma._format_document(obj))

    def test_format_document_with_unknown(self):
        obj = ReimbursementMock('2345678')
        self.assertEqual('2345678', self.ma._format_document(obj))


class TestSubquotaListFilter(TestCase):

    def setUp(self):
        args = [MagicMock()] * 4  # SubquotaListFilter expectss 4 arguments
        self.list_filter = SubquotaListFilter(*args)
        self.qs = MagicMock()

    @patch.object(SubquotaListFilter, 'value')
    def test_queryset_without_subquota(self, value):
        value.return_value = None
        self.list_filter.queryset(MagicMock(), self.qs)
        self.qs.filter.assert_not_called()

    @patch.object(SubquotaListFilter, 'value')
    def test_queryset_with_subquota(self, value):
        value.return_value = '10'
        self.list_filter.queryset(MagicMock(), self.qs)
        expected = dict(subquota_description='Telecommunication')
        self.qs.filter.assert_called_once_with(**expected)


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
