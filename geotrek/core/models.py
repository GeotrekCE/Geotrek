import functools
import json
import logging
from geotrek.common.signals import log_cascade_deletion
import simplekml
import uuid
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, fromstr, LineString, GEOSGeometry
from django.contrib.postgres.indexes import GistIndex
from django.core.mail import mail_managers
from django.db import connection, connections, DEFAULT_DB_ALIAS
from django.db.models import ProtectedError
from django.db.models.query import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from geotrek.altimetry.models import AltimetryMixin
from geotrek.authent.models import StructureRelated, StructureOrNoneRelated
from geotrek.core.managers import PathManager, PathInvisibleManager, TopologyManager, PathAggregationManager, \
    TrailManager
from geotrek.common.mixins.models import (TimeStampedModelMixin, NoDeleteMixin, AddPropertyMixin,
                                          CheckBoxActionMixin, GeotrekMapEntityMixin)
from geotrek.common.utils import classproperty, simplify_coords, sqlfunction, uniquify
from geotrek.zoning.mixins import ZoningPropertiesMixin
from mapentity.serializers import plain_text

logger = logging.getLogger(__name__)


class Path(CheckBoxActionMixin, ZoningPropertiesMixin, AddPropertyMixin, GeotrekMapEntityMixin, AltimetryMixin,
           TimeStampedModelMixin, StructureRelated, ClusterableModel):
    """ Path model. Spatial indexes disabled because managed in Meta.indexes """
    geom = models.LineStringField(srid=settings.SRID, spatial_index=False)
    geom_cadastre = models.LineStringField(null=True, srid=settings.SRID, spatial_index=False,
                                           editable=False)
    valid = models.BooleanField(default=True, verbose_name=_("Validity"),
                                help_text=_("Approved by manager"))
    visible = models.BooleanField(default=True, verbose_name=_("Visible"),
                                  help_text=_("Shown in lists and maps"))
    name = models.CharField(null=True, blank=True, max_length=250, verbose_name=_("Name"),
                            help_text=_("Official name"))
    comments = models.TextField(null=True, blank=True, verbose_name=_("Comments"),
                                help_text=_("Remarks"))

    departure = models.CharField(null=True, blank=True, default="", max_length=250, verbose_name=_("Departure"),
                                 help_text=_("Departure place"))
    arrival = models.CharField(null=True, blank=True, default="", max_length=250, verbose_name=_("Arrival"),
                               help_text=_("Arrival place"))

    comfort = models.ForeignKey('Comfort', on_delete=models.PROTECT,
                                null=True, blank=True, related_name='paths',
                                verbose_name=_("Comfort"))
    source = models.ForeignKey('PathSource', on_delete=models.PROTECT,
                               null=True, blank=True, related_name='paths',
                               verbose_name=_("Source"))
    stake = models.ForeignKey('Stake', on_delete=models.PROTECT,
                              null=True, blank=True, related_name='paths',
                              verbose_name=_("Maintenance stake"))
    usages = models.ManyToManyField('Usage',
                                    blank=True, related_name="paths",
                                    verbose_name=_("Usages"))
    networks = models.ManyToManyField('Network',
                                      blank=True, related_name="paths",
                                      verbose_name=_("Networks"))
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)
    provider = models.CharField(verbose_name=_("Provider"), db_index=True, max_length=1024, blank=True)
    draft = models.BooleanField(default=False, verbose_name=_("Draft"), db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    source_pgr = models.IntegerField(null=True,
                                     blank=True,
                                     help_text='Internal field used by pgRouting',
                                     editable=False,
                                     db_column='source')
    target_pgr = models.IntegerField(null=True,
                                     blank=True,
                                     help_text='Internal field used by pgRouting',
                                     editable=False,
                                     db_column='target')

    objects = PathManager()
    include_invisible = PathInvisibleManager()

    is_reversed = False
    can_duplicate = False

    @property
    def topology_set(self):
        return Topology.objects.filter(aggregations__path=self)

    @classproperty
    def length_2d_verbose_name(cls):
        return _("2D Length")

    @classmethod
    def no_draft_latest_updated(cls):
        try:
            latest = cls.objects.filter(draft=False).only('date_update').latest('date_update').get_date_update()
        except cls.DoesNotExist:
            latest = None
        return latest

    @property
    def length_2d_display(self):
        return round(self.length_2d, 1)

    def kml(self):
        """ Exports path into KML format, add geometry as linestring """
        kml = simplekml.Kml()
        geom3d = self.geom_3d.transform(4326, clone=True)  # KML uses WGS84

        line = kml.newlinestring(name=self.name,
                                 description=plain_text(self.comments),
                                 coords=simplify_coords(geom3d.coords))
        line.style.linestyle.color = simplekml.Color.red  # Red
        line.style.linestyle.width = 4  # pixels
        return kml.kml()

    def __str__(self):
        return self.name or _('path %d') % self.pk

    class Meta:
        verbose_name = _("Path")
        verbose_name_plural = _("Paths")
        permissions = GeotrekMapEntityMixin._meta.permissions + [
            ("add_draft_path", "Can add draft Path"),
            ("change_draft_path", "Can change draft Path"),
            ("delete_draft_path", "Can delete draft Path"),
        ]
        indexes = [
            GistIndex(name='path_geom_gist_idx', fields=['geom']),
            GistIndex(name='path_geom_cadastre_gist_idx', fields=['geom_cadastre']),
            GistIndex(name='path_geom_3d_gist_idx', fields=['geom_3d']),
            # some other complex indexes can't be created by django and are created in migrations
            # Gist (ST_STARTPOINT(geom)) and (ST_ENDPOINT(geom))
        ]

    @classmethod
    def closest(cls, point, exclude=None):
        """
        Returns the closest path of the point.
        Will fail if no path in database.
        """
        # TODO: move to custom manager
        if point.srid != settings.SRID:
            point = point.transform(settings.SRID, clone=True)
        qs = cls.objects.exclude(draft=True)
        if exclude:
            qs = qs.exclude(pk=exclude.pk)
        return qs.exclude(visible=False).annotate(distance=Distance('geom', point)).order_by('distance')[0]

    @classmethod
    def check_path_not_overlap(cls, geom, pk):
        """
        Returns True if this path does not overlap another.
        TODO: this could be a constraint at DB-level. But this would mean that
        path never ever overlap, even during trigger computation, like path splitting...
        """
        wkt = "ST_GeomFromText('%s', %s)" % (geom, settings.SRID)
        disjoint = sqlfunction('SELECT * FROM check_path_not_overlap', str(pk), wkt)
        return disjoint[0]

    def reverse(self):
        """
        Reverse the geometry.
        We keep track of this, since we will have to work on topologies at save()
        """
        reversed_coord = self.geom.coords[-1::-1]
        self.geom = LineString(reversed_coord)
        self.is_reversed = True
        return self

    def interpolate(self, point):
        """
        Returns position ([0.0-1.0]) and offset (distance) of the point
        along this path.
        """
        if not self.pk:
            raise ValueError("Cannot compute interpolation on unsaved path")
        if point.srid != self.geom.srid:
            point.transform(self.geom.srid)
        cursor = connection.cursor()
        sql = """
        SELECT position, distance
        FROM ft_path_interpolate(%(pk)s, ST_GeomFromText('POINT(%(x)s %(y)s)',%(srid)s))
             AS (position FLOAT, distance FLOAT)
        """ % {'pk': self.pk,
               'x': point.x,
               'y': point.y,
               'srid': self.geom.srid}
        cursor.execute(sql)
        result = cursor.fetchall()
        return result[0]

    def snap(self, point):
        """
        Returns the point snapped (i.e closest) to the path line geometry.
        """
        if not self.pk:
            raise ValueError("Cannot compute snap on unsaved path")
        if point.srid != self.geom.srid:
            point.transform(self.geom.srid)
        cursor = connection.cursor()
        sql = """
        WITH p AS (SELECT ST_ClosestPoint(geom, '%(ewkt)s'::geometry) AS geom
                   FROM %(table)s
                   WHERE id = '%(pk)s')
        SELECT ST_X(p.geom), ST_Y(p.geom) FROM p
        """ % {'ewkt': point.ewkt, 'table': self._meta.db_table, 'pk': self.pk}
        cursor.execute(sql)
        result = cursor.fetchall()
        return Point(*result[0], srid=self.geom.srid)

    def reload(self):
        # Update object's computed values (reload from database)
        if self.pk and self.visible:
            fromdb = self.__class__.objects.get(pk=self.pk)
            self.geom = fromdb.geom
            AltimetryMixin.reload(self, fromdb)
            TimeStampedModelMixin.reload(self, fromdb)
        return self

    def save(self, *args, **kwargs):
        # If the path was reversed, we have to invert related topologies
        if self.is_reversed:
            for aggr in self.aggregations.all():
                aggr.start_position = 1 - aggr.start_position
                aggr.end_position = 1 - aggr.end_position
                aggr.save()
            self._is_reversed = False

        # If draft is set from False to True, and setting ALERT_DRAFT is True, send email to managers
        if (self.pk and self.draft and self.__class__.objects.get(pk=self.pk).draft != self.draft) \
                and settings.ALERT_DRAFT:
            subject = _("{obj} has been set to draft").format(obj=self)
            message = render_to_string('core/draft_email_message.txt', {"obj": self})
            try:
                mail_managers(subject, message, fail_silently=False)
            except Exception as exc:
                msg = f'Caught {exc.__class__.__name__}: {exc}'
                logger.warning(f"Error mail managers didn't work ({msg})")
        super().save(*args, **kwargs)
        self.reload()

    def delete(self, *args, **kwargs):
        if not settings.TREKKING_TOPOLOGY_ENABLED:
            return super().delete(*args, **kwargs)
        topologies = self.topology_set.all()
        if topologies.exists() and not settings.ALLOW_PATH_DELETION_TOPOLOGY:
            raise ProtectedError(_("You can't delete this path, some topologies are linked with this path"), self)
        topologies_list = list(topologies)
        r = super().delete(*args, **kwargs)
        if not Path.objects.exists():
            return r
        for topology in topologies_list:
            if isinstance(topology.geom, Point):
                closest = self.closest(topology.geom, self)
                position, offset = closest.interpolate(topology.geom)
                new_topology = Topology.objects.create()
                aggrobj = PathAggregation(topo_object=new_topology,
                                          start_position=position,
                                          end_position=position,
                                          path=closest)
                aggrobj.save()
                point = Point(topology.geom.x, topology.geom.y, srid=settings.SRID)
                new_topology.geom = point
                new_topology.offset = offset
                new_topology.position = position
                new_topology.save()
                topology.mutate(new_topology)
        return r

    @property
    def name_display(self):
        return '<a data-pk="%s" href="%s" title="%s" >%s</a>' % (self.pk,
                                                                 self.get_detail_url(),
                                                                 self,
                                                                 self)

    @property
    def name_csv_display(self):
        return str(self)

    @classproperty
    def trails_verbose_name(cls):
        return _("Trails")

    @property
    def trails_display(self):
        trails = getattr(self, '_trails', self.trails)
        if trails:
            return ", ".join([t.name_display for t in trails])
        return _("None")

    @property
    def trails_csv_display(self):
        trails = getattr(self, '_trails', self.trails)
        if trails:
            return ", ".join([str(t) for t in trails])
        return _("None")

    @property
    def usages_display(self):
        return ", ".join([str(u) for u in self.usages.all()])

    @property
    def networks_display(self):
        return ", ".join([str(n) for n in self.networks.all()])

    @classmethod
    def get_create_label(cls):
        return _("Add a new path")

    def topologies_by_path(self, default_dict):
        if 'geotrek.core' in settings.INSTALLED_APPS:
            for trail in self.trails:
                default_dict[_('Trails')].append({'name': trail.name, 'url': trail.get_detail_url()})
        if 'geotrek.trekking' in settings.INSTALLED_APPS:
            for trek in self.treks:
                default_dict[_('Treks')].append({'name': trek.name, 'url': trek.get_detail_url()})
            for service in self.services:
                default_dict[_('Services')].append(
                    {'name': service.type.name, 'url': service.get_detail_url()})
            for poi in self.pois:
                default_dict[_('Pois')].append({'name': poi.name, 'url': poi.get_detail_url()})
        if 'geotrek.signage' in settings.INSTALLED_APPS:
            for signage in self.signages:
                default_dict[_('Signages')].append({'name': signage.name, 'url': signage.get_detail_url()})
        if 'geotrek.infrastructure' in settings.INSTALLED_APPS:
            for infrastructure in self.infrastructures:
                default_dict[_('Infrastructures')].append(
                    {'name': infrastructure.name, 'url': infrastructure.get_detail_url()})
        if 'geotrek.maintenance' in settings.INSTALLED_APPS:
            for intervention in self.interventions:
                default_dict[_('Interventions')].append(
                    {'name': intervention.name, 'url': intervention.get_detail_url()})

    def merge_path(self, path_to_merge):
        """
        Path unification
        :param path_to path_to_merge: Path instance to merge
        :return: Boolean
        """
        if (self.pk and path_to_merge) and (self.pk != path_to_merge.pk):
            conn = connections[DEFAULT_DB_ALIAS]
            cursor = conn.cursor()
            sql = "SELECT ft_merge_path({}, {});".format(self.pk, path_to_merge.pk)
            cursor.execute(sql)

            result = cursor.fetchall()[0][0]

            if result:
                # reload object after unification
                self.reload()

            return result

    @property
    def extent(self):
        return self.geom.transform(settings.API_SRID, clone=True).extent if self.geom else None

    def distance(self, to_cls):
        """Distance to associate this path to another class"""
        return None


class Topology(ZoningPropertiesMixin, AddPropertyMixin, AltimetryMixin,
               TimeStampedModelMixin, NoDeleteMixin, ClusterableModel):
    paths = models.ManyToManyField(Path, through='PathAggregation', verbose_name=_("Path"))
    offset = models.FloatField(default=0.0, verbose_name=_("Offset"))  # in SRID units
    kind = models.CharField(editable=False, verbose_name=_("Kind"), max_length=32)
    geom_need_update = models.BooleanField(default=False)

    geom = models.GeometryField(editable=(not settings.TREKKING_TOPOLOGY_ENABLED),
                                srid=settings.SRID, null=True,
                                default=None, spatial_index=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    """ Fake srid attribute, that prevents transform() calls when using Django map widgets. """
    srid = settings.API_SRID

    geometry_types_allowed = ["LINESTRING", "POINT"]
    objects = TopologyManager()

    class Meta:
        verbose_name = _("Topology")
        verbose_name_plural = _("Topologies")
        indexes = [
            GistIndex(name='topology_geom_gist_idx', fields=['geom']),
            GistIndex(name='topology_geom_3d_gist_idx', fields=['geom_3d']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.pk and not self.kind:
            self.kind = self.__class__.KIND

    @property
    def paths(self):    # noqa
        return Path.objects.filter(aggregations__topo_object=self)

    @classproperty
    def length_2d_verbose_name(cls):
        return _("2D Length")

    @property
    def length_2d_display(self):
        return round(self.length_2d, 1)

    @classproperty
    def KIND(cls):
        return cls._meta.object_name.upper()

    def __str__(self):
        return "%s (%s)" % (_("Topology"), self.pk)

    def ispoint(self):
        if not settings.TREKKING_TOPOLOGY_ENABLED or not self.pk:
            return self.geom and self.geom.geom_type == 'Point'
        return all([a.start_position == a.end_position for a in self.aggregations.all()])

    def add_path(self, path, start=0.0, end=1.0, order=0, reload=True):
        """
        Shortcut function to add paths into this topology.
        """
        aggr = PathAggregation.objects.create(topo_object=self,
                                              path=path,
                                              start_position=start,
                                              end_position=end,
                                              order=order)

        if self.deleted:
            self.deleted = False
            self.save(update_fields=['deleted'])

        # Since a trigger modifies geom, we reload the object
        if reload:
            self.reload()
        return aggr

    @classmethod
    def overlapping(cls, queryset, all_objects=None):
        """ Return a Topology queryset overlapping specified topologies.
        """
        if all_objects is None:
            all_objects = cls.objects.existing()
        is_generic = all_objects.model.KIND == Topology.KIND
        single_input = isinstance(queryset, QuerySet)

        if single_input:
            topology_pks = [str(pk) for pk in queryset.values_list('pk', flat=True)]
        else:
            topology_pks = [str(queryset.pk)]

        if len(topology_pks) == 0:
            return all_objects.filter(pk__in=[])

        sql = """
        WITH topologies AS (SELECT id FROM %(topology_table)s WHERE id IN (%(topology_list)s)),
        -- Concerned aggregations
             aggregations AS (SELECT * FROM %(aggregations_table)s a, topologies t
                              WHERE a.topo_object_id = t.id),
        -- Concerned paths along with (start, end)
             paths_aggr AS (SELECT a.start_position AS start, a.end_position AS end, p.id, a.order AS order
                            FROM %(paths_table)s p, aggregations a
                            WHERE a.path_id = p.id
                            ORDER BY a.order)
        -- Retrieve primary keys
        SELECT t.id
        FROM %(topology_table)s t, %(aggregations_table)s a, paths_aggr pa
        WHERE a.path_id = pa.id AND a.topo_object_id = t.id
          AND least(a.start_position, a.end_position) <= greatest(pa.start, pa.end)
          AND greatest(a.start_position, a.end_position) >= least(pa.start, pa.end)
          AND %(extra_condition)s
        ORDER BY (pa.order + CASE WHEN pa.start > pa.end THEN (1 - a.start_position) ELSE a.start_position END);
        """ % {
            'topology_table': Topology._meta.db_table,
            'aggregations_table': PathAggregation._meta.db_table,
            'paths_table': Path._meta.db_table,
            'topology_list': ','.join(topology_pks),
            'extra_condition': 'true' if is_generic else "kind = '%s'" % all_objects.model.KIND
        }

        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        pk_list = uniquify([row[0] for row in result])

        # Return a QuerySet and preserve pk list order
        # http://stackoverflow.com/a/1310188/141895
        ordering = 'CASE %s END' % ' '.join(['WHEN %s.id=%s THEN %s' % (Topology._meta.db_table, id_, i)
                                             for i, id_ in enumerate(pk_list)])
        queryset = all_objects.filter(pk__in=pk_list).extra(
            select={'ordering': ordering}, order_by=('ordering',))
        return queryset

    def mutate(self, other):
        """
        Take alls attributes of the other topology specified and
        save them into this one. Optionnally deletes the other.
        """
        self.offset = other.offset
        self.save(update_fields=['offset'])
        PathAggregation.objects.filter(topo_object=self).delete()
        # The previous operation has put deleted = True (in triggers)
        # and NULL in geom (see update_geometry_of_topology:: IF t_count = 0)
        self.deleted = False
        self.geom = other.geom
        self.save(update_fields=['deleted', 'geom'])

        # Now copy all agregations from other to self
        aggrs = other.aggregations.all()
        # A point has only one aggregation, except if it is on an intersection.
        # In this case, the trigger will create them, so ignore them here.
        if other.ispoint():
            aggrs = aggrs[:1]
        PathAggregation.objects.bulk_create([
            PathAggregation(
                path=aggr.path,
                topo_object=self,
                start_position=aggr.start_position,
                end_position=aggr.end_position,
                order=aggr.order
            )
            for aggr in aggrs
        ])
        self.reload()
        return self

    def reload(self):
        """
        Reload into instance all computed attributes in triggers.
        """
        if self.pk:
            # Update computed values
            fromdb = self.__class__.objects.get(pk=self.pk)
            self.geom = fromdb.geom
            # /!\ offset may be set by a trigger OR in
            # the django code, reload() will override
            # any unsaved value
            self.offset = fromdb.offset
            AltimetryMixin.reload(self, fromdb)
            TimeStampedModelMixin.reload(self, fromdb)
            NoDeleteMixin.reload(self, fromdb)

        return self

    def save(self, *args, **kwargs):
        # HACK: these fields are readonly from the Django point of view
        # but they can be changed at DB level. Since Django write all fields
        # to DB anyway, it is important to update it before writting
        if self.pk and settings.TREKKING_TOPOLOGY_ENABLED:
            existing = self.__class__.objects.get(pk=self.pk)
            self.length = existing.length
            # In the case of points, the geom can be set by Django. Don't override.
            point_geom_not_set = self.ispoint() and self.geom is None
            geom_already_in_db = not self.ispoint() and existing.geom is not None
            if (point_geom_not_set or geom_already_in_db):
                self.geom = existing.geom
        else:
            if not self.deleted and self.geom is None:
                # We cannot have NULL geometry. So we use an empty one,
                # it will be computed or overwritten by triggers.
                self.geom = fromstr('POINT (0 0)')

        if not self.kind:
            if self.KIND == "TOPOLOGYMIXIN":
                raise Exception("Cannot save abstract topologies")
            self.kind = self.__class__.KIND

        # Static value for Topology offset, if any
        shortmodelname = self._meta.object_name.lower().replace('edge', '')
        self.offset = settings.TOPOLOGY_STATIC_OFFSETS.get(shortmodelname, self.offset)

        # Save into db
        super().save(*args, **kwargs)
        self.reload()

    def serialize(self, with_pk=True):
        if not self.aggregations.exists():
            # Empty topology
            return ''
        elif self.ispoint():
            # Point topology
            point = self.geom.transform(settings.API_SRID, clone=True)
            objdict = dict(kind=self.kind, lng=point.x, lat=point.y)
            if with_pk:
                objdict['pk'] = self.pk
            if settings.TREKKING_TOPOLOGY_ENABLED and self.offset == 0:
                objdict['snap'] = self.aggregations.all()[0].path.pk
        else:
            # Line topology
            # Fetch properly ordered aggregations
            aggregations = self.aggregations.select_related('path').all()
            objdict = []
            current = {}
            ipath = 0
            for i, aggr in enumerate(aggregations):
                last = i == len(aggregations) - 1
                intermediary = aggr.start_position == aggr.end_position

                if with_pk:
                    current.setdefault('pk', self.pk)
                current.setdefault('kind', self.kind)
                current.setdefault('offset', self.offset)
                if not intermediary:
                    current.setdefault('paths', []).append(aggr.path.pk)
                    current.setdefault('positions', {})[ipath] = (aggr.start_position, aggr.end_position)
                ipath = ipath + 1

                subtopology_done = 'paths' in current and (intermediary or last)
                if subtopology_done:
                    objdict.append(current)
                    current = {}
                    ipath = 0
        return json.dumps(objdict)

    @classmethod
    def _topologypoint(cls, lng, lat, kind=None, snap=None):
        """
        Receives a point (lng, lat) with API_SRID, and returns
        a topology objects with a computed path aggregation.
        """
        # Find closest path
        point = Point(lng, lat, srid=settings.API_SRID)
        point.transform(settings.SRID)
        if snap is None:
            closest = Path.closest(point)
            position, offset = closest.interpolate(point)
        else:
            closest = Path.objects.get(pk=snap)
            position, offset = closest.interpolate(point)
            offset = 0
        # We can now instantiante a Topology object
        topology = Topology(kind=kind, offset=offset)
        aggr = PathAggregation(
            topo_object=topology,
            path=closest,
            start_position=position,
            end_position=position
        )
        topology.aggregations = [aggr]
        closest.aggregations.add(aggr)
        point = Point(point.x, point.y, srid=settings.SRID)
        topology.geom = point
        return topology

    @classmethod
    def deserialize(cls, serialized):
        """
        Topologies can be points or lines. Serialized topologies come from Javascript
        module ``topology_helper.js``.

        Example of linear point topology (snapped with path 1245):

            {"lat":5.0, "lng":10.2, "snap":1245}

        Example of linear serialized topology :

        [
            {"offset":0,"positions":{"0":[0,0.3],"1":[0.2,1]},"paths":[1264,1208]},
            {"offset":0,"positions":{"0":[0.2,1],"5":[0,0.2]},"paths":[1208,1263,678,1265,1266,686]}
        ]

        * Each sub-topology represents a way between markers.
        * Start point is first position of sub-topology.
        * End point is last position of sub-topology.
        * All last positions represents intermediary markers.

        Global strategy is :
        * If has lat/lng return point topology
        * Otherwise, create path aggregations from serialized data.
        ____________________________________________________________________________________________
        Without Dynamic Segmentation :

        Deserialize normally and create a topology from the geojson
        """
        try:
            return Topology.objects.get(pk=int(serialized))
        except Topology.DoesNotExist:
            raise
        except (TypeError, ValueError):
            pass  # value is not integer, thus should be deserialized
        if not settings.TREKKING_TOPOLOGY_ENABLED:
            return Topology(kind='TMP', geom=GEOSGeometry(serialized, srid=settings.API_SRID))
        objdict = serialized
        if isinstance(serialized, str):
            try:
                objdict = json.loads(serialized)
            except ValueError as e:
                raise ValueError("Invalid serialization: %s" % e)

        if objdict and not isinstance(objdict, list):
            lat = objdict.get('lat')
            lng = objdict.get('lng')
            pk = objdict.get('pk')
            kind = objdict.get('kind')
            # Point topology ?
            if lat is not None and lng is not None:
                if pk:
                    try:
                        return Topology.objects.get(pk=int(pk))
                    except (Topology.DoesNotExist, ValueError):
                        pass

                return Topology._topologypoint(lng, lat, kind, snap=objdict.get('snap'))
            else:
                objdict = [objdict]

        if not objdict:
            raise ValueError("Invalid serialized topology : empty list found")

        # If pk is still here, the user did not edit it.
        # Return existing topology instead
        pk = objdict[0].get('pk')
        if pk:
            try:
                return Topology.objects.get(pk=int(pk))
            except (Topology.DoesNotExist, ValueError):
                pass

        offset = objdict[0].get('offset', 0.0)
        topology = Topology(kind='TMP', offset=offset)
        try:
            counter = 0
            for j, subtopology in enumerate(objdict):
                last_topo = j == len(objdict) - 1
                positions = subtopology.get('positions', {})
                paths = subtopology['paths']
                # Create path aggregations
                aggrs = []
                for i, path in enumerate(paths):
                    last_path = i == len(paths) - 1
                    # Javascript hash keys are parsed as a string
                    idx = str(i)
                    start_position, end_position = positions.get(idx, (0.0, 1.0))
                    path = Path.objects.get(pk=path)
                    aggr = PathAggregation(
                        path=path,
                        topo_object=topology,
                        start_position=start_position,
                        end_position=end_position,
                        order=counter
                    )
                    aggrs.append(aggr)
                    path.aggregations.add(aggr)
                    if not last_topo and last_path:
                        counter += 1
                        # Intermediary marker.
                        # make sure pos will be [X, X]
                        # [0, X] or [X, 1] or [X, 0] or [1, X] --> X
                        # [0.0, 0.0] --> 0.0  : marker at beginning of path
                        # [1.0, 1.0] --> 1.0  : marker at end of path
                        pos = -1
                        if start_position == end_position:
                            pos = start_position
                        if start_position == 0.0:
                            pos = end_position
                        elif start_position == 1.0:
                            pos = end_position
                        elif end_position == 0.0:
                            pos = start_position
                        elif end_position == 1.0:
                            pos = start_position
                        elif len(paths) == 1:
                            pos = end_position
                        assert pos >= 0, "Invalid position (%s, %s)." % (start_position, end_position)
                        aggr = PathAggregation(
                            path=path,
                            topo_object=topology,
                            start_position=pos,
                            end_position=pos,
                            order=counter
                        )
                        aggrs.append(aggr)
                        path.aggregations.add(aggr)
                    counter += 1
                topology.aggregations.add(*aggrs)
        except (AssertionError, ValueError, KeyError, Path.DoesNotExist) as e:
            raise ValueError("Invalid serialized topology : %s" % e)
        return topology

    def distance(self, to_cls):
        """Distance to associate this topology to another topology class"""
        return None

    @property
    def aggregations_optimized(self):
        return self.aggregations.all().select_related('path')


class PathAggregation(models.Model):
    path = ParentalKey(Path, null=False,
                       verbose_name=_("Path"),
                       related_name="aggregations",
                       on_delete=models.DO_NOTHING)  # The CASCADE behavior is enforced at DB-level (see file ../sql/30_topologies_paths.sql)
    topo_object = ParentalKey(Topology, null=False, related_name="aggregations", on_delete=models.CASCADE,
                              verbose_name=_("Topology"))
    start_position = models.FloatField(verbose_name=_("Start position"), db_index=True)
    end_position = models.FloatField(verbose_name=_("End position"), db_index=True)
    order = models.IntegerField(default=0, blank=True, null=True, verbose_name=_("Order"))

    # Override default manager
    objects = PathAggregationManager()

    def __str__(self):
        return "%s (%s-%s: %s - %s)" % (_("Path aggregation"), self.path.pk, self.path.name, self.start_position, self.end_position)

    @property
    def start_meter(self):
        try:
            return 0 if self.start_position == 0.0 else int(self.start_position * self.path.length)
        except ValueError:
            return -1

    @property
    def end_meter(self):
        try:
            return 0 if self.end_position == 0.0 else int(self.end_position * self.path.length)
        except ValueError:
            return -1

    @property
    def is_full(self):
        return (self.start_position == 0.0 and self.end_position == 1.0
                or self.start_position == 1.0 and self.end_position == 0.0)

    class Meta:
        verbose_name = _("Path aggregation")
        verbose_name_plural = _("Path aggregations")
        # Important - represent the order of the path in the Topology path list
        ordering = ['order', ]


@receiver(pre_delete, sender=Path)
def log_cascade_deletion_from_pathaggregation_path(sender, instance, using, **kwargs):
    # PathAggregation are deleted when Path are deleted
    log_cascade_deletion(sender, instance, PathAggregation, 'path')


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_pathaggregation_topology(sender, instance, using, **kwargs):
    # PathAggregation are deleted when Topology are deleted
    log_cascade_deletion(sender, instance, PathAggregation, 'topo_object')


class PathSource(StructureOrNoneRelated):
    source = models.CharField(verbose_name=_("Source"), max_length=50)

    class Meta:
        verbose_name = _("Path source")
        verbose_name_plural = _("Path sources")
        ordering = ['source']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.source, self.structure.name)
        return self.source


@functools.total_ordering
class Stake(StructureOrNoneRelated):
    stake = models.CharField(verbose_name=_("Stake"), max_length=50)

    class Meta:
        verbose_name = _("Maintenance stake")
        verbose_name_plural = _("Maintenance stakes")
        ordering = ['id']

    def __lt__(self, other):
        if other is None:
            return False
        return self.pk < other.pk

    def __eq__(self, other):
        return isinstance(other, Stake) \
            and self.pk == other.pk

    def __hash__(self):
        return super().__hash__()

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.stake, self.structure.name)
        return self.stake


class Comfort(StructureOrNoneRelated):

    comfort = models.CharField(verbose_name=_("Comfort"), max_length=50)

    class Meta:
        verbose_name = _("Comfort")
        verbose_name_plural = _("Comforts")
        ordering = ['comfort']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.comfort, self.structure.name)
        return self.comfort


class Usage(StructureOrNoneRelated):

    usage = models.CharField(verbose_name=_("Usage"), max_length=50)

    class Meta:
        verbose_name = _("Usage")
        verbose_name_plural = _("Usages")
        ordering = ['usage']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.usage, self.structure.name)
        return self.usage


class Network(StructureOrNoneRelated):
    network = models.CharField(verbose_name=_("Network"), max_length=50)

    class Meta:
        verbose_name = _("Network")
        verbose_name_plural = _("Networks")
        ordering = ['network']

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.network, self.structure.name)
        return self.network


class Trail(GeotrekMapEntityMixin, Topology, StructureRelated):
    topo_object = models.OneToOneField(Topology, parent_link=True, on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_("Name"), max_length=64)
    category = models.ForeignKey(
        "TrailCategory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Category"),
    )
    departure = models.CharField(verbose_name=_("Departure"), blank=True, max_length=64)
    arrival = models.CharField(verbose_name=_("Arrival"), blank=True, max_length=64)
    comments = models.TextField(default="", blank=True, verbose_name=_("Comments"))
    eid = models.CharField(verbose_name=_("External id"), max_length=1024, blank=True, null=True)
    provider = models.CharField(verbose_name=_("Provider"), db_index=True, max_length=1024, blank=True)

    certifications_verbose_name = _("Certifications")
    geometry_types_allowed = ["LINESTRING"]

    objects = TrailManager()

    class Meta:
        verbose_name = _("Trail")
        verbose_name_plural = _("Trails")
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def name_display(self):
        return '<a data-pk="%s" href="%s" title="%s" >%s</a>' % (self.pk,
                                                                 self.get_detail_url(),
                                                                 self,
                                                                 self)

    @property
    def certifications_display(self):
        return ', '.join([str(n) for n in self.certifications.all()])

    @classmethod
    def path_trails(cls, path):
        trails = cls.objects.existing().filter(aggregations__path=path)
        # The following part prevents conflict with default trail ordering
        # ProgrammingError: SELECT DISTINCT ON expressions must match initial ORDER BY expressions
        return trails.order_by('topo_object').distinct('topo_object')

    def kml(self):
        """ Exports path into KML format, add geometry as linestring """
        kml = simplekml.Kml()
        geom3d = self.geom_3d.transform(4326, clone=True)  # KML uses WGS84
        line = kml.newlinestring(name=self.name,
                                 description=plain_text(self.comments),
                                 coords=simplify_coords(geom3d.coords))
        line.style.linestyle.color = simplekml.Color.red  # Red
        line.style.linestyle.width = 4  # pixels
        return kml.kml()


@receiver(pre_delete, sender=Topology)
def log_cascade_deletion_from_trail_topology(sender, instance, using, **kwargs):
    # Trail are deleted when Topologies are deleted
    log_cascade_deletion(sender, instance, Trail, 'topo_object')


class TrailCategory(StructureOrNoneRelated):
    """Trail category"""
    label = models.CharField(verbose_name=_("Name"), max_length=128)

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.label, self.structure.name)
        return self.label

    class Meta:
        verbose_name = _("Trail category")
        verbose_name_plural = _("Trail categories")
        ordering = ['label']
        unique_together = (
            ('label', 'structure'),
        )


class CertificationLabel(StructureOrNoneRelated):
    """Certification label model"""
    label = models.CharField(verbose_name=_("Name"), max_length=128)

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.label, self.structure.name)
        return self.label

    class Meta:
        verbose_name = _("Certification label")
        verbose_name_plural = _("Certification labels")
        ordering = ['label']
        unique_together = (
            ('label', 'structure'),
        )


class CertificationStatus(StructureOrNoneRelated):
    """Certification status model"""
    label = models.CharField(verbose_name=_("Name"), max_length=128)

    def __str__(self):
        if self.structure:
            return "{} ({})".format(self.label, self.structure.name)
        return self.label

    class Meta:
        verbose_name = _("Certification status")
        verbose_name_plural = _("Certification statuses")
        ordering = ['label']
        unique_together = (
            ('label', 'structure'),
        )


class CertificationTrail(StructureOrNoneRelated):
    """Certification trail model"""

    trail = models.ForeignKey("core.Trail",
                              related_name='certifications',
                              on_delete=models.CASCADE,
                              verbose_name=_("Trail"))
    certification_label = models.ForeignKey("core.CertificationLabel",
                                            related_name='certifications',
                                            on_delete=models.PROTECT,
                                            verbose_name=_("Certification label"))
    certification_status = models.ForeignKey("core.CertificationStatus",
                                             related_name='certifications',
                                             on_delete=models.PROTECT,
                                             verbose_name=_("Certification status"))

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")
        unique_together = (
            ('trail', 'certification_label', 'certification_status'),
        )

    def __str__(self):
        return f"{self.certification_label} / {self.certification_status}"


@receiver(pre_delete, sender=Trail)
def log_cascade_deletion_from_certificationtrail_trail(sender, instance, using, **kwargs):
    # CertificationTrail are deleted when Trails are deleted
    log_cascade_deletion(sender, instance, CertificationTrail, 'trail')


Path.add_property('trails', lambda self: Trail.path_trails(self), _("Trails"))
Topology.add_property('trails', lambda self: Trail.overlapping(self), _("Trails"))
