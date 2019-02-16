from django import template
from django.template.defaultfilters import stringfilter

from jarbas.dashboard.admin.subquotas import Subquotas


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
    # TODO properly use locales
    value = value or 0
    value = f'{value:,.2f}'
    return value.replace(',', 'x').replace('.', ',').replace('x', '.')


@register.filter()
def brazilian_integer(value):
    # TODO properly use locales
    value = value or 0
    value = f'{value:,.0f}'
    return value.replace(',', '.')


@register.filter()
def translate_subquota(value):
    return Subquotas.pt_br(value) or value


@register.filter()
def translate_period(value):
    translation = {
        'day': 'dia',
        'month': 'mês',
        'year': 'ano'
    }
    return translation.get(value, value)
