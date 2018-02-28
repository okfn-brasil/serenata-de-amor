from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def rename_title(title):
    title = title.replace('modificar', 'visualizar')
    title = title.replace('Modificar', 'Visualizar')
    return title
