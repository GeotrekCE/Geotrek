import logging
from collections import defaultdict
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import Point, LineString, MultiLineString
from django.core.cache import caches
from django.db import connection
from django.db.models import Sum, Prefetch
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified as cache_last_modified
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from mapentity.serializers import GPXSerializer
from mapentity.views import (MapEntityList, MapEntityDetail, MapEntityDocument, MapEntityCreate, MapEntityUpdate,
                             MapEntityDelete, MapEntityFormat, LastModifiedMixin)
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response


import numpy as np
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import csr_matrix

from geotrek.authent.decorators import same_structure_required
from geotrek.common.functions import Length
from geotrek.common.utils import sqlfunction
from geotrek.common.mixins.views import CustomColumnsMixin
from geotrek.common.mixins.forms import FormsetMixin
from geotrek.common.permissions import PublicOrReadPermMixin
from geotrek.common.viewsets import GeotrekMapentityViewSet
from . import graph as graph_lib
from .filters import PathFilterSet, TrailFilterSet
from .forms import PathForm, TrailForm, CertificationTrailFormSet
from .models import AltimetryMixin, Path, Trail, Topology, CertificationTrail
from .serializers import PathSerializer, PathGeojsonSerializer, TrailSerializer, TrailGeojsonSerializer

logger = logging.getLogger(__name__)


class CreateFromTopologyMixin:
    def on_topology(self):
        pk = self.request.GET.get('topology')
        if pk:
            try:
                return Topology.objects.existing().get(pk=pk)
            except Topology.DoesNotExist:
                logger.warning("Intervention on unknown topology %s" % pk)
        return None

    def get_initial(self):
        initial = super().get_initial()
        # Create intervention with an existing topology as initial data
        topology = self.on_topology()
        if topology:
            initial['topology'] = topology.serialize(with_pk=False)
        return initial


class PathList(CustomColumnsMixin, MapEntityList):
    queryset = Path.objects.all()
    filterform = PathFilterSet
    mandatory_columns = ['id', 'checkbox', 'name', 'length']
    default_extra_columns = ['length_2d']
    unorderable_columns = ['checkbox']
    searchable_columns = ['id', 'name']


class PathFormatList(MapEntityFormat, PathList):
    mandatory_columns = ['id']
    default_extra_columns = [
        'structure', 'valid', 'visible', 'name', 'comments', 'departure', 'arrival',
        'comfort', 'source', 'stake', 'usages', 'networks',
        'date_insert', 'date_update', 'length_2d', 'uuid',
    ] + AltimetryMixin.COLUMNS

    def get_queryset(self):
        return super().get_queryset() \
            .select_related('structure', 'comfort', 'source', 'stake') \
            .prefetch_related('usages', 'networks')


class PathDetail(MapEntityDetail):
    model = Path

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['can_edit'] = self.get_object().same_structure(self.request.user)
        return context


class PathGPXDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = Path.objects.all()

    def render_to_response(self, context):
        gpx_serializer = GPXSerializer()
        response = HttpResponse(content_type='application/gpx+xml')
        response['Content-Disposition'] = 'attachment; filename="%s.gpx"' % self.object
        gpx_serializer.serialize([self.object], stream=response, gpx_field='geom_3d')
        return response


class PathKMLDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = Path.objects.all()

    def render_to_response(self, context):
        response = HttpResponse(self.object.kml(),
                                content_type='application/vnd.google-earth.kml+xml')
        response['Content-Disposition'] = 'attachment; filename="%s.kml"' % self.object
        return response


class PathDocument(MapEntityDocument):
    model = Path

    def get_context_data(self, *args, **kwargs):
        language = self.request.LANGUAGE_CODE
        self.get_object().prepare_elevation_chart(language)
        return super().get_context_data(*args, **kwargs)


class PathCreate(MapEntityCreate):
    model = Path
    form_class = PathForm

    def dispatch(self, *args, **kwargs):
        if self.request.user.has_perm('core.add_path') or self.request.user.has_perm('core.add_draft_path'):
            return super(MapEntityCreate, self).dispatch(*args, **kwargs)
        return super().dispatch(*args, **kwargs)


class PathUpdate(MapEntityUpdate):
    model = Path
    form_class = PathForm

    @same_structure_required('core:path_detail')
    def dispatch(self, *args, **kwargs):
        path = self.get_object()
        if path.draft and not self.request.user.has_perm('core.change_draft_path'):
            messages.warning(self.request, _(
                'Access to the requested resource is restricted. You have been redirected.'))
            return redirect('core:path_detail', **kwargs)
        if not path.draft and not self.request.user.has_perm('core.change_path'):
            messages.warning(self.request, _(
                'Access to the requested resource is restricted. You have been redirected.'))
            return redirect('core:path_detail', **kwargs)
        if path.draft and self.request.user.has_perm('core.change_draft_path'):
            return super(MapEntityUpdate, self).dispatch(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        path = self.get_object()
        if path.draft and self.request.user.has_perm('core.delete_draft_path'):
            kwargs['can_delete'] = True
        return kwargs


class MultiplePathDelete(TemplateView):
    template_name = "core/multiplepath_confirm_delete.html"
    model = Path
    success_url = "core:path_list"

    def dispatch(self, *args, **kwargs):
        self.paths_pk = self.kwargs['pk'].split(',')
        self.paths = []
        for pk in self.paths_pk:
            path = Path.objects.get(pk=pk)
            self.paths.append(path)
            if path.draft and not self.request.user.has_perm('core.delete_draft_path'):
                messages.warning(self.request, _(
                    'Access to the requested resource is restricted. You have been redirected.'))
                return redirect('core:path_list')
            if not path.draft and not self.request.user.has_perm('core.delete_path'):
                messages.warning(self.request, _(
                    'Access to the requested resource is restricted. You have been redirected.'))
                return redirect('core:path_list')
            if not path.same_structure(self.request.user):
                messages.warning(self.request, _('Access to the requested resource is restricted by structure. '
                                                 'You have been redirected.'))
                return redirect('core:path_list')
        return super().dispatch(*args, **kwargs)

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        for path in self.paths:
            path.delete()
        return HttpResponseRedirect(reverse(self.success_url))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topologies_by_model = defaultdict(list)
        for path in self.paths:
            path.topologies_by_path(topologies_by_model)
        context['topologies_by_model'] = dict(topologies_by_model)
        return context


class PathDelete(MapEntityDelete):
    model = Path

    @same_structure_required('core:path_detail')
    def dispatch(self, *args, **kwargs):
        path = self.get_object()
        if path.draft and not self.request.user.has_perm('core.delete_draft_path'):
            messages.warning(self.request, _(
                'Access to the requested resource is restricted. You have been redirected.'))
            return redirect('core:path_detail', **kwargs)
        if not path.draft and not self.request.user.has_perm('core.delete_path'):
            messages.warning(self.request, _(
                'Access to the requested resource is restricted. You have been redirected.'))
            return redirect('core:path_detail', **kwargs)
        if path.draft and self.request.user.has_perm('core.delete_draft_path'):
            return super(MapEntityDelete, self).dispatch(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topologies_by_model = defaultdict(list)
        self.object.topologies_by_path(topologies_by_model)
        context['topologies_by_model'] = dict(topologies_by_model)
        return context


class PathViewSet(GeotrekMapentityViewSet):
    model = Path
    serializer_class = PathSerializer
    geojson_serializer_class = PathGeojsonSerializer
    filterset_class = PathFilterSet
    mapentity_list_class = PathList

    def view_cache_key(self):
        """Used by the ``view_cache_response_content`` decorator."""
        language = self.request.LANGUAGE_CODE
        no_draft = self.request.GET.get('_no_draft')
        if no_draft:
            latest_saved = Path.no_draft_latest_updated()
        else:
            latest_saved = Path.latest_updated()
        geojson_lookup = None

        if latest_saved:
            geojson_lookup = '%s_path_%s%s_json_layer' % (
                language,
                latest_saved.strftime('%y%m%d%H%M%S%f'),
                '_nodraft' if no_draft else ''
            )
        return geojson_lookup

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.format_kwarg == 'geojson':
            if self.request.GET.get('_no_draft'):
                qs = qs.exclude(draft=True)
            # get display name if name is undefined to display tooltip on map feature hover
            # Can't use annotate because it doesn't allow to use a model field name
            # Can't use Case(When) in qs.extra
            qs = qs.extra(
                select={'name': "CASE WHEN name IS NULL OR name = '' THEN CONCAT(%s || ' ' || id) ELSE name END"},
                select_params=(_("path"),)
            )

            qs = qs.annotate(api_geom=Transform('geom', settings.API_SRID))
            qs = qs.only("id", "name", "draft")

        else:
            qs = qs.defer('geom', 'geom_cadastre', 'geom_3d')
        return qs

    def get_filter_count_infos(self, qs):
        """ Add total path length to count infos in List dropdown menu """
        data = super().get_filter_count_infos(qs)
        return f"{data} ({round(qs.aggregate(sumPath=Sum(Length('geom') / 1000)).get('sumPath') or 0, 1)} km)"

    @method_decorator(cache_control(max_age=0, must_revalidate=True))
    @method_decorator(cache_last_modified(lambda x: Path.no_draft_latest_updated()))
    @action(methods=['GET'], detail=False, url_path='graph.json', renderer_classes=[JSONRenderer, BrowsableAPIRenderer])
    def graph(self, request, *args, **kwargs):
        """ Return a graph of the path. """
        cache = caches['fat']
        key = 'path_graph_json'

        result = cache.get(key)
        latest = Path.no_draft_latest_updated()

        if result and latest:
            cache_latest, graph = result
            # Not empty and still valid
            if cache_latest and cache_latest >= latest:
                return Response(graph)

        # cache does not exist or is not up-to-date, rebuild the graph and cache it
        graph = graph_lib.graph_edges_nodes_of_qs(Path.objects.exclude(draft=True))

        cache.set(key, (latest, graph))
        return Response(graph)

    @method_decorator(permission_required('core.change_path'))
    @action(methods=['POST'], detail=False, renderer_classes=[JSONRenderer])
    def merge_path(self, request, *args, **kwargs):
        try:
            ids_path_merge = request.POST.getlist('path[]')

            if len(ids_path_merge) != 2:
                raise Exception(_("You should select two paths"))
            paths = [int(path) for path in ids_path_merge]
            path_a = Path.objects.get(pk=min(paths))
            path_b = Path.objects.get(pk=max(paths))

            if not path_a.same_structure(request.user) or not path_b.same_structure(request.user):
                raise Exception(_("You don't have the right to change these paths"))

            if path_a.draft != path_b.draft:
                raise Exception(_("You can't merge 1 draft path with 1 normal path"))

            result = path_a.merge_path(path_b)

            if result == 2:
                raise Exception(_("You can't merge 2 paths with a 3rd path in the intersection"))

            elif result == 0:
                raise Exception(_("No matching points to merge paths found"))

            else:
                response = {'success': _("Paths merged successfully")}
                messages.success(request, response['success'])

        except Exception as exc:
            response = {'error': '%s' % exc, }

        return Response(response)


class CertificationTrailMixin(FormsetMixin):
    context_name = 'certificationtrail_formset'
    formset_class = CertificationTrailFormSet


class TrailList(CustomColumnsMixin, MapEntityList):
    queryset = Trail.objects.existing()
    filterform = TrailFilterSet
    mandatory_columns = ['id', 'name']
    default_extra_columns = ['departure', 'arrival', 'length']
    searchable_columns = ['id', 'name', 'departure', 'arrival', ]


class TrailFormatList(MapEntityFormat, TrailList):
    mandatory_columns = ['id']
    default_extra_columns = [
        'structure', 'name', 'comments',
        'departure', 'arrival', 'category',
        'certifications', 'date_insert', 'date_update',
        'cities', 'districts', 'areas', 'uuid',
    ] + AltimetryMixin.COLUMNS

    def get_queryset(self):
        return super().get_queryset() \
            .select_related('category__structure') \
            .prefetch_related(Prefetch('certifications',
                                       queryset=CertificationTrail.objects.select_related(
                                           'certification_label',
                                           'certification_status'
                                       )))


class TrailDetail(MapEntityDetail):
    queryset = Trail.objects.existing()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['can_edit'] = self.get_object().same_structure(self.request.user)
        return context


class TrailGPXDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = Trail.objects.existing()

    def render_to_response(self, context):
        gpx_serializer = GPXSerializer()
        response = HttpResponse(content_type='application/gpx+xml')
        response['Content-Disposition'] = 'attachment; filename="%s.gpx"' % self.object
        gpx_serializer.serialize([self.object], stream=response, gpx_field='geom_3d')
        return response


class TrailKMLDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = Trail.objects.existing()

    def render_to_response(self, context):
        response = HttpResponse(self.object.kml(),
                                content_type='application/vnd.google-earth.kml+xml')
        response['Content-Disposition'] = 'attachment; filename="%s.kml"' % self.object
        return response


class TrailDocument(MapEntityDocument):
    queryset = Trail.objects.existing()


class TrailCreate(CreateFromTopologyMixin, CertificationTrailMixin, MapEntityCreate):
    model = Trail
    form_class = TrailForm


class TrailUpdate(CertificationTrailMixin, MapEntityUpdate):
    queryset = Trail.objects.existing()
    form_class = TrailForm

    @same_structure_required('core:trail_detail')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class TrailDelete(MapEntityDelete):
    queryset = Trail.objects.existing()

    @same_structure_required('core:trail_detail')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class TrailViewSet(GeotrekMapentityViewSet):
    model = Trail
    serializer_class = TrailSerializer
    geojson_serializer_class = TrailGeojsonSerializer
    filterset_class = TrailFilterSet
    mapentity_list_class = TrailList

    def get_queryset(self):
        qs = self.model.objects.existing()
        if self.format_kwarg == 'geojson':
            qs = qs.annotate(api_geom=Transform('geom', settings.API_SRID))
            qs = qs.only('id', 'name')
        else:
            qs = qs.defer('geom', 'geom_3d')
        return qs


class TrekGeometry(View):

    def get_cs_graph(self):

        def get_edge_weight(edge_id):
            edge = self.edges.get(edge_id)
            if edge is None:
                return None
            return edge.get('length')

        array = []
        for key1, value1 in self.nodes.items():
            row = []
            for key2, value2 in self.nodes.items():
                if key1 == key2:
                    # If it's the same node, the weight is 0
                    row.append(0)
                elif key2 in value1.keys():
                    # If the nodes are linked by a single edge, the weight is
                    # the edge length
                    edge_id = self.get_edge_id_by_nodes(value1, value2)
                    edge_weight = get_edge_weight(edge_id)
                    if edge_weight is not None:
                        row.append(edge_weight)
                else:
                    # If the nodes are not directly linked, the weight is 0
                    row.append(0)
            array.append(row)

        return np.array(array)

    def get_edge_id_by_nodes(self, node1, node2):
        for value in node1.values():
            if value in node2.values():
                return value
        return None

    def compute_list_of_paths(self):
        total_line_strings = []
        # Compute the shortest path for each pair of adjacent steps
        for i in range(len(self.steps) - 1):
            from_step = self.steps[i]
            to_step = self.steps[i + 1]
            line_strings = self.compute_two_steps_line_strings(from_step, to_step)
            total_line_strings += line_strings
        return total_line_strings

    def add_steps_to_graph(self, from_step, to_step):

        def create_point_from_coords(lat, lng):
            point = Point(lng, lat, srid=settings.API_SRID)
            point.transform(settings.SRID)
            return point

        def fill_point_closest_path_info(point):
            # Path and edge info
            point['base_path'] = base_path = Path.closest(point['geom'])
            point['edge_id'] = edge_id = base_path.pk
            point['edge'] = edge = self.edges[edge_id]

            # Nodes linked by this edge
            point['first_node_id'] = edge.get('nodes_id')[0]
            point['last_node_id'] = edge.get('nodes_id')[1]

            # Percentage of the Path this point is on
            base_path_str = f"'{base_path.geom}'"
            point_str = f"'{point['geom'].ewkt}'"
            percent_distance = sqlfunction('SELECT ST_LineLocatePoint',
                                           base_path_str, point_str)[0]
            point['percent_distance'] = percent_distance

        # Create a Point corresponding to each step
        from_point, to_point = {}, {}
        from_point['geom'] = create_point_from_coords(from_step['lat'], from_step['lng'])
        to_point['geom'] = create_point_from_coords(to_step['lat'], to_step['lng'])

        # Get the Path (and corresponding graph edge info) each Point is on
        fill_point_closest_path_info(from_point)
        fill_point_closest_path_info(to_point)

        # If the steps are on the same edge, it's divided into 3 new edges
        if from_point['edge_id'] == to_point['edge_id']:
            from_node_info, to_node_info = self.split_edge_in_three(from_point,
                                                                    to_point)
        # If they are on different edges, both are divided into two new edges
        else:
            from_node_info = self.split_edge_in_two(from_point)
            to_node_info = self.split_edge_in_two(to_point)
        return (from_node_info, to_node_info)

    def compute_two_steps_line_strings(self, from_step, to_step):
        from_node_info, to_node_info = self.add_steps_to_graph(from_step, to_step)

        shortest_path = self.get_shortest_path(from_node_info['node_id'],
                                               to_node_info['node_id'])
        line_strings = self.node_list_to_line_strings(shortest_path,
                                                      from_node_info, to_node_info)

        # Restore the graph (remove the steps)
        self.remove_step_from_graph(from_node_info)
        self.remove_step_from_graph(to_node_info)
        return line_strings

    def node_list_to_line_strings(self, node_list, from_node_info, to_node_info):
        line_strings = []
        # Get a LineString for each pair of adjacent nodes in the path
        for i in range(len(node_list) - 1):
            # Get the id of the edge corresponding to these nodes
            node1 = self.nodes[node_list[i]]
            node2 = self.nodes[node_list[i + 1]]
            edge_id = self.get_edge_id_by_nodes(node1, node2)

            # If this pair of nodes requires to go backwards relative to a
            # Path direction (i.e. the edge 2nd node is the 1st of this pair)
            backwards = False
            if self.edges[edge_id]['nodes_id'][1] == node_list[i]:
                backwards = True
            
            # If it's the first or last edge of this subpath (it can be both!),
            # then the edge is temporary (i.e. created because of a step)
            if i == 0 or i == len(node_list) - 2:
                # Start and end percentages of the line substring to be created
                start_fraction = 0
                end_fraction = 1
                if backwards:
                    start_fraction, end_fraction = end_fraction, start_fraction

                if i == 0:
                    original_path = Path.objects.get(pk=from_node_info['original_egde_id'])
                    start_fraction = from_node_info['percent_of_edge']
                if i == len(node_list) - 2:
                    original_path = Path.objects.get(pk=to_node_info['original_egde_id'])
                    end_fraction = to_node_info['percent_of_edge']

                line_substring = self.create_line_substring(
                    original_path.geom,
                    start_fraction,
                    end_fraction
                )
                line_strings.append(line_substring)

            # If it's a real edge (i.e. it corresponds to a whole path),
            # we use its LineString
            else:
                path = Path.objects.get(pk=edge_id)
                line_strings.append(path.geom)

        return line_strings

    def create_line_substring(self, geometry, start_fraction, end_fraction):
        sql = """
        SELECT ST_AsText(ST_SmartLineSubstring('{}'::geometry, {}, {}))
        """.format(geometry, start_fraction, end_fraction)

        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()[0]

        # Convert the string into an array of arrays of floats
        coords_str = result.split('(')[1].split(')')[0]
        str_points_array = [elem.split(' ') for elem in coords_str.split(',')]
        arr = [[float(nb) for nb in sub_array] for sub_array in str_points_array]

        line_substring = LineString(arr, srid=settings.SRID)
        return line_substring

    def split_edge_in_two(self, point_info):

        # Get the length of the edges that will be created
        path_length = point_info['base_path'].length
        dist_to_start = path_length * point_info['percent_distance']
        dist_to_end = path_length * (1 - point_info['percent_distance'])

        # Create the new node and edges
        new_node_id = self.generate_id()
        edge1 = {
            'id': self.generate_id(),
            'length': dist_to_start,
            'nodes_id': [point_info['first_node_id'], new_node_id],
        }
        edge2 = {
            'id': self.generate_id(),
            'length': dist_to_end,
            'nodes_id': [new_node_id, point_info['last_node_id']],
        }
        first_node, last_node, new_node = {}, {}, {}
        first_node[new_node_id] = new_node[point_info['first_node_id']] = edge1['id']
        last_node[new_node_id] = new_node[point_info['last_node_id']] = edge2['id']

        # Add them to the graph
        self.edges[edge1['id']] = edge1
        self.edges[edge2['id']] = edge2
        self.nodes[new_node_id] = new_node
        self.extend_dict(self.nodes[point_info['first_node_id']], first_node)
        self.extend_dict(self.nodes[point_info['last_node_id']], last_node)

        new_node_info = {
            'node_id': new_node_id,
            'new_edge1_id': edge1['id'],
            'new_edge2_id': edge2['id'],
            'prev_node_id': point_info['first_node_id'],
            'next_node_id': point_info['last_node_id'],
            'original_egde_id': point_info['edge_id'],
            'percent_of_edge': point_info['percent_distance'],
        }
        return new_node_info

    def split_edge_in_three(self, from_point, to_point):
        # Get the length of the edges that will be created
        path_length = from_point['base_path'].length
        start_percent = from_point['percent_distance']
        end_percent = to_point['percent_distance']

        # If we're going backwards relative to the Path direction
        start_percent, end_percent = end_percent, start_percent

        dist_to_start = path_length * start_percent
        dist_to_end = path_length * (1 - end_percent)
        dist_middle = path_length - dist_to_start - dist_to_end

        # Create the new nodes and edges
        new_node_id_1 = self.generate_id()
        new_node_id_2 = self.generate_id()
        edge1 = {
            'id': self.generate_id(),
            'length': dist_to_start,
            'nodes_id': [from_point['first_node_id'], new_node_id_1],
        }
        edge2 = {
            'id': self.generate_id(),
            'length': dist_middle,
            'nodes_id': [new_node_id_1, new_node_id_2],
        }
        edge3 = {
            'id': self.generate_id(),
            'length': dist_to_end,
            'nodes_id': [new_node_id_2, from_point['last_node_id']],
        }

        # Link them together and to the existing nodes
        first_node, last_node, new_node_1, new_node_2 = {}, {}, {}, {}
        first_node[new_node_id_1] = new_node_1[from_point['first_node_id']] = edge1['id']
        new_node_1[new_node_id_2] = new_node_2[new_node_id_1] = edge2['id']
        new_node_2[from_point['last_node_id']] = last_node[new_node_id_2] = edge3['id']

        # Add them to the graph
        self.edges[edge1['id']] = edge1
        self.edges[edge2['id']] = edge2
        self.edges[edge3['id']] = edge3
        self.nodes[new_node_id_1] = new_node_1
        self.nodes[new_node_id_2] = new_node_2
        self.extend_dict(self.nodes[from_point['first_node_id']], first_node)
        self.extend_dict(self.nodes[from_point['last_node_id']], last_node)

        new_node_info_1 = {
            'node_id': new_node_id_1,
            'new_edge1_id': edge1['id'],
            'new_edge2_id': edge2['id'],
            'prev_node_id': from_point['first_node_id'],
            'next_node_id': new_node_id_2,
            'original_egde_id': from_point['edge_id'],
            'percent_of_edge': from_point['percent_distance'],
        }
        new_node_info_2 = {
            'node_id': new_node_id_2,
            'new_edge1_id': edge2['id'],
            'prev_node_id': new_node_id_1,
            'next_node_id': from_point['last_node_id'],
            'new_edge2_id': edge3['id'],
            'original_egde_id': from_point['edge_id'],
            'percent_of_edge': to_point['percent_distance'],
        }
        return new_node_info_1, new_node_info_2

    def remove_step_from_graph(self, node_info):

        # Remove the 2 new edges from the graph:
        # They will have already been deleted if this is the 2nd step and
        # both steps are on the same path
        if self.edges.get(node_info['new_edge1_id']) is not None:
            del self.edges[node_info['new_edge1_id']]
        if self.edges.get(node_info['new_edge2_id']) is not None:
            del self.edges[node_info['new_edge2_id']]

        # Get the 2 nodes this temporary node is linked to
        prev_node = self.nodes.get(node_info['prev_node_id'])
        next_node = self.nodes.get(node_info['next_node_id'])

        # Remove the new node from the graph
        removed_node_id = node_info['node_id']
        del self.nodes[removed_node_id]
        if prev_node is not None:
            # It will have already been deleted if this is the 2nd step and
            # both steps are on the same path
            del prev_node[removed_node_id]
        del next_node[removed_node_id]

    def extend_dict(self, dict, source):
        for key, value in source.items():
            dict[key] = value

    def get_shortest_path(self, from_node_id, to_node_id):
        cs_graph = self.get_cs_graph()
        matrix = csr_matrix(cs_graph)

        # List of all nodes IDs -> to interprete dijkstra results
        self.nodes_ids = list(self.nodes.keys())

        def get_node_idx_per_id(node_id):
            try:
                return self.nodes_ids.index(node_id)
            except ValueError:
                return None

        def get_node_id_per_idx(node_idx):
            if node_idx >= len(self.nodes_ids):
                return None
            return self.nodes_ids[node_idx]

        from_node_idx = get_node_idx_per_id(from_node_id)
        to_node_idx = get_node_idx_per_id(to_node_id)
        result = dijkstra(matrix, return_predecessors=True, indices=from_node_idx,
                          directed=False)

        # Retrace the path ID by ID, from end to start
        predecessors = result[1]
        current_node_id, current_node_idx = to_node_id, to_node_idx
        path = [current_node_id]
        while current_node_id != from_node_id:
            current_node_idx = predecessors[current_node_idx]
            current_node_id = get_node_id_per_idx(current_node_idx)
            path.append(current_node_id)

        path.reverse()
        return path

    def merge_line_strings(self, line_strings):
        rounded_line_strings = [
            self.round_line_string_coordinates(ls) for ls in line_strings
        ]
        multi_line_string = MultiLineString(rounded_line_strings, srid=settings.SRID)
        return multi_line_string.merged

    def round_line_string_coordinates(self, line_string):
        # TODO: see which precision level is best
        coords = line_string.coords
        new_coords = [[round(nb, 4) for nb in pt_coord] for pt_coord in coords]
        new_line_string = LineString(new_coords, srid=line_string.srid)
        return new_line_string

    def generate_id(self):
        new_id = self.id_count
        self.id_count += 1
        return new_id

    def post(self, request):
        try:
            params = json.loads(request.body.decode())
            self.steps = params['steps']
        except KeyError:
            print("TrekGeometry POST: incorrect parameters")
            # TODO: Bad request

        # To generate IDs for temporary nodes and edges
        self.id_count = 90000000

        graph = graph_lib.graph_edges_nodes_of_qs(Path.objects.exclude(draft=True))
        self.nodes = graph['nodes']
        self.edges = graph['edges']

        line_strings = self.compute_list_of_paths()
        merged_line_string = self.merge_line_strings(line_strings)
        merged_line_string.transform(settings.API_SRID)

        # TODO: use GEOSGeometry.geojson (LineString?)
        geojson = merged_line_string.geojson
        print(geojson, type(geojson))

        return JsonResponse({
            'geojson': {
                'type': 'LineString',
                'coordinates': merged_line_string.coords,
            },
        })
