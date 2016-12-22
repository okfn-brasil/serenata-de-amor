import re
from collections import namedtuple
from functools import reduce

from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveAPIView

from jarbas.api.serializers import (
    ApplicantSerializer,
    ReceiptSerializer,
    ReimbursementSerializer,
    SubquotaSerializer,
    CompanySerializer
)
from jarbas.core.models import Reimbursement, Company


Pair = namedtuple('Pair', ('key', 'values'))


def get_distinct(field, order_by, query=None):
    qs = Reimbursement.objects.all()
    if query:
        filter = {order_by + '__icontains': query}
        qs = qs.filter(**filter)
    return qs.values(field, order_by).order_by(order_by) .distinct()


class MultipleFieldLookupMixin(object):

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {k: self.kwargs[k] for k in self.lookup_fields}
        return get_object_or_404(queryset, **filter)


class ReimbursementListView(ListAPIView):

    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer

    def get(self, request, year=None, applicant_id=None):

        # get filtering parameters from query string
        params = (
            'applicant_id',
            'cnpj_cpf',
            'document_id',
            'month',
            'subquota_id',
            'year'
        )
        values = map(self.request.query_params.get, params)
        filters = {k: v for k, v in zip(params, values) if v is not None}

        # select year and applicant ID from the URL path (not query string)
        if year:
            filters['year'] = year
        if applicant_id:
            filters['applicant_id'] = applicant_id

        # filter queryset
        if filters:
            self.queryset = self.queryset.filter(self.big_q(filters))

        # change ordering if needed
        order_by = self.request.query_params.get('order_by')
        if order_by == 'probability':
            kwargs = {
                'select': {'probability_is_null': 'probability IS NULL'},
                'order_by': ['probability_is_null', '-probability']
            }
            self.queryset = self.queryset.extra(**kwargs)

        return super().get(request)

    def big_q(self, filters):
        """
        Gets filters (dict) and returns a sequence of Q objects with the AND
        operator.
        """
        regex = re.compile('[ ,]+')
        as_pairs = (Pair(k, regex.split(v)) for k, v in filters.items())
        as_q = map(self.big_q_or, as_pairs)
        return reduce(lambda q, new_q: q & (new_q), as_q, Q())

    @staticmethod
    def big_q_or(query):
        """
        Gets a Pair with a key and an iterable as values and returns a Q object
        with the OR operator.
        """
        pairs = ({query.key: v} for v in query.values)
        return reduce(lambda q, new_q: q | Q(**new_q), pairs, Q())


class ReimbursementDetailView(MultipleFieldLookupMixin, RetrieveAPIView):

    lookup_fields = ('year', 'applicant_id', 'document_id')
    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer


class ReceiptDetailView(MultipleFieldLookupMixin, RetrieveAPIView):

    lookup_fields = ('year', 'applicant_id', 'document_id')
    queryset = Reimbursement.objects.all()
    serializer_class = ReceiptSerializer

    def get_object(self):
        obj = super().get_object()
        force = 'force' in self.request.query_params
        obj.get_receipt_url(force=force)
        return obj


class ApplicantListView(ListAPIView):

    serializer_class = ApplicantSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        return get_distinct('applicant_id', 'congressperson_name', query)


class SubquotaListView(ListAPIView):

    serializer_class = SubquotaSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        return get_distinct('subquota_id', 'subquota_description', query)


class CompanyDetailView(RetrieveAPIView):

    lookup_field = 'cnpj'
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_object(self):
        cnpj = self.kwargs.get(self.lookup_field, '00000000000000')
        formatted = '{}.{}.{}/{}-{}'.format(
            cnpj[0:2],
            cnpj[2:5],
            cnpj[5:8],
            cnpj[8:12],
            cnpj[12:14]
        )
        return get_object_or_404(Company, cnpj=formatted)
