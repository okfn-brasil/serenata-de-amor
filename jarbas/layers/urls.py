from django.conf.urls import url

from jarbas.layers.views import home


urlpatterns = [
    url(r'^$', home, name='home')
]
