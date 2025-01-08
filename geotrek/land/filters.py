from django.utils.translation import gettext_lazy as _
from django_filters import LookupChoiceFilter
from django import forms

from mapentity.filters import MapEntityFilterSet

from geotrek.common.models import Organism

from geotrek.core.filters import TopologyFilter, PathFilterSet, TrailFilterSet, ValidTopologyFilterSet
from geotrek.infrastructure.filters import InfrastructureFilterSet
from geotrek.signage.filters import SignageFilterSet
from geotrek.maintenance.filters import InterventionFilterSet, ProjectFilterSet
from geotrek.trekking.filters import TrekFilterSet, POIFilterSet
from geotrek.zoning.filters import *  # NOQA

from .models import (
    CompetenceEdge, LandEdge, LandType, PhysicalEdge, PhysicalType,
    SignageManagementEdge, WorkManagementEdge, CirculationEdge, CirculationType,
    AuthorizationType
)


class PhysicalEdgeFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = PhysicalEdge
        fields = ['physical_type']


class CirculationEdgeFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = CirculationEdge
        fields = ['circulation_type', 'authorization_type']


class LandEdgeFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = LandEdge
        fields = ['land_type', 'owner', 'agreement', 'identification']

    identification_choices = LandEdge.objects.values_list('identification', 'identification').order_by('identification').distinct()

    identification = LookupChoiceFilter(
        field_class=forms.CharField,
        lookup_choices=[
            ('contains', 'Contains'),
            ('startswith', 'Starts with'),
            ('endswith', 'Ends with'),
        ]
    )


class OrganismFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        fields = ['organization']


class CompetenceEdgeFilterSet(OrganismFilterSet):
    class Meta(OrganismFilterSet.Meta):
        model = CompetenceEdge


class WorkManagementEdgeFilterSet(OrganismFilterSet):
    class Meta(OrganismFilterSet.Meta):
        model = WorkManagementEdge


class SignageManagementEdgeFilterSet(OrganismFilterSet):
    class Meta(OrganismFilterSet.Meta):
        model = SignageManagementEdge


"""

    Injected filter fields

"""


class PrefetchStructureMixin:
    def get_queryset(self, request=None):
        qs = super().get_queryset(request)
        return qs.select_related('structure')


class TopologyFilterPhysicalType(PrefetchStructureMixin, TopologyFilter):
    model = PhysicalType

    def values_to_edges(self, values):
        return PhysicalEdge.objects.filter(physical_type__in=values)


class TopologyFilterCirculationType(PrefetchStructureMixin, TopologyFilter):
    model = CirculationType

    def values_to_edges(self, values):
        return CirculationEdge.objects.filter(circulation_type__in=values)


class TopologyFilterAuthorizationType(PrefetchStructureMixin, TopologyFilter):
    model = AuthorizationType

    def values_to_edges(self, values):
        return CirculationEdge.objects.filter(authorization_type__in=values)


class TopologyFilterLandType(PrefetchStructureMixin, TopologyFilter):
    model = LandType

    def values_to_edges(self, values):
        return LandEdge.objects.filter(land_type__in=values)


class TopologyFilterCompetenceEdge(TopologyFilter):
    model = Organism

    def values_to_edges(self, values):
        return CompetenceEdge.objects.filter(organization__in=values).select_related('organization')


class TopologyFilterSignageManagementEdge(TopologyFilter):
    model = Organism

    def values_to_edges(self, values):
        return SignageManagementEdge.objects.filter(organization__in=values).select_related('organization')


class TopologyFilterWorkManagementEdge(TopologyFilter):
    model = Organism

    def values_to_edges(self, values):
        return WorkManagementEdge.objects.filter(organization__in=values).select_related('organization')


def add_edge_filters(filter_set):
    filter_set.add_filters({
        'land_type': TopologyFilterLandType(label=_('Land edge'), required=False),
        'physical_type': TopologyFilterPhysicalType(label=_('Physical edge'), required=False),
        'circulation_type': TopologyFilterCirculationType(label=_('Circulation edge'), required=False),
        'authorization_type': TopologyFilterAuthorizationType(label=_('Circulation edge'), required=False),
        'competence': TopologyFilterCompetenceEdge(label=_('Competence edge'), required=False),
        'signage': TopologyFilterSignageManagementEdge(label=_('Signage management edge'), required=False),
        'work': TopologyFilterWorkManagementEdge(label=_('Work management edge'), required=False),
    })


add_edge_filters(TrekFilterSet)
add_edge_filters(POIFilterSet)
add_edge_filters(InterventionFilterSet)
add_edge_filters(ProjectFilterSet)
add_edge_filters(PathFilterSet)
add_edge_filters(InfrastructureFilterSet)
add_edge_filters(SignageFilterSet)
add_edge_filters(TrailFilterSet)
