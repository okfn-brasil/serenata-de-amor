from django.conf import settings
from django.shortcuts import render


def home(request):
    context = {
        'google_street_view_api_key': settings.GOOGLE_STREET_VIEW_API_KEY
    }
    return render(request, 'layers/home.html', context=context)
