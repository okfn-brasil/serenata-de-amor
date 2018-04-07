from django.urls import re_path

from jarbas.core.views import CompanyDetailView


app_name = 'core'

urlpatterns = [
    re_path(
        r'^company/(?P<cnpj>\d{14})/$',
        CompanyDetailView.as_view(),
        name='company-detail'
    ),
]
