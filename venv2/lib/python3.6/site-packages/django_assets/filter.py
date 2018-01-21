"""Django specific filters.

For those to be registered automatically, make sure the main
django_assets namespace imports this file.
"""
from django.template import Template, Context

from webassets import six
from webassets.filter import Filter, register_filter


class TemplateFilter(Filter):
    """
    Will compile all source files as Django templates.
    """
    name = 'template'
    max_debug_level = None

    def __init__(self, context=None):
        super(TemplateFilter, self).__init__()
        self.context = context

    def input(self, _in, out, source_path, output_path, **kw):
        t = Template(_in.read(), origin='django-assets', name=source_path)
        rendered = t.render(Context(self.context if self.context else {}))
        out.write(rendered)


register_filter(TemplateFilter)
