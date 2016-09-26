
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from jarbas.api.serializers import DocumentSerializer, SupplierSerializer
from jarbas.core.models import Document, Supplier


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


class SupplierViewSet(ViewSet):

    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()

    def retrieve(self, request, pk=None):
        cnpj = str(pk).zfill(14)
        formatted = '{}.{}.{}/{}-{}'.format(
            cnpj[0:2],
            cnpj[2:5],
            cnpj[5:8],
            cnpj[8:12],
            cnpj[12:14]
        )
        supplier = get_object_or_404(Supplier, cnpj=formatted)
        serializer = SupplierSerializer(supplier)
        return Response(serializer.data)
