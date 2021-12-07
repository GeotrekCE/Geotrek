from django_filters import FilterSet
from django.conf import settings
from django.db.models import Q
from django.contrib.gis.geos import GeometryCollection
from django.utils.translation import gettext_lazy as _


from geotrek.common.filters import RightFilter
from geotrek.zoning.models import City, District, RestrictedArea, RestrictedAreaType


class IntersectionFilter(RightFilter):
    """Inherit from ``RightFilter``, just to make sure the widgets
    will be initialized the same way.
    """

    def filter(self, qs, value):
        q = Q()
        for subvalue in value:
            q |= Q(geom__intersects=subvalue.geom)
        return qs.filter(q)


class IntersectionFilterCity(IntersectionFilter):
    model = City


class IntersectionFilterDistrict(IntersectionFilter):
    model = District


class IntersectionFilterRestrictedAreaType(RightFilter):
    model = RestrictedAreaType

    def filter(self, qs, value):
        if not value:
            return qs

        areas_geom = RestrictedArea.objects.filter(area_type__in=value).values_list('geom', flat=True)
        if areas_geom:
            geom = GeometryCollection(*areas_geom, srid=settings.SRID)
            return qs.filter(geom__intersects=geom)
        else:
            return qs.none()

    def get_queryset(self, request=None):
        if self.queryset is not None:
            return self.queryset.order_by("name")
        return self.model.objects.all().order_by("name")


class IntersectionFilterRestrictedArea(IntersectionFilter):
    model = RestrictedArea


class ZoningFilterSet(FilterSet):
    city = IntersectionFilterCity(label=_('City'), required=False)
    district = IntersectionFilterDistrict(label=_('District'), required=False)
    area_type = IntersectionFilterRestrictedAreaType(label=_('Restricted area type'), required=False)
    area = IntersectionFilterRestrictedArea(label=_('Restricted area'), required=False)
