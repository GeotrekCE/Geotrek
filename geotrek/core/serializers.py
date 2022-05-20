from drf_dynamic_fields import DynamicFieldsMixin
from mapentity.serializers import MapentityGeojsonModelSerializer
from rest_framework import serializers

from geotrek.core.models import Path, Trail


class PathSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    checkbox = serializers.CharField(source='checkbox_display')
    length_2d = serializers.SerializerMethodField()
    length = serializers.FloatField(source='length_display')
    name = serializers.CharField(source='name_display')
    usages = serializers.CharField(source='usages_display')
    networks = serializers.CharField(source='networks_display')
    trails = serializers.CharField(source='trails_display')
    structure = serializers.SlugRelatedField('name', read_only=True)
    comfort = serializers.SlugRelatedField('comfort', read_only=True)
    source = serializers.SlugRelatedField('source', read_only=True)
    stake = serializers.SlugRelatedField('stake', read_only=True)

    def get_length_2d(self, obj):
        return round(obj.length_2d, 1)

    class Meta:
        model = Path
        fields = "__all__"


class PathGeojsonSerializer(MapentityGeojsonModelSerializer):
    class Meta(MapentityGeojsonModelSerializer.Meta):
        model = Path
        id_field = 'id'
        fields = ["id", "name", "draft"]


class TrailSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    length = serializers.FloatField(source='length_display')
    name = serializers.CharField(source='name_display')

    class Meta:
        model = Trail
        fields = "__all__"


class TrailGeojsonSerializer(MapentityGeojsonModelSerializer):
    class Meta(MapentityGeojsonModelSerializer.Meta):
        model = Trail
        fields = ["id", "name"]
