import json

from django.forms.widgets import Widget

from jarbas.dashboard.admin.subquotas import Subquotas


class ReceiptUrlWidget(Widget):

    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            return ''

        url = '<div class="readonly"><a href="{}" target="_blank">{}</a></div>'
        return url.format(value, value)


class SubquotaWidget(Widget, Subquotas):

    def render(self, name, value, attrs=None, renderer=None):
        value = self.pt_br(value) or value
        return '<div class="readonly">{}</div>'.format(value)


class SuspiciousWidget(Widget):

    SUSPICIONS = (
        'meal_price_outlier',
        'over_monthly_subquota_limit',
        'suspicious_traveled_speed_day',
        'invalid_cnpj_cpf',
        'election_expenses',
        'irregular_companies_classifier'
    )

    HUMAN_NAMES = (
        'Preço de refeição muito incomum',
        'Extrapolou limita da (sub)quota',
        'Muitas despesas em diferentes cidades no mesmo dia',
        'CPF ou CNPJ inválidos',
        'Gasto com campanha eleitoral',
        'CNPJ irregular'
    )

    MAP = dict(zip(SUSPICIONS, HUMAN_NAMES))

    def render(self, name, value, attrs=None, renderer=None):
        value_as_dict = json.loads(value)
        if not value_as_dict:
            return ''

        values = (self.MAP.get(k, k) for k in value_as_dict.keys())
        suspicions = '<br>'.join(values)
        return '<div class="readonly">{}</div>'.format(suspicions)
