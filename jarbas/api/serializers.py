from rest_framework import serializers

from jarbas.core.models import Document


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        exclude = ('id', 'source', 'line', 'receipt_url', 'receipt_url_last_update')
