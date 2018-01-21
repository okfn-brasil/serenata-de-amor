import django.template

from newrelic.hooks.framework_django import (
        newrelic_browser_timing_header, newrelic_browser_timing_footer)

register = django.template.Library()

register.simple_tag(newrelic_browser_timing_header)
register.simple_tag(newrelic_browser_timing_footer)
