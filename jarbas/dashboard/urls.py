from django.conf.urls import url
from jarbas.dashboard.sites import dashboard

urlpatterns = [
    url(r'', dashboard.urls)
]
