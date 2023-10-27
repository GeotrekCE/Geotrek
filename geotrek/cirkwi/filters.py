from django_filters import FilterSet
from geotrek.authent.models import Structure
from geotrek.common.mixins.filters import ComaSeparatedMultipleModelChoiceFilter
from geotrek.common.models import TargetPortal
from geotrek.trekking.models import POI, Trek


class CirkwiPOIFilterSet(FilterSet):
    structures = ComaSeparatedMultipleModelChoiceFilter(field_name='structure', required=False,
                                                        queryset=Structure.objects.all())

    class Meta:
        model = POI
        fields = ('structures', )


class CirkwiTrekFilterSet(FilterSet):
    structures = ComaSeparatedMultipleModelChoiceFilter(field_name='structure', required=False,
                                                        queryset=Structure.objects.all())
    portals = ComaSeparatedMultipleModelChoiceFilter(field_name='portal', required=False,
                                                     queryset=TargetPortal.objects.all())

    class Meta:
        model = Trek
        fields = ('structures', 'portals', )
