from django_filters import FilterSet
from django.db.models import Q, Exists, OuterRef
from django.utils.translation import gettext_lazy as _


from geotrek.common.mixins.filters import RightFilter
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
        return qs.filter(Exists(RestrictedArea.objects.filter(area_type__in=value, geom__intersects=OuterRef('geom'))))

    def get_queryset(self, request=None):
        return super().get_queryset().order_by("name")


class IntersectionFilterRestrictedArea(IntersectionFilter):
    queryset = RestrictedArea.objects.all().select_related("area_type")


class ZoningFilterSet(FilterSet):
    city = IntersectionFilterCity(label=_('City'), required=False)
    district = IntersectionFilterDistrict(label=_('District'), required=False)
    area_type = IntersectionFilterRestrictedAreaType(label=_('Restricted area type'), required=False)
    area = IntersectionFilterRestrictedArea(label=_('Restricted area'), required=False)
