from rest_framework import serializers

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.core.models import Company


class ReimbursementSerializer(serializers.ModelSerializer):

    all_net_values = serializers.SerializerMethodField()
    all_reimbursement_numbers = serializers.SerializerMethodField()
    all_reimbursement_values = serializers.SerializerMethodField()
    document_value = serializers.SerializerMethodField()
    probability = serializers.SerializerMethodField()
    receipt = serializers.SerializerMethodField()
    rosies_tweet = serializers.SerializerMethodField()
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
        return to_float(obj.document_value)

    def get_probability(self, obj):
        return to_float(obj.probability)

    def get_receipt(self, obj):
        return dict(fetched=obj.receipt_fetched, url=obj.receipt_url)

    def get_rosies_tweet(self, obj):
        try:
            return obj.tweet.get_url()
        except Reimbursement.tweet.RelatedObjectDoesNotExist:
            return None

    def get_remark_value(self, obj):
        return to_float(obj.remark_value)

    def get_total_net_value(self, obj):
        return to_float(obj.total_net_value)

    def get_total_reimbursement_value(self, obj):
        return to_float(obj.total_reimbursement_value)

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


class SameDayReimbursementSerializer(serializers.ModelSerializer):

    city = serializers.SerializerMethodField()
    total_net_value = serializers.SerializerMethodField()

    def get_city(self, obj):
        try:
            company = Company.objects.get(cnpj=format_cnpj(obj.cnpj_cpf))
        except Company.DoesNotExist:
            return None

        location = company.city, company.state
        if not any(location):
            return None

        return ', '.join(v for v in location if v)

    def get_total_net_value(self, obj):
        return to_float(obj.total_net_value)

    class Meta:
        model = Reimbursement
        fields = (
            'applicant_id',
            'city',
            'document_id',
            'subquota_id',
            'subquota_description',
            'supplier',
            'total_net_value',
            'year'
        )


class ReceiptSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.receipt_url

    class Meta:
        model = Reimbursement
        fields = ('url',)


class ApplicantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reimbursement
        fields = ('applicant_id', 'congressperson_name')


class SubquotaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reimbursement
        fields = ('subquota_id', 'subquota_description')


def to_float(number):
    try:
        return float(number)
    except TypeError:
        return None


def format_cnpj(cnpj):
    return '{}.{}.{}/{}-{}'.format(
        cnpj[0:2],
        cnpj[2:5],
        cnpj[5:8],
        cnpj[8:12],
        cnpj[12:14]
    )
