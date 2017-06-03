from django.conf import settings


def google_analytics(request):
    return {'google_analytics': settings.GOOGLE_ANALYTICS}
