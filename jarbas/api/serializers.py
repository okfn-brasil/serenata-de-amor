from rest_framework import serializers

from jarbas.core.models import Activity, Document, Supplier


class DocumentSerializer(serializers.ModelSerializer):

    receipt = serializers.SerializerMethodField()

    def get_receipt(self, obj):
        return dict(url=obj.receipt_url, fetched=obj.receipt_fetched)

    class Meta:
        model = Document
        exclude = ('source', 'line', 'receipt_url', 'receipt_fetched')


class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = ('code', 'description')


class SupplierSerializer(serializers.ModelSerializer):

    main_activity = ActivitySerializer(many=True, read_only=True)
    secondary_activity = ActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        exclude = ('id',)
        depth = 1
