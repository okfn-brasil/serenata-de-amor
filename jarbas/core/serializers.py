from rest_framework import serializers

from jarbas.core.models import Activity, Company


class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = ('code', 'description')


class CompanySerializer(serializers.ModelSerializer):

    main_activity = ActivitySerializer(many=True, read_only=True)
    secondary_activity = ActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Company
        exclude = ('id',)
        depth = 1
