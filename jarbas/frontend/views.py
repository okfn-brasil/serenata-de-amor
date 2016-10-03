from django.conf import settings
from django.shortcuts import render


def home(request):
    context = {'google_analytics': settings.GOOGLE_ANALYTICS}
    return render(request, 'frontend/home.html', context=context)
