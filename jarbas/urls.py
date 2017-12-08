"""serenata URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls import include, url


urlpatterns = [
    url(r'^$', lambda _: redirect(settings.HOMES_REDIRECTS_TO), name='home'),
    url(r'^dashboard/', include('jarbas.dashboard.urls')),
    url(r'^layers/', include('jarbas.layers.urls', namespace='layers')),
    url(r'^api/', include('jarbas.core.urls', namespace='core')),
    url(
        r'^api/chamber_of_deputies/',
        include('jarbas.chamber_of_deputies.urls', namespace='chamber_of_deputies')
    )
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
