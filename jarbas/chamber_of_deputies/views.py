from rest_framework.generics import ListAPIView, RetrieveAPIView

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.chamber_of_deputies.serializers import (ReimbursementSerializer,
                                                    ReceiptSerializer,
                                                    SameDayReimbursementSerializer,
                                                    ApplicantSerializer,
                                                    SubquotaSerializer)

from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchVector


class ReimbursementListView(ListAPIView):

    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer

    def get(self, request):

        self._build_filters()

        self._build_vector_filters()

        self._build_order_by()

        return super().get(request)

    def _bool_param(self, param):
        if param not in self.request.query_params:
            return None

        value = self.request.query_params[param]
        if value.lower() in ('1', 'true'):
            return True

        return False

    def _build_order_by(self):
        """ Change ordering if needed """

        order_by = self.request.query_params.get('order_by')
        if order_by == 'probability':
            self.queryset = self.queryset.order_by_probability()

    def _build_filters(self):
        """ 
            Builder and aplly all filters on QuerySet
        """

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

    def _build_vector_filters(self):
        """ 
            Builder and aplly all vector filters on QuerySet 
        """

        # get vector parameters from query string
        vector_params = (
            'congressperson_name',
        )
        vector_values = map(self.request.query_params.get, vector_params)
        vector_filters = {k: v for k, v in zip(vector_params, vector_values) if v}

        # filter search_vector
        for vector in vector_filters:
            self.queryset = self.queryset.annotate(search=SearchVector(vector)).filter(search=vector_filters[vector])


class ReimbursementDetailView(RetrieveAPIView):

    lookup_field = 'document_id'
    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer


class ReceiptDetailView(RetrieveAPIView):

    lookup_field = 'document_id'
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
        return Reimbursement.objects.same_day_as(**self.kwargs)


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
