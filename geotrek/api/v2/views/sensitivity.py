import logging
import datetime

from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.db.models import F, Case, When
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from geotrek.api.v2 import serializers as api_serializers, \
    viewsets as api_viewsets
from geotrek.common.functions import GeometryType, Buffer, Area
from geotrek.sensitivity import models as sensitivity_models
from ..filters import GeotrekQueryParamsFilter, GeotrekQueryParamsDimensionFilter, GeotrekInBBoxFilter, GeotrekSensitiveAreaFilter, NearbyContentFilter, UpdateOrCreateDateFilter


logger = logging.getLogger(__name__)


class SensitiveAreaViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = (
        DjangoFilterBackend,
        GeotrekQueryParamsFilter,
        GeotrekQueryParamsDimensionFilter,
        GeotrekInBBoxFilter,
        GeotrekSensitiveAreaFilter,
        NearbyContentFilter,
        UpdateOrCreateDateFilter,
    )
    bbox_filter_field = 'geom_transformed'
    bbox_filter_include_overlapping = True
    renderer_classes = api_viewsets.GeotrekGeometricViewset.renderer_classes + [TemplateHTMLRenderer]
    template_name = 'sensitivity/sensitivearea_detail_public.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.accepted_renderer.format == 'html':
            logger.debug(f'INSTANCE {instance}')
            if instance:
                current_month = datetime.date.today().month
                return Response(
                    {
                        'object': instance,
                        'current_month': current_month,
                        'current_sensitivity': instance.species.list_period()[current_month - 1]
                    }
                )
            else:
                return NotFound()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_class(self):
        if 'bubble' in self.request.GET:
            base_serializer_class = api_serializers.BubbleSensitiveAreaSerializer
        else:
            base_serializer_class = api_serializers.SensitiveAreaSerializer
        format_output = self.request.query_params.get('format', 'json')
        return api_serializers.override_serializer(format_output, base_serializer_class)

    def get_queryset(self):
        queryset = sensitivity_models.SensitiveArea.objects.existing() \
            .filter(published=True) \
            .select_related('species', 'structure') \
            .prefetch_related('species__practices') \
            .alias(geom_type=GeometryType(F('geom')))
        if 'bubble' in self.request.GET:
            queryset = queryset.annotate(geom_transformed=Transform(F('geom'), settings.API_SRID))
        else:
            queryset = queryset.annotate(geom_transformed=Case(
                When(geom_type='POINT', then=Transform(Buffer(F('geom'), F('species__radius'), 4), settings.API_SRID)),
                default=Transform(F('geom'), settings.API_SRID)
            ))
        # Ensure smaller areas are at the end of the list, ie above bigger areas on the map
        # to ensure we can select every area in case of overlapping
        # Second sort key pk is required for reliable pagination
        queryset = queryset.order_by(Area('geom_transformed').desc(), 'pk')
        return queryset.defer('geom')


class SportPracticeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.SportPracticeSerializer

    def get_queryset(self):
        queryset = sensitivity_models.SportPractice.objects.all()
        queryset = queryset.order_by('pk')  # Required for reliable pagination
        return queryset


class SpeciesViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.SpeciesSerializer

    def get_queryset(self):
        queryset = sensitivity_models.Species.objects.all()
        queryset = queryset.order_by('pk')  # Required for reliable pagination
        return queryset
