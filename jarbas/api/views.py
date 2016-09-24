
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from jarbas.api.serializers import DocumentSerializer
from jarbas.core.models import Document


class DocumentViewSet(ReadOnlyModelViewSet):

    serializer_class = DocumentSerializer

    def get_queryset(self):

        # look up for filters in the query parameters
        params = (
            'applicant_id',
            'cnpj_cpf',
            'congressperson_id',
            'document_id',
            'document_type',
            'month',
            'party',
            'reimbursement_number',
            'state',
            'subquota_group_id',
            'subquota_number',
            'term',
            'year',
        )
        values = map(self.request.query_params.get, params)
        filters = {k: v for k, v in zip(params, values) if v is not None}

        # build queryset
        queryset = Document.objects.all()
        if filters:
            queryset = queryset.filter(**filters)

        return queryset


class ReceiptViewSet(ViewSet):

    queryset = Document.objects.all()

    def retrieve(self, request, pk=None):
        document = get_object_or_404(Document, pk=pk)
        return Response({'url': document.fetch_receipt()})
