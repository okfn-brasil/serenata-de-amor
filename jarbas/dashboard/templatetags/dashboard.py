from datetime import datetime
from django import template
from django.template.defaultfilters import stringfilter

from jarbas.dashboard.admin.subquotas import Subquotas


BR_NUMBER_TRANSLATION = str.maketrans(',.', '.,')
register = template.Library()


@register.filter
@stringfilter
def rename_title(title):
    title = title.replace('modificar', 'visualizar')
    title = title.replace('Modificar', 'Visualizar')
    return title


@register.filter()
def percentof(amount, total):
    try:
        return f'{brazilian_float(amount * 100 / total)}%'
    except ZeroDivisionError:
        return None


@register.filter()
def brazilian_reais(value):
    return f'R$ {brazilian_float(value)}'


@register.filter()
def brazilian_float(value):
    value = value or 0
    value = f'{value:,.2f}'
    return value.translate(BR_NUMBER_TRANSLATION)


@register.filter()
def brazilian_integer(value):
    value = value or 0
    value = f'{value:,.0f}'
    return value.translate(BR_NUMBER_TRANSLATION)


@register.filter()
def translate_subquota(value):
    return Subquotas.pt_br(value) or value


@register.filter()
def translate_chart_grouping(value):
    translation = {'month': 'mês', 'year': 'ano'}
    return translation.get(value, value)


@register.filter()
def chart_grouping_as_date(value):
    """Transforms a string YYYYMM or YYYY in a date object"""
    value = str(value)
    for format in ('%Y', '%Y%m'):
        try:
            return datetime.strptime(str(value), format).date()
        except ValueError:
            pass
