from django.utils.translation import gettext_lazy as _

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
    SignageManagementEdge, WorkManagementEdge,
)


class PhysicalEdgeFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = PhysicalEdge
        fields = ['physical_type']


class LandEdgeFilterSet(ValidTopologyFilterSet, MapEntityFilterSet):
    class Meta(MapEntityFilterSet.Meta):
        model = LandEdge
        fields = ['land_type', 'owner', 'agreement']


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


class TopologyFilterPhysicalType(TopologyFilter):
    model = PhysicalType

    def values_to_edges(self, values):
        return PhysicalEdge.objects.filter(physical_type__in=values)


class TopologyFilterLandType(TopologyFilter):
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
        'physical_type': TopologyFilterPhysicalType(label=_('Physical type'), required=False),
        'land_type': TopologyFilterLandType(label=_('Land type'), required=False),
        'competence': TopologyFilterCompetenceEdge(label=_('Competence'), required=False),
        'signage': TopologyFilterSignageManagementEdge(label=_('Signage management'), required=False),
        'work': TopologyFilterWorkManagementEdge(label=_('Work management'), required=False),
    })


add_edge_filters(TrekFilterSet)
add_edge_filters(POIFilterSet)
add_edge_filters(InterventionFilterSet)
add_edge_filters(ProjectFilterSet)
add_edge_filters(PathFilterSet)
add_edge_filters(InfrastructureFilterSet)
add_edge_filters(SignageFilterSet)
add_edge_filters(TrailFilterSet)
