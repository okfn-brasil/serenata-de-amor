"""
Serenata URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/ref/urls/#django.urls.path
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('home/', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('home/', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('', lambda _: redirect(settings.HOMES_REDIRECTS_TO), name='home'),
    path('dashboard/', include('jarbas.dashboard.urls')),
    path('layers/', include('jarbas.layers.urls', namespace='layers')),
    path('api/', include('jarbas.core.urls', namespace='core')),
    path('api/chamber_of_deputies/',
         include(
             'jarbas.chamber_of_deputies.urls',
             namespace='chamber_of_deputies'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
