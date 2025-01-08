from drf_dynamic_fields import DynamicFieldsMixin
from mapentity.serializers import MapentityGeojsonModelSerializer
from rest_framework import serializers as rest_serializers

from . import models as sensitivity_models


class SensitiveAreaSerializer(DynamicFieldsMixin, rest_serializers.ModelSerializer):
    category = rest_serializers.CharField(source='category_display')
    structure = rest_serializers.SlugRelatedField('name', read_only=True)
    species = rest_serializers.CharField(source='species.name')
    name = rest_serializers.CharField(source='name_display')

    class Meta:
        model = sensitivity_models.SensitiveArea
        fields = "__all__"


class SensitiveAreaGeojsonSerializer(MapentityGeojsonModelSerializer):
    radius = rest_serializers.IntegerField()

    class Meta(MapentityGeojsonModelSerializer.Meta):
        model = sensitivity_models.SensitiveArea
        fields = ['id', 'species', 'radius', 'published']
