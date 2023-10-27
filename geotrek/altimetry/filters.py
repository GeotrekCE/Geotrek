from django.utils.translation import gettext_lazy as _

from django_filters import FilterSet

from geotrek.common.mixins.filters import OptionalRangeFilter


class AltimetryPointFilterSet(FilterSet):
    elevation = OptionalRangeFilter(label=_('elevation'), method='filter_elevation')

    def filter_elevation(self, qs, name, value):
        # TODO: Remove, when min_elevation and max_elevation use DecimalRangeField
        if value.start is not None:
            lookup_start = '%s__%s' % ('min_elevation', 'gte')
            qs = qs.filter(**{lookup_start: value.start})
        if value.stop is not None:
            lookup_stop = '%s__%s' % ('max_elevation', 'lte')
            qs = qs.filter(**{lookup_stop: value.stop})
        return qs


class AltimetryAllGeometriesFilterSet(AltimetryPointFilterSet):
    length = OptionalRangeFilter(field_name='length_2d', label=_('length'))
    length_3d = OptionalRangeFilter(field_name='length', label=_('length 3d'))
    ascent = OptionalRangeFilter(label=_('ascent'))
    descent = OptionalRangeFilter(label=_('descent'))
    slope = OptionalRangeFilter(label=_('slope'))
