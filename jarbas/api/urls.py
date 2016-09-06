from django.conf.urls import url

from jarbas.api.views import document

urlpatterns = [
    url(r'^document/(?P<document_id>\d+)/$', document, name='document'),
]
