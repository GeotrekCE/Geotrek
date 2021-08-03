from django.conf import settings
from django.db.models import F, Q, Prefetch
from django.db.models.aggregates import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import activate

from rest_framework.response import Response

from geotrek.api.v2 import serializers as api_serializers, \
    viewsets as api_viewsets, filters as api_filters
from geotrek.api.v2.functions import Transform, Length, Length3D
from geotrek.trekking import models as trekking_models


class WebLinkCategoryViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.WebLinkCategorySerializer
    queryset = trekking_models.WebLinkCategory.objects.all()


class TrekViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (api_filters.GeotrekTrekQueryParamsFilter,)
    serializer_class = api_serializers.TrekSerializer

    def get_queryset(self):
        activate(self.request.GET.get('language'))
        return trekking_models.Trek.objects.existing() \
            .select_related('topo_object') \
            .prefetch_related('topo_object__aggregations', 'accessibilities', 'attachments',
                              Prefetch('web_links',
                                       queryset=trekking_models.WebLink.objects.select_related('category'))) \
            .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID),
                      length_2d_m=Length('geom'),
                      length_3d_m=Length3D('geom_3d')) \
            .order_by("name")  # Required for reliable pagination

    def retrieve(self, request, pk=None, format=None):
        # Return detail view even for unpublished treks that are childrens of other published treks
        qs_filtered = self.filter_published_lang_retrieve(request, self.get_queryset())
        try:
            trek = qs_filtered.get(pk=pk)
        except self.get_queryset().model.DoesNotExist:
            raise Http404('No %s matches the given query.' % self.get_queryset().model._meta.object_name)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(trek, many=False, context={'request': request})
        return Response(serializer.data)

    def filter_published_lang_retrieve(self, request, queryset):
        # filter trek by publication language (including parents publication language)
        qs = queryset
        language = request.GET.get('language', 'all')
        associated_published_fields = [f.name for f in qs.model._meta.get_fields() if f.name.startswith('published')]

        if language == 'all':
            # no language specified. Check for all.
            q = Q()
            for lang in settings.MODELTRANSLATION_LANGUAGES:
                field_name = 'published_{}'.format(lang)
                if field_name in associated_published_fields:
                    field_name_parent = 'trek_parents__parent__published_{}'.format(lang)
                    q |= Q(**{field_name: True}) | Q(**{field_name_parent: True})
            qs = qs.filter(q)
        else:
            # one language is specified
            field_name = 'published_{}'.format(language)
            field_name_parent = 'trek_parents__parent__published_{}'.format(language)
            qs = qs.filter(Q(**{field_name: True}) | Q(**{field_name_parent: True}))
        return qs.distinct()


class TourViewSet(TrekViewSet):
    serializer_class = api_serializers.TourSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(count_children=Count('trek_children'))\
            .filter(count_children__gt=0)
        return qs


class PracticeViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRelatedPortalTrekFilter,)
    serializer_class = api_serializers.PracticeSerializer
    queryset = trekking_models.Practice.objects.all()

    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Practice, pk=pk)
        serializer = api_serializers.PracticeSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class NetworkViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRelatedPortalTrekFilter,)
    serializer_class = api_serializers.NetworkSerializer
    queryset = trekking_models.TrekNetwork.objects.all()

    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.TrekNetwork, pk=pk)
        serializer = api_serializers.NetworkSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class DifficultyViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRelatedPortalTrekFilter,)
    serializer_class = api_serializers.TrekDifficultySerializer
    queryset = trekking_models.DifficultyLevel.objects.all()

    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.DifficultyLevel, pk=pk)
        serializer = api_serializers.TrekDifficultySerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class POIViewSet(api_viewsets.GeotrekGeometricViewset):
    filter_backends = api_viewsets.GeotrekGeometricViewset.filter_backends + (api_filters.GeotrekPOIFilter,)
    serializer_class = api_serializers.POISerializer
    queryset = trekking_models.POI.objects.existing() \
        .select_related('topo_object', 'type', ) \
        .prefetch_related('topo_object__aggregations', 'attachments') \
        .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID)) \
        .order_by('pk')  # Required for reliable pagination


class POITypeViewSet(api_viewsets.GeotrekViewSet):
    serializer_class = api_serializers.POITypeSerializer
    queryset = trekking_models.POIType.objects.all()


class AccessibilityViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRelatedPortalTrekFilter,)
    serializer_class = api_serializers.AccessibilitySerializer
    queryset = trekking_models.Accessibility.objects.all()

    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Accessibility, pk=pk)
        serializer = api_serializers.AccessibilitySerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)


class RouteViewSet(api_viewsets.GeotrekViewSet):
    filter_backends = api_viewsets.GeotrekViewSet.filter_backends + (api_filters.GeotrekRelatedPortalTrekFilter,)
    serializer_class = api_serializers.RouteSerializer
    queryset = trekking_models.Route.objects.all()

    def retrieve(self, request, pk=None, format=None):
        # Allow to retrieve objects even if not visible in list view
        elem = get_object_or_404(trekking_models.Route, pk=pk)
        serializer = api_serializers.RouteSerializer(elem, many=False, context={'request': request})
        return Response(serializer.data)
