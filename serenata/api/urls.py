from django.conf.urls import url

from serenata.api.views import document

urlpatterns = [
    url(r'^document/(?P<document_id>\d+)/$', document, name='document'),
]
