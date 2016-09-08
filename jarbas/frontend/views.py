from django.shortcuts import render

from jarbas.core.models import Document


def home(request):
    return render(request, 'frontend/home.html',
                  context=dict(count=Document.objects.count()))
