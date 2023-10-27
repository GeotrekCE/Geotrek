from mapentity.filters import MapEntityFilterSet

from geotrek.common.models import HDViewPoint


class HDViewPointFilterSet(MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = HDViewPoint
        fields = ['title']
