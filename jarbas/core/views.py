from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView

from jarbas.core.models import Company
from jarbas.core.serializers import CompanySerializer
from jarbas.chamber_of_deputies.serializers import format_cnpj


class CompanyDetailView(RetrieveAPIView):

    lookup_field = 'cnpj'
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_object(self):
        cnpj = self.kwargs.get(self.lookup_field, '00000000000000')
        return get_object_or_404(Company, cnpj=format_cnpj(cnpj))


def healthcheck(request):
    """A simple view to run a health check in Django and in the database"""
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    return HttpResponse()
