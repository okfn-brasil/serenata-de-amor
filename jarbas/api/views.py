from rest_framework.viewsets import ReadOnlyModelViewSet

from jarbas.api.serializers import DocumentSerializer
from jarbas.core.models import Document


class DocumentViewSet(ReadOnlyModelViewSet):

    serializer_class = DocumentSerializer

    def get_queryset(self):

        # look up for filters in the query parameters
        params = list(
            field.name for field in DocumentSerializer.Meta.model._meta.fields
            if field.name not in DocumentSerializer.Meta.exclude
        )
        values = map(self.request.query_params.get, params)
        filters = {k: v for k, v in zip(params, values) if v is not None}

        # build queryset
        queryset = Document.objects.all()
        if filters:
            queryset = queryset.filter(**filters)

        return queryset
