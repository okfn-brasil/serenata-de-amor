from django.conf import settings
from django.shortcuts import render


def home(request):
    context = {
        'google_analytics': settings.GOOGLE_ANALYTICS,
        'google_street_view_api_key': settings.GOOGLE_STREET_VIEW_API_KEY
    }
    return render(request, 'frontend/home.html', context=context)
