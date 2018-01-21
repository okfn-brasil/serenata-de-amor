from django.urls import path

from jarbas.core.views import CompanyDetailView


app_name = 'core'

urlpatterns = [
    path(
        'company/<int:cnpj>/',
        CompanyDetailView.as_view(),
        name='company-detail'
    ),
]
