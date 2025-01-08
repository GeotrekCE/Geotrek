import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.detail import BaseDetailView
from mapentity.views import (MapEntityCreate, MapEntityUpdate, MapEntityList, MapEntityDetail,
                             MapEntityDelete, MapEntityFormat, LastModifiedMixin)

from geotrek.authent.decorators import same_structure_required
from geotrek.common.mixins.views import CustomColumnsMixin
from geotrek.common.permissions import PublicOrReadPermMixin
from geotrek.common.viewsets import GeotrekMapentityViewSet
from .filters import SensitiveAreaFilterSet
from .forms import SensitiveAreaForm, RegulatorySensitiveAreaForm
from .models import SensitiveArea, Species, SportPractice
from .serializers import SensitiveAreaSerializer, SensitiveAreaGeojsonSerializer


logger = logging.getLogger(__name__)


class SensitiveAreaList(CustomColumnsMixin, MapEntityList):
    queryset = SensitiveArea.objects.existing()
    filterform = SensitiveAreaFilterSet
    mandatory_columns = ['id', 'name']
    default_extra_columns = ['species','category']


class SensitiveAreaFormatList(MapEntityFormat, SensitiveAreaList):
    mandatory_columns = ['id']
    default_extra_columns = [
        'species', 'published', 'description', 'contact', 'radius', 'pretty_period', 'pretty_practices',
    ]


class SensitiveAreaDetail(MapEntityDetail):
    queryset = SensitiveArea.objects.existing()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['can_edit'] = self.object.same_structure(self.request.user)
        return context


class SensitiveAreaRadiiMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        species = Species.objects.filter(category=Species.SPECIES)
        context['radii'] = json.dumps({
            str(s.id): settings.SENSITIVITY_DEFAULT_RADIUS if s.radius is None else s.radius for s in species
        })
        return context


class SensitiveAreaCreate(SensitiveAreaRadiiMixin, MapEntityCreate):
    model = SensitiveArea

    def get_form_class(self):
        if self.request.GET.get('category') == str(Species.REGULATORY):
            return RegulatorySensitiveAreaForm
        return SensitiveAreaForm


class SensitiveAreaUpdate(SensitiveAreaRadiiMixin, MapEntityUpdate):
    queryset = SensitiveArea.objects.existing()

    def get_form_class(self):
        if self.object.species.category == Species.REGULATORY:
            return RegulatorySensitiveAreaForm
        return SensitiveAreaForm

    @same_structure_required('sensitivity:sensitivearea_detail')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class SensitiveAreaDelete(MapEntityDelete):
    model = SensitiveArea

    @same_structure_required('sensitivity:sensitivearea_detail')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class SensitiveAreaViewSet(GeotrekMapentityViewSet):
    model = SensitiveArea
    serializer_class = SensitiveAreaSerializer
    geojson_serializer_class = SensitiveAreaGeojsonSerializer
    filterset_class = SensitiveAreaFilterSet
    mapentity_list_class = SensitiveAreaList

    def get_queryset(self):
        qs = self.model.objects.existing().select_related('species')
        if self.format_kwarg == 'geojson':
            qs = qs.annotate(api_geom=Transform('geom', settings.API_SRID))
            qs = qs.only('id', 'species')
        return qs


class SensitiveAreaKMLDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = SensitiveArea.objects.existing()

    def render_to_response(self, context):
        area = self.get_object()
        response = HttpResponse(area.kml(),
                                content_type='application/vnd.google-earth.kml+xml')
        return response


class SensitiveAreaOpenAirDetail(LastModifiedMixin, PublicOrReadPermMixin, BaseDetailView):
    queryset = SensitiveArea.objects.existing()

    def render_to_response(self, context):
        area = self.get_object()
        file_header = """* This file has been produced from GeoTrek sensitivity (https://geotrek.fr/) module from website {scheme}://{domain}
* Using pyopenair library (https://github.com/lpoaura/pyopenair)
* This file was created on:  {timestamp}\n\n""".format(scheme=self.request.scheme, domain=self.request.headers['host'], timestamp=datetime.now())
        is_aerial = area.species.practices.filter(name__in=settings.SENSITIVITY_OPENAIR_SPORT_PRACTICES).exists()
        if is_aerial and area.openair():
            result = file_header + area.openair()
            response = HttpResponse(result, content_type='application/octet-stream; charset=UTF-8')
            response['Content-Disposition'] = 'inline; filename=sensitivearea_openair_' + str(area.id) + '.txt'
            return response
        else:
            message = _('This is not an aerial area')
            response = HttpResponse(message, content_type='text/plain; charset=UTF-8')

        return response


class SensitiveAreaOpenAirList(PublicOrReadPermMixin, ListView):

    def get_queryset(self):
        aerial_practice = SportPractice.objects.filter(name__in=settings.SENSITIVITY_OPENAIR_SPORT_PRACTICES)
        return SensitiveArea.objects.existing().filter(
            species__practices__in=aerial_practice, published=True
        ).select_related('species')

    def render_to_response(self, context):
        areas = self.get_queryset()
        file_header = """* This file has been produced from GeoTrek sensitivity (https://geotrek.fr/) module from website {scheme}://{domain}
* Using pyopenair library (https://github.com/lpoaura/pyopenair)
* This file was created on:  {timestamp}\n\n""".format(scheme=self.request.scheme, domain=self.request.headers['host'], timestamp=datetime.now())
        airspace_list = [a.openair() for a in areas if a.openair()]
        airspace_core = '\n\n'.join(airspace_list)
        airspace_file = file_header + airspace_core
        response = HttpResponse(airspace_file, content_type='application/octet-stream; charset=UTF-8')
        response['Content-Disposition'] = 'inline; filename=sensitivearea_openair.txt'
        return response
