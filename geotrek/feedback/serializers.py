from django.contrib.gis.geos import GEOSGeometry
from rest_framework import serializers as rest_serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from geotrek.feedback import models as feedback_models


class ReportSerializer(rest_serializers.ModelSerializer):
    class Meta:
        model = feedback_models.Report
        id_field = 'id'
        fields = ('id', 'email', 'activity', 'comment', 'category',
                  'status', 'problem_magnitude', 'geom', 'context_object')

    def validate_geom(self, value):
        return GEOSGeometry(value, srid=4326)


class ReportGeojsonSerializer(GeoFeatureModelSerializer, ReportSerializer):
    # Annotated geom field with API_SRID
    api_geom = GeometryField(read_only=True, precision=7)

    class Meta(ReportSerializer.Meta):
        geo_field = 'api_geom'
        fields = ReportSerializer.Meta.fields + ('api_geom', )
