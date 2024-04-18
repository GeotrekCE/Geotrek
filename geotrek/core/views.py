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

    def compute_two_steps_line_strings(self, from_step, to_step):
        # Add the steps to the graph
        # TODO: only add them if the step is a marker?
        from_node_info = self.add_step_to_graph(from_step)
        to_node_info = self.add_step_to_graph(to_step)

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

            # If it's the first or last edge of this subpath (it can be both!),
            # then the edge is temporary (i.e. created because of a step) 
            if i == 0 or i == len(node_list) - 2:
                # Start and end percentages of the line substring to be created
                start_fraction = 0
                end_fraction = 1
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
                # Get the id of the edge corresponding to these nodes
                node1 = self.nodes[node_list[i]]
                node2 = self.nodes[node_list[i + 1]]
                edge_id = self.get_edge_id_by_nodes(node1, node2)

                path = Path.objects.get(pk=edge_id)
                line_strings.append(path.geom)

        return line_strings
    
    def create_line_substring(self, geometry, start_fraction, end_fraction):
        sql = """
        SELECT ST_AsText(ST_LineSubstring('{}'::geometry, {}, {})) 
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

    def add_step_to_graph(self, step):
        # Create a Point corresponding to this step
        point = Point(step['lng'], step['lat'], srid=settings.API_SRID)
        point.transform(settings.SRID)

        # Get the Path (and corresponding graph edge) this Point is on
        base_path = Path.closest(point)
        edge_id = base_path.pk
        edge = self.edges[edge_id]

        # Get the edge nodes
        first_node_id = edge.get('nodes_id')[0]
        last_node_id = edge.get('nodes_id')[1]

        # Get the percentage of the Path this Point is on
        base_path_str = "'{}'".format(base_path.geom)
        point_str = "'{}'".format(point.ewkt)
        percent_distance = sqlfunction('SELECT ST_LineLocatePoint',
                                       base_path_str, point_str)[0]

        path_length = base_path.length

        # Get the length of the edges that will be created
        dist_to_start = path_length * percent_distance
        dist_to_end = path_length * (1 - percent_distance)

        # Create the new node and edges
        new_node_id = self.generate_id()
        edge1 = {
            'id': self.generate_id(),
            'length': dist_to_start,
            'nodes_id': [first_node_id, new_node_id],
        }
        edge2 = {
            'id': self.generate_id(),
            'length': dist_to_end,
            'nodes_id': [new_node_id, last_node_id],
        }
        first_node, last_node, new_node = {}, {}, {}
        first_node[new_node_id] = new_node[first_node_id] = edge1['id']
        last_node[new_node_id] = new_node[last_node_id] = edge2['id']

        # Add them to the graph
        self.edges[edge1['id']] = edge1
        self.edges[edge2['id']] = edge2
        self.nodes[new_node_id] = new_node
        self.extend_dict(self.nodes[first_node_id], first_node)
        self.extend_dict(self.nodes[last_node_id], last_node)

        # TODO: return a 'new edges' array?
        new_node_info = {
            'node_id': new_node_id,
            'new_edge1_id': edge1['id'],
            'new_edge2_id': edge2['id'],
            'original_egde_id': edge_id,
            'percent_of_edge': percent_distance,
        }
        return new_node_info

    def remove_step_from_graph(self, node_info):
        # Remove the 2 new edges from the graph
        del self.edges[node_info['new_edge1_id']]
        del self.edges[node_info['new_edge2_id']]

        # Get the 2 nodes of the original edge (the one the step was on)
        original_edge = self.edges[node_info['original_egde_id']]
        nodes_id = original_edge['nodes_id']
        first_node = self.nodes[nodes_id[0]]
        last_node = self.nodes[nodes_id[1]]

        # Remove the new node from the graph
        removed_node_id = node_info['node_id']
        del self.nodes[removed_node_id]
        del first_node[removed_node_id]
        del last_node[removed_node_id]

    def extend_dict(self, dict, source):
        for key, value in source.items():
            dict[key] = value

    def get_shortest_path(self, from_node_id, to_node_id):
        cs_graph = self.get_cs_graph()
        matrix = csr_matrix(cs_graph)

        # List of all nodes indexes -> to interprete dijkstra results
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

        # Retrace the path index by index, from end to start
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
    
    trek = {
        "type": "LineString",
        "coordinates": [
                [5.8921902,44.6888518,1451.0],[5.8920368,44.688848,1450.0],[5.8918196,44.6888427,1450.0],[5.8916025,44.6888373,1450.0],[5.8913771,44.6887051,1450.0],[5.8913211,44.6886722,1450.0],[5.8911518,44.6885729,1449.0],[5.8909265,44.6884407,1447.0],[5.8907777,44.6884446,1446.0],[5.8907187,44.6885704,1444.0],[5.8906597,44.6886963,1442.0],[5.8906033,44.6888946,1440.0],[5.890547,44.6890929,1439.0],[5.890488,44.6893027,1437.0],[5.890429,44.6895124,1435.0],[5.8901876,44.6895086,1433.0],[5.8902719,44.6896295,1431.0],[5.8902885,44.6896336,1430.0],[5.8903788,44.68967,1429.0],[5.8905075,44.6897414,1428.0],[5.8905388,44.6897847,1428.0],[5.890582,44.6898403,1427.0],[5.8904582,44.6898609,1427.0],[5.8903831,44.68988,1426.0],[5.8903027,44.6898952,1426.0],[5.8902007,44.6899295,1426.0],[5.8901364,44.6899524,1425.0],[5.890072,44.6899867,1425.0],[5.890013,44.6900134,1425.0],[5.8899647,44.6900287,1425.0],[5.8898681,44.6900439,1424.0],[5.889793,44.6900478,1424.0],[5.8896858,44.6900401,1424.0],[5.8895946,44.6900211,1424.0],[5.8895007,44.6899951,1424.0],[5.889498,44.6899944,1424.0],[5.8894122,44.6899677,1424.0],[5.889321,44.6899448,1424.0],[5.8892459,44.6899181,1424.0],[5.88916,44.689899,1423.0],[5.889101,44.6898761,1423.0],[5.8890313,44.6898533,1423.0],[5.8889776,44.6898342,1423.0],[5.8889079,44.6898037,1423.0],[5.8888489,44.6897732,1423.0],[5.8887684,44.6897465,1423.0],[5.8886665,44.6897198,1423.0],[5.8885753,44.6896969,1423.0],[5.8884627,44.689674,1423.0],[5.88835,44.689674,1423.0],[5.8882052,44.6896664,1423.0],[5.8880711,44.6896511,1423.0],[5.8879316,44.6896244,1422.0],[5.8877599,44.6895977,1421.0],[5.8876204,44.6895749,1421.0],[5.8875024,44.6895482,1420.0],[5.8873469,44.6895062,1418.0],[5.8872074,44.6894643,1417.0],[5.8870679,44.6894261,1416.0],[5.8869553,44.6893804,1415.0],[5.8868694,44.6893308,1413.0],[5.8867782,44.6892659,1412.0],[5.8866978,44.6892011,1410.0],[5.8866012,44.689102,1408.0],[5.8864993,44.6890181,1407.0],[5.8863813,44.6889265,1406.0],[5.8863062,44.6888769,1405.0],[5.8862042,44.6888007,1403.0],[5.8860916,44.6887282,1402.0],[5.8860058,44.688671,1401.0],[5.8859199,44.68861,1400.0],[5.8858341,44.6885375,1399.0],[5.8857322,44.6884765,1398.0],[5.8856463,44.6884079,1396.0],[5.8855551,44.6883583,1395.0],[5.8854892,44.688321,1394.0],[5.8854126,44.6883059,1392.0],[5.8853212,44.6883461,1390.0],[5.8851847,44.6884668,1389.0],[5.8851528,44.6885146,1388.0],[5.8850831,44.6885985,1386.0],[5.8850402,44.6886596,1383.0],[5.8849919,44.6887015,1381.0],[5.8849436,44.6887549,1379.0],[5.8849007,44.6888197,1378.0],[5.8848578,44.6888846,1376.0],[5.8848149,44.6889608,1375.0],[5.8847773,44.6890295,1373.0],[5.8847344,44.6891134,1372.0],[5.8847129,44.6891897,1370.0],[5.8846968,44.6892659,1369.0],[5.8846754,44.6893422,1368.0],[5.8846378,44.6894071,1367.0],[5.8845842,44.6894604,1365.0],[5.8845359,44.6895062,1364.0],[5.8844393,44.6895596,1363.0],[5.8843535,44.6895863,1361.0],[5.8842838,44.6896092,1360.0],[5.8842087,44.6896359,1359.0],[5.8841014,44.6896626,1358.0],[5.8839995,44.6896855,1356.0],[5.8838922,44.6897236,1355.0],[5.8838117,44.6897388,1354.0],[5.8837473,44.6897617,1353.0],[5.8836776,44.6897732,1352.0],[5.8836025,44.6897808,1350.0],[5.883522,44.6897961,1349.0],[5.8834523,44.6898266,1348.0],[5.883404,44.6898609,1347.0],[5.8833611,44.6898914,1345.0],[5.8832806,44.689941,1344.0],[5.883227,44.6899906,1343.0],[5.8831787,44.6900401,1341.0],[5.8831465,44.6900706,1341.0],[5.8831143,44.690105,1339.0],[5.8830768,44.6901393,1338.0],[5.8830339,44.6901774,1337.0],[5.8830329,44.6901792,1336.0],[5.8830124,44.6902156,1335.0],[5.8830017,44.6902766,1335.0],[5.8830017,44.6903262,1334.0],[5.8830017,44.6903719,1332.0],[5.882991,44.6904177,1331.0],[5.8829641,44.6904558,1330.0],[5.8828837,44.690555,1328.0],[5.8828032,44.6906274,1327.0],[5.8827066,44.690738,1325.0],[5.8826369,44.6908219,1323.0],[5.8825833,44.690902,1321.0],[5.8824921,44.6910393,1319.0],[5.8824867,44.691108,1317.0],[5.8824599,44.6911766,1315.0],[5.8824438,44.6912605,1314.0],[5.8824384,44.6913368,1312.0],[5.8824277,44.6914054,1311.0],[5.8824062,44.6914741,1309.0],[5.8823794,44.6915465,1308.0],[5.8823633,44.6916113,1307.0],[5.8823633,44.6916914,1306.0],[5.8823633,44.6918058,1305.0],[5.8824116,44.6918745,1304.0],[5.8824706,44.6919469,1304.0],[5.8825243,44.6920041,1303.0],[5.8826101,44.6920766,1302.0],[5.8827013,44.6921147,1302.0],[5.8827925,44.6921491,1301.0],[5.8828837,44.6921719,1300.0],[5.882948,44.6922558,1299.0],[5.8829856,44.6923588,1298.0],[5.8830285,44.6924274,1297.0],[5.8830285,44.6924846,1296.0],[5.8830339,44.6925685,1295.0],[5.8830446,44.6926181,1294.0],[5.88305,44.6926868,1293.0],[5.88305,44.6927478,1291.0],[5.8830124,44.6928012,1290.0],[5.8829749,44.6928736,1289.0],[5.8829856,44.6929308,1289.0],[5.8830285,44.6929995,1288.0],[5.8830661,44.6930452,1288.0],[5.8831197,44.693091,1287.0],[5.883168,44.6931215,1286.0],[5.8832324,44.6931787,1285.0],[5.8832431,44.6932207,1284.0],[5.8832055,44.6932473,1283.0],[5.8830768,44.6932397,1282.0],[5.8829856,44.6932321,1280.0],[5.8828676,44.6932283,1279.0],[5.8827549,44.6932283,1277.0],[5.882653,44.6932283,1276.0],[5.8825886,44.6932397,1274.0],[5.8825082,44.6932626,1273.0],[5.882476,44.6933351,1272.0],[5.8824331,44.6934266,1272.0],[5.8824277,44.6935105,1272.0],[5.8824652,44.6935677,1273.0],[5.8825135,44.6936478,1273.0],[5.8826881,44.6937303,1274.0],[5.8828571,44.6938504,1274.0],[5.8830261,44.6939705,1275.0],[5.8830797,44.6940582,1276.0],[5.8830985,44.6942413,1278.0],[5.8831173,44.6944243,1279.0],[5.8832299,44.6946112,1281.0],[5.8833962,44.6947027,1283.0],[5.8835625,44.6947179,1285.0],[5.8837449,44.6946493,1287.0],[5.8838844,44.6945501,1290.0],[5.8840239,44.694451,1292.0],[5.8841553,44.6942927,1295.0],[5.8842867,44.6941345,1297.0],[5.8843887,44.6940239,1299.0],[5.8845603,44.6941269,1302.0],[5.8846622,44.6943137,1304.0],[5.8846944,44.6944052,1306.0],[5.8847964,44.6944014,1308.0],[5.8848178,44.6942718,1309.0],[5.8848446,44.6940906,1311.0],[5.8848715,44.6939095,1312.0],[5.884909,44.6937322,1314.0],[5.8849466,44.6935548,1315.0],[5.8850056,44.6934061,1317.0],[5.8851665,44.693593,1318.0],[5.8852416,44.6937417,1319.0],[5.8853167,44.6938904,1320.0],[5.8853972,44.6940105,1321.0],[5.8854776,44.6941307,1322.0],[5.8855205,44.694287,1324.0],[5.8855635,44.6944434,1325.0],[5.8856815,44.6946302,1326.0],[5.8858558,44.6947713,1328.0],[5.8860302,44.6949124,1330.0],[5.8861482,44.6950459,1331.0],[5.8862662,44.6951793,1333.0],[5.8863842,44.6953128,1335.0],[5.88647,44.6955073,1337.0],[5.8865559,44.6957018,1339.0],[5.8865773,44.6959229,1341.0],[5.8866578,44.6960526,1343.0],[5.8867383,44.6961822,1345.0],[5.8868724,44.6962394,1347.0],[5.8869904,44.6962051,1350.0],[5.8870548,44.6960602,1352.0],[5.887264,44.6959306,1353.0],[5.8873981,44.6959801,1355.0],[5.8874249,44.6961822,1357.0],[5.8875751,44.6962852,1359.0],[5.8877924,44.6963767,1361.0],[5.8880096,44.6964682,1363.0],[5.8881706,44.6965731,1364.0],[5.8883315,44.696678,1366.0],[5.8884978,44.6967314,1368.0],[5.8886641,44.6967847,1371.0],[5.8888626,44.6968839,1373.0],[5.8890181,44.6969754,1376.0],[5.8891737,44.6971508,1379.0],[5.8893293,44.6973262,1382.0],[5.8895036,44.6974692,1385.0],[5.889678,44.6976122,1389.0],[5.8898577,44.6977476,1392.0],[5.8900374,44.6978829,1395.0],[5.8901742,44.6979916,1398.0],[5.890311,44.6981003,1401.0],[5.8905148,44.6981664,1404.0],[5.8907187,44.6982325,1407.0],[5.8909225,44.6982986,1409.0],[5.8911478,44.6983787,1411.0],[5.8913731,44.6984587,1414.0],[5.8915341,44.6984816,1416.0],[5.891695,44.6985045,1417.0],[5.8919437,44.6985245,1419.0],[5.8919848,44.6985135,1421.0],[5.8920041,44.6984949,1422.0],[5.8920106,44.698475,1423.0],[5.8920001,44.6984419,1425.0],[5.8919898,44.6983656,1425.0],[5.8921548,44.6984415,1426.0],[5.8923197,44.6985173,1427.0],[5.8924852,44.6985671,1427.0],[5.8926681,44.6986118,1428.0],[5.8928961,44.6986473,1428.0],[5.8930978,44.6986655,1428.0],[5.8932996,44.6986836,1428.0],[5.8934754,44.6987123,1428.0],[5.8935803,44.6987384,1427.0],[5.8938566,44.698788,1427.0],[5.8941329,44.6988375,1426.0],[5.8944093,44.698887,1426.0],[5.8946856,44.6989365,1425.0],[5.8949442,44.6990199,1425.0],[5.8952028,44.6991032,1424.0],[5.8954614,44.6991865,1423.0],[5.895729,44.6992976,1423.0],[5.8959517,44.6993929,1423.0],[5.8961743,44.6994883,1423.0],[5.8963123,44.6995452,1422.0],[5.8964503,44.6996021,1422.0],[5.8966022,44.699681,1422.0],[5.8968022,44.699764,1422.0],[5.8969605,44.6998094,1422.0],[5.8971189,44.6998548,1422.0],[5.8973456,44.6999651,1422.0],[5.897569,44.7000412,1422.0],[5.89773,44.7000564,1421.0],[5.8978909,44.7000717,1421.0],[5.8981162,44.7001136,1421.0],[5.8983227,44.7001575,1420.0],[5.8985293,44.7002013,1420.0],[5.8987117,44.7002452,1420.0],[5.898894,44.700289,1420.0],[5.899063,44.700371,1419.0],[5.899232,44.700453,1419.0],[5.8994287,44.7005114,1419.0],[5.8996254,44.7005699,1418.0],[5.8997935,44.7006198,1418.0],[5.8998221,44.7006284,1417.0],[5.9000447,44.7006646,1417.0],[5.9002673,44.7007008,1416.0],[5.9004944,44.7007644,1415.0],[5.9007215,44.7008279,1414.0],[5.9009486,44.7008915,1413.0],[5.9011981,44.7009201,1412.0],[5.9014475,44.7009486,1411.0],[5.9016084,44.7009639,1409.0],[5.9017694,44.7009792,1408.0],[5.9020483,44.7010363,1407.0],[5.9023273,44.7010935,1405.0],[5.9024936,44.7011069,1403.0],[5.9026599,44.7011202,1402.0],[5.9028691,44.7010783,1400.0],[5.9030908,44.7010236,1398.0],[5.9033125,44.700969,1395.0],[5.9035343,44.7009143,1393.0],[5.9037542,44.7009315,1391.0],[5.9039741,44.7009486,1388.0],[5.9042263,44.7009868,1386.0],[5.9044784,44.7010249,1384.0],[5.9046793,44.7010416,1383.0],[5.9049153,44.70095,1383.0],[5.9049153,44.70095,1383.0],[5.9050548,44.7008166,1383.0],[5.9051943,44.7006831,1384.0],[5.9052318,44.7004696,1385.0],[5.9052694,44.7002561,1386.0],[5.9051514,44.7001798,1388.0],[5.9050065,44.7002828,1389.0],[5.9048617,44.7003857,1391.0],[5.9046865,44.7002739,1391.0],[5.9045112,44.700162,1392.0],[5.904336,44.7000502,1393.0],[5.9041622,44.699919,1393.0],[5.9039884,44.6997878,1394.0],[5.9038146,44.6996567,1395.0],[5.9036407,44.6995255,1395.0],[5.9034669,44.6993943,1396.0],[5.9033436,44.6992113,1396.0],[5.9032202,44.6990283,1397.0],[5.9030968,44.6988453,1397.0],[5.9029734,44.6986622,1398.0],[5.9027696,44.698525,1398.0],[5.9025657,44.6983877,1398.0],[5.9025067,44.698258,1399.0],[5.9024477,44.6981284,1399.0],[5.9023511,44.6979835,1399.0],[5.9022546,44.6978386,1400.0],[5.9020783,44.697673,1400.0],[5.9019021,44.6975074,1401.0],[5.9017258,44.6973418,1402.0],[5.9015495,44.6971762,1403.0],[5.9013733,44.6970106,1405.0],[5.901197,44.696845,1407.0],[5.9010208,44.6966794,1409.0],[5.9008491,44.6965406,1410.0],[5.9006774,44.6964018,1412.0],[5.9005058,44.696263,1413.0],[5.9003341,44.6961242,1415.0],[5.9001625,44.6959854,1417.0],[5.8999801,44.6959167,1418.0],[5.8997977,44.6958481,1420.0],[5.8996153,44.6957006,1421.0],[5.8994329,44.6955532,1423.0],[5.8992505,44.6954057,1424.0],[5.8990681,44.6952583,1425.0],[5.8988857,44.6951108,1427.0],[5.8987033,44.6949634,1429.0],[5.8985236,44.694795,1431.0],[5.8983439,44.6946265,1433.0],[5.8981642,44.6944581,1435.0],[5.8979845,44.6942897,1436.0],[5.8978048,44.6941213,1438.0],[5.8976251,44.6939528,1440.0],[5.8974132,44.6938623,1442.0],[5.8972013,44.6937717,1444.0],[5.8969894,44.6936811,1446.0],[5.8967775,44.6935906,1447.0],[5.8966114,44.693406,1449.0],[5.8964453,44.6932214,1450.0],[5.8962793,44.6930368,1452.0],[5.8961132,44.6928523,1453.0],[5.8959471,44.6926677,1454.0],[5.8958559,44.6926257,1455.0],[5.8957325,44.6925685,1456.0],[5.8955877,44.6925342,1457.0],[5.8954697,44.6924999,1457.0],[5.8954321,44.6924427,1457.0],[5.8953034,44.6924656,1457.0],[5.8951693,44.6924618,1457.0],[5.8950512,44.6924389,1457.0],[5.89496,44.6923893,1456.0],[5.8948259,44.6922711,1455.0],[5.8947026,44.6921109,1454.0],[5.8945738,44.6920003,1453.0],[5.894502,44.6919513,1453.0],[5.8942876,44.6919083,1452.0],[5.8943217,44.6917982,1451.0],[5.8943217,44.6916139,1451.0],[5.8943217,44.6914296,1451.0],[5.8943217,44.6912452,1450.0],[5.8943031,44.6910795,1450.0],[5.8942845,44.6909138,1450.0],[5.8942804,44.690772,1450.0],[5.8942762,44.6906302,1450.0],[5.8943003,44.6905332,1450.0],[5.8943034,44.6905196,1450.0],[5.8943223,44.6904218,1450.0],[5.8943274,44.6903983,1450.0],[5.8943264,44.6903037,1451.0],[5.8943016,44.6901908,1451.0],[5.8942096,44.6899856,1451.0],[5.8941176,44.6897803,1452.0],[5.8940492,44.6896533,1452.0],[5.8939808,44.6895263,1452.0],[5.8938898,44.6894277,1452.0],[5.8938607,44.6894006,1452.0],[5.8938116,44.6894532,1452.0],[5.8937345,44.6894021,1452.0],[5.8935994,44.6893299,1452.0],[5.8933763,44.6892272,1452.0],[5.8931531,44.6891245,1452.0],[5.8928828,44.6890403,1451.0],[5.8926124,44.688956,1451.0],[5.8923942,44.6888881,1451.0]
            ]
        }

