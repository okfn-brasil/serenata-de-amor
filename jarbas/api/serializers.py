from rest_framework import serializers

from jarbas.core.models import Activity, Document, Receipt, Reimbursement, Supplier


class ReimbursementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reimbursement
        exclude = ('id',)


class ReceiptSerializer(serializers.ModelSerializer):

    class Meta:
        model = Receipt
        fields = ('url', 'fetched')


class DocumentSerializer(serializers.ModelSerializer):

    receipt = serializers.SerializerMethodField()

    def get_receipt(self, obj):
        receipt, created = Receipt.objects.get_or_create(
            document=obj,
            defaults=dict(document=obj)
        )
        return ReceiptSerializer(receipt).data

    class Meta:
        model = Document
        exclude = ()


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
