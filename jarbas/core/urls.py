from django.conf.urls import url

from jarbas.core.views import CompanyDetailView


urlpatterns = [
    url(
        r'^company/(?P<cnpj>\d{14})/$',
        CompanyDetailView.as_view(),
        name='company-detail'
    ),
]
