from django.urls import path

from jarbas.dashboard.admin import public_admin


urlpatterns = [
    path('', public_admin.urls)
]
