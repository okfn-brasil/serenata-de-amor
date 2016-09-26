from rest_framework import serializers

from jarbas.core.models import Activity, Document, Supplier


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        exclude = ('source', 'line')


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
