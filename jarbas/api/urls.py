from django.conf.urls import url

from jarbas.api.views import document, home

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^document/(?P<document_id>\d+)/$', document, name='document'),
]
