from django.conf.urls import url

from jarbas.public_admin.sites import public_admin


urlpatterns = [
    url(r'', public_admin.urls)
]
