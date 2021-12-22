from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.utils.decorators import method_decorator
from djgeojson.views import GeoJSONLayerView

from .models import City, RestrictedArea, RestrictedAreaType, District


class LandLayerMixin:
    srid = settings.API_SRID
    precision = settings.LAYER_PRECISION_LAND
    simplify = settings.LAYER_SIMPLIFY_LAND

    @method_decorator(cache_page(settings.CACHE_TIMEOUT_LAND_LAYERS,
                                 cache=settings.MAPENTITY_CONFIG['GEOJSON_LAYERS_CACHE_BACKEND']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CityGeoJSONLayer(LandLayerMixin, GeoJSONLayerView):
    model = City


class RestrictedAreaGeoJSONLayer(LandLayerMixin, GeoJSONLayerView):
    model = RestrictedArea


class RestrictedAreaTypeGeoJSONLayer(LandLayerMixin, GeoJSONLayerView):
    model = RestrictedArea

    def get_queryset(self):
        type_pk = self.kwargs['type_pk']
        qs = super().get_queryset()
        get_object_or_404(RestrictedAreaType, pk=type_pk)
        return qs.filter(area_type=type_pk)


class DistrictGeoJSONLayer(LandLayerMixin, GeoJSONLayerView):
    model = District
    properties = ['name']
