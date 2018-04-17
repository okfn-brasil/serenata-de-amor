from django.urls import path

from jarbas.public_admin.sites import public_admin


urlpatterns = [
    path('', public_admin.urls)
]
