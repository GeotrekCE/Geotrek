from django.conf import settings
from django.contrib.gis.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from geotrek.authent.models import StructureOrNoneRelated
from geotrek.common.signals import log_cascade_deletion
from geotrek.core.models import Topology, Path
from geotrek.common.models import Organism
from geotrek.common.mixins.models import GeotrekMapEntityMixin
from geotrek.maintenance.models import Intervention, Project


if 'geotrek.signage' in settings.INSTALLED_APPS:
    from geotrek.signage.models import Blade


class Status(GeotrekMapEntityMixin):
    """
    Model with a verbose name to represent this module (meta-class)
    """
    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")


class PhysicalType(StructureOrNoneRelated):
    name = models.CharField(max_length=128, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Physical type")
        verbose_name_plural = _("Physical types")
        ordering = ['name']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.name, self.structure.name)
        return self.name


class PhysicalEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    physical_type = models.ForeignKey(PhysicalType, verbose_name=_("Physical type"),
                                      on_delete=models.PROTECT)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Physical edge")
        verbose_name_plural = _("Physical edges")

    def __str__(self):
        return _("Physical edge") + ": %s" % self.physical_type

    @property
    def color_index(self):
        return self.physical_type_id

    @property
    def name(self):
        return self.physical_type_csv_display

    @property
    def name_display(self):
        return self.physical_type_display

    @property
    def physical_type_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.physical_type
        )

    @property
    def physical_type_csv_display(self):
        return str(self.physical_type)

    @classmethod
    def path_physicals(cls, path):
        return cls.objects.existing().select_related('physical_type', 'physical_type__structure').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_physicals(cls, topology):
        return cls.overlapping(topology).select_related('physical_type', 'physical_type__structure')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_physicaledge_topology(sender, instance, using, **kwargs):
    # PhysicalEdges are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, PhysicalEdge, 'topo_object')


Path.add_property('physical_edges', PhysicalEdge.path_physicals, _("Physical edges"))
Topology.add_property('physical_edges', PhysicalEdge.topology_physicals, _("Physical edges"))
Intervention.add_property('physical_edges', lambda self: self.target.physical_edges if self.target and hasattr(self.target, 'physical_edges') else [], _("Physical edges"))
Project.add_property('physical_edges', lambda self: self.edges_by_attr('physical_edges'), _("Physical edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('physical_edges', lambda self: self.signage.physical_edges, _("Physical edges"))


class LandType(StructureOrNoneRelated):
    name = models.CharField(max_length=128, verbose_name=_("Name"))
    right_of_way = models.BooleanField(default=False, verbose_name=_("Right of way"))

    class Meta:
        verbose_name = _("Land type")
        verbose_name_plural = _("Land types")
        ordering = ['name']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.name, self.structure.name)
        return self.name


class LandEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    land_type = models.ForeignKey(LandType, verbose_name=_("Land type"), on_delete=models.PROTECT)
    owner = models.TextField(verbose_name=_("Owner"), blank=True)
    agreement = models.BooleanField(verbose_name=_("Agreement"), default=False)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)
    identification = models.CharField(verbose_name=_("Land id"), max_length=40, blank=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Land edge")
        verbose_name_plural = _("Land edges")

    def __str__(self):
        return _("Land edge") + ": %s" % self.land_type

    @property
    def color_index(self):
        return self.land_type_id

    @property
    def name(self):
        return self.land_type_csv_display

    @property
    def name_display(self):
        return self.land_type_display

    @property
    def land_type_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.land_type
        )

    @property
    def land_type_csv_display(self):
        return str(self.land_type)

    @classmethod
    def path_lands(cls, path):
        return cls.objects.existing().select_related('land_type').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_lands(cls, topology):
        return cls.overlapping(topology).select_related('land_type')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_landedge_topology(sender, instance, using, **kwargs):
    # LandEdges are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, LandEdge, 'topo_object')


Path.add_property('land_edges', LandEdge.path_lands, _("Land edges"))
Topology.add_property('land_edges', LandEdge.topology_lands, _("Land edges"))
Intervention.add_property('land_edges', lambda self: self.target.land_edges if self.target and hasattr(self.target, 'land_edges') else [], _("Land edges"))
Project.add_property('land_edges', lambda self: self.edges_by_attr('land_edges'), _("Land edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('land_edges', lambda self: self.signage.land_edges, _("Land edges"))


class CompetenceEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organism, verbose_name=_("Organism"), on_delete=models.PROTECT)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Competence edge")
        verbose_name_plural = _("Competence edges")

    def __str__(self):
        return _("Competence edge") + ": %s" % self.organization

    @property
    def color_index(self):
        return self.organization_id

    @property
    def name(self):
        return self.organization_csv_display

    @property
    def name_display(self):
        return self.organization_display

    @property
    def organization_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.organization
        )

    @property
    def organization_csv_display(self):
        return str(self.organization)

    @classmethod
    def path_competences(cls, path):
        return cls.objects.existing().select_related('organization').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_competences(cls, topology):
        return cls.overlapping(Topology.objects.get(pk=topology.pk)).select_related('organization')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_competenceedge_topology(sender, instance, using, **kwargs):
    # CompetenceEdges are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, CompetenceEdge, 'topo_object')


Path.add_property('competence_edges', CompetenceEdge.path_competences, _("Competence edges"))
Topology.add_property('competence_edges', CompetenceEdge.topology_competences, _("Competence edges"))
Intervention.add_property('competence_edges', lambda self: self.target.competence_edges if self.target and hasattr(self.target, 'competence_edges') else [], _("Competence edges"))
Project.add_property('competence_edges', lambda self: self.edges_by_attr('competence_edges'), _("Competence edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('competence_edges', lambda self: self.signage.competence_edges, _("Competence edges"))


class WorkManagementEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organism, verbose_name=_("Organism"), on_delete=models.PROTECT)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Work management edge")
        verbose_name_plural = _("Work management edges")

    def __str__(self):
        return _("Work management edge") + ": %s" % self.organization

    @property
    def color_index(self):
        return self.organization_id

    @property
    def name(self):
        return self.organization_csv_display

    @property
    def name_display(self):
        return self.organization_display

    @property
    def organization_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.organization
        )

    @property
    def organization_csv_display(self):
        return str(self.organization)

    @classmethod
    def path_works(cls, path):
        return cls.objects.existing().select_related('organization').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_works(cls, topology):
        return cls.overlapping(topology).select_related('organization')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_workmanagementedge_topology(sender, instance, using, **kwargs):
    # WorkManagementEdges are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, WorkManagementEdge, 'topo_object')


Path.add_property('work_edges', WorkManagementEdge.path_works, _("Work management edges"))
Topology.add_property('work_edges', WorkManagementEdge.topology_works, _("Work management edges"))
Intervention.add_property('work_edges', lambda self: self.target.work_edges if self.target and hasattr(self.target, 'work_edges') else [], _("Work management edges"))
Project.add_property('work_edges', lambda self: self.edges_by_attr('work_edges'), _("Work management edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('work_edges', lambda self: self.signage.work_edges, _("Work management edges"))


class SignageManagementEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organism, verbose_name=_("Organism"), on_delete=models.PROTECT)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Signage management edge")
        verbose_name_plural = _("Signage management edges")

    def __str__(self):
        return _("Signage management edge") + ": %s" % self.organization

    @property
    def color_index(self):
        return self.organization_id

    @property
    def name(self):
        return self.organization_csv_display

    @property
    def name_display(self):
        return self.organization_display

    @property
    def organization_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.organization
        )

    @property
    def organization_csv_display(self):
        return str(self.organization)

    @classmethod
    def path_signages(cls, path):
        return cls.objects.existing().select_related('organization').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_signages(cls, topology):
        return cls.overlapping(topology).select_related('organization')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_signagemanagementedge_topology(sender, instance, using, **kwargs):
    # SignageManagementEdge are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, SignageManagementEdge, 'topo_object')


Path.add_property('signage_edges', SignageManagementEdge.path_signages, _("Signage management edges"))
Topology.add_property('signage_edges', SignageManagementEdge.topology_signages, _("Signage management edges"))
Intervention.add_property('signage_edges', lambda self: self.target.signage_edges if self.target and hasattr(self.target, 'signage_edges') else [], _("Signage management edges"))
Project.add_property('signage_edges', lambda self: self.edges_by_attr('signage_edges'), _("Signage management edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('signage_edges', lambda self: self.signage.signage_edges, _("Signage management edges"))


class CirculationType(StructureOrNoneRelated):
    name = models.CharField(max_length=128, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Circulation type")
        verbose_name_plural = _("Circulation types")
        ordering = ['name']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.name, self.structure.name)
        return self.name


class AuthorizationType(StructureOrNoneRelated):
    name = models.CharField(max_length=128, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Authorization type")
        verbose_name_plural = _("Authorization types")
        ordering = ['name']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.name, self.structure.name)
        return self.name


class CirculationEdge(GeotrekMapEntityMixin, Topology):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    circulation_type = models.ForeignKey(CirculationType, verbose_name=_("Circulation type"), on_delete=models.PROTECT)
    authorization_type = models.ForeignKey(AuthorizationType, verbose_name=_("Authorization type"), on_delete=models.PROTECT)
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True)

    geometry_types_allowed = ["LINESTRING"]

    class Meta:
        verbose_name = _("Circulation edge")
        verbose_name_plural = _("Circulation edges")

    def __str__(self):
        return _("Circulation edge") + ": %s" % self.circulation_type

    @property
    def color_index(self):
        return self.circulation_type_id

    @property
    def name(self):
        return self.circulation_type_csv_display

    @property
    def name_display(self):
        return self.circulation_type_display

    @property
    def circulation_type_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.circulation_type
        )

    @property
    def authorization_type_display(self):
        return '<a data-pk="%s" href="%s" >%s</a>' % (
            self.pk,
            self.get_detail_url(),
            self.authorization_type
        )

    @property
    def circulation_type_csv_display(self):
        return str(self.circulation_type)

    @classmethod
    def path_circulations(cls, path):
        return cls.objects.existing().select_related('circulation_type').filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_circulations(cls, topology):
        return cls.overlapping(topology).select_related('circulation_type')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_circulationedge_topology(sender, instance, using, **kwargs):
    # CirculationEdges are deleted when topologies are deleted
    log_cascade_deletion(sender, instance, CirculationEdge, 'topo_object')


Path.add_property('circulation_edges', CirculationEdge.path_circulations, _("Circulation edges"))
Topology.add_property('circulation_edges', CirculationEdge.topology_circulations, _("Circulation edges"))
Intervention.add_property('circulation_edges', lambda self: self.target.circulation_edges if self.target and hasattr(self.target, 'circulation_edges') else [], _("Circulation edges"))
Project.add_property('circulation_edges', lambda self: self.edges_by_attr('circulation_edges'), _("Circulation edges"))
if 'geotrek.signage' in settings.INSTALLED_APPS:
    Blade.add_property('circulation_edges', lambda self: self.signage.circulation_edges, _("Circulation edges"))
