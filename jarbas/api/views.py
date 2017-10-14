from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView

from jarbas.api import serializers
from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.core.models import Company


class ReimbursementListView(ListAPIView):

    queryset = Reimbursement.objects.all()
    serializer_class = serializers.ReimbursementSerializer

    def get(self, request):

        # get filtering parameters from query string
        params = (
            'applicant_id',
            'cnpj_cpf',
            'document_id',
            'issue_date_end',
            'issue_date_start',
            'month',
            'subquota_id',
            'year'
        )
        values = map(self.request.query_params.get, params)
        filters = {k: v for k, v in zip(params, values) if v}

        # filter suspicions
        suspicions = self._bool_param('suspicions')
        if suspicions is not None:
            self.queryset = self.queryset.suspicions(suspicions)

        # filter receipt_url
        receipt_url = self._bool_param('receipt_url')
        if receipt_url is not None:
            self.queryset = self.queryset.has_receipt_url(receipt_url)

        # filter reimbursement in latest dataset
        in_latest = self._bool_param('in_latest_dataset')
        if in_latest is not None:
            self.queryset = self.queryset.in_latest_dataset(in_latest)

        # filter queryset
        if filters:
            self.queryset = self.queryset.tuple_filter(**filters)

        # change ordering if needed
        order_by = self.request.query_params.get('order_by')
        if order_by == 'probability':
            self.queryset = self.queryset.order_by_probability()

        return super().get(request)

    def _bool_param(self, param):
        if param not in self.request.query_params:
            return None

        value = self.request.query_params[param]
        if value.lower() in ('1', 'true'):
            return True

        return False


class ReimbursementDetailView(RetrieveAPIView):

    lookup_field = 'document_id'
    queryset = Reimbursement.objects.all()
    serializer_class = serializers.ReimbursementSerializer


class ReceiptDetailView(RetrieveAPIView):

    lookup_field = 'document_id'
    queryset = Reimbursement.objects.all()
    serializer_class = serializers.ReceiptSerializer

    def get_object(self):
        obj = super().get_object()
        force = 'force' in self.request.query_params
        obj.get_receipt_url(force=force)
        return obj


class SameDayReimbursementListView(ListAPIView):

    serializer_class = serializers.SameDayReimbursementSerializer

    def get_queryset(self):
        return Reimbursement.objects.same_day_as(**self.kwargs)


class ApplicantListView(ListAPIView):

    serializer_class = serializers.ApplicantSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        args = ('applicant_id', 'congressperson_name', query)
        return Reimbursement.objects.list_distinct(*args)


class SubquotaListView(ListAPIView):

    serializer_class = serializers.SubquotaSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        args = ('subquota_id', 'subquota_description', query)
        return Reimbursement.objects.list_distinct(*args)


class CompanyDetailView(RetrieveAPIView):

    lookup_field = 'cnpj'
    queryset = Company.objects.all()
    serializer_class = serializers.CompanySerializer

    def get_object(self):
        cnpj = self.kwargs.get(self.lookup_field, '00000000000000')
        return get_object_or_404(Company, cnpj=serializers.format_cnpj(cnpj))
