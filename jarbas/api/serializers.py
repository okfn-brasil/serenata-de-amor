from rest_framework import serializers

from jarbas.core.models import Activity, Document, Receipt, Reimbursement, Supplier


class ReimbursementSerializer(serializers.ModelSerializer):

    all_net_values = serializers.SerializerMethodField()
    all_reimbursement_numbers = serializers.SerializerMethodField()
    all_reimbursement_values = serializers.SerializerMethodField()
    document_value = serializers.SerializerMethodField()
    probability = serializers.SerializerMethodField()
    receipt = serializers.SerializerMethodField()
    remark_value = serializers.SerializerMethodField()
    total_net_value = serializers.SerializerMethodField()
    total_reimbursement_value = serializers.SerializerMethodField()

    def get_all_net_values(self, obj):
        return obj.all_net_values

    def get_all_reimbursement_numbers(self, obj):
        return obj.all_reimbursement_numbers

    def get_all_reimbursement_values(self, obj):
        return obj.all_reimbursement_values

    def get_document_value(self, obj):
        return self.to_float(obj.document_value)

    def get_probability(self, obj):
        return self.to_float(obj.probability)

    def get_receipt(self, obj):
        return dict(fecthed=obj.receipt_fetched, url=obj.receipt_url)

    def get_remark_value(self, obj):
        return self.to_float(obj.remark_value)

    def get_total_net_value(self, obj):
        return self.to_float(obj.total_net_value)

    def get_total_reimbursement_value(self, obj):
        return self.to_float(obj.total_reimbursement_value)

    @staticmethod
    def to_float(number):
        try:
            return float(number)
        except TypeError:
            return None

    class Meta:
        model = Reimbursement
        exclude = (
            'id',
            'net_values',
            'receipt_fetched',
            'receipt_url',
            'reimbursement_numbers',
            'reimbursement_values'
        )


class NewReceiptSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.receipt_url

    class Meta:
        model = Reimbursement
        fields = (
            'applicant_id',
            'document_id',
            'url',
            'year'
        )


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
