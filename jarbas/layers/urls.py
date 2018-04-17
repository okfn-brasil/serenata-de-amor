from django.urls import path

from jarbas.layers.views import home


app_name = 'layers'

urlpatterns = [
    path('', home, name='home')
]
