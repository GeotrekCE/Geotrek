import logging
from collections import defaultdict
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.gis.db.models.functions import Transform
from django.core.cache import caches
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

        def get_edge_id_by_nodes(node1, node2):
            for value in node1[1].values():
                if value in node2[1].values():
                    return value
            return None

        def get_edge_weight(edge_id):
            edge = self.edges.get(str(edge_id))
            if edge is None:
                return None
            return edge.get('length')
        
        array = []
        for node1 in self.nodes.items():
            key1, value1 = node1
            row = []
            for node2 in self.nodes.items():
                key2, _ = node2
                if key1 == key2:
                    # If it's the same node, the weight is 0
                    row.append(0)
                elif key2 in value1.keys():
                    # If the nodes are linked by a single edge, the weight is
                    # the edge length
                    edge_id = get_edge_id_by_nodes(node1, node2)
                    edge_weight = get_edge_weight(edge_id)
                    if edge_weight is not None:
                        row.append(edge_weight)
                else:
                    # If the nodes are not directly linked, the weight is 0
                    row.append(0)
            array.append(row)

        return np.array(array)

    def get_start_and_end_node_ids(self):
        # For each step, get its associated edge:
        step_edges = [self.edges.get(str(x.get('edge_id'))) for x in self.steps]

        # For each of these edges, get its starting and ending node
        bound_nodes = [(x.get('nodes_id')[0], x.get('nodes_id')[1]) for x in step_edges]

        path_starting_node = bound_nodes[0][0]
        path_ending_node = bound_nodes[-1][-1]
        return path_starting_node, path_ending_node

    def post(self, request):
        try:
            params = json.loads(request.body.decode())
            self.steps = params['steps']
            graph = params['graph']
            self.nodes = graph['nodes']
            self.edges = graph['edges']
        except:
            print("TrekGeometry POST: incorrect parameters")
            # TODO: Bad request

        cs_graph = self.get_cs_graph()
        matrix = csr_matrix(cs_graph)

        start_node, end_node = self.get_start_and_end_node_ids()
        print("start_node, end_node", start_node, end_node)

        result = dijkstra(matrix, return_predecessors=True, indices=2,
                          directed=False)
        print(result)

        return JsonResponse({
            'graph': params['graph'],
            'steps': params['steps'],
        })
