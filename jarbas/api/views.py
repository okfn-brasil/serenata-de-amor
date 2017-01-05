from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView

from jarbas.api.serializers import (
    ApplicantSerializer,
    ReceiptSerializer,
    ReimbursementSerializer,
    SameDayReimbursementSerializer,
    SubquotaSerializer,
    CompanySerializer,
    format_cnpj
)
from jarbas.core.models import Reimbursement, Company


class MultipleFieldLookupMixin(object):

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
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
            self.queryset = Reimbursement.objects.tuple_filter(**filters)

        # change ordering if needed
        order_by = self.request.query_params.get('order_by')
        if order_by == 'probability':
            kwargs = {
                'select': {'probability_is_null': 'probability IS NULL'},
                'order_by': ['probability_is_null', '-probability']
            }
            self.queryset = self.queryset.extra(**kwargs)

        return super().get(request)


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


class SameDayReimbursementListView(ListAPIView):

    serializer_class = SameDayReimbursementSerializer

    def get_queryset(self):
        return Reimbursement.objects.same_day(**self.kwargs)


class ApplicantListView(ListAPIView):

    serializer_class = ApplicantSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        args = ('applicant_id', 'congressperson_name', query)
        return Reimbursement.objects.list_distinct(*args)


class SubquotaListView(ListAPIView):

    serializer_class = SubquotaSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        args = ('subquota_id', 'subquota_description', query)
        return Reimbursement.objects.list_distinct(*args)


class CompanyDetailView(RetrieveAPIView):

    lookup_field = 'cnpj'
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_object(self):
        cnpj = self.kwargs.get(self.lookup_field, '00000000000000')
        return get_object_or_404(Company, cnpj=format_cnpj(cnpj))
