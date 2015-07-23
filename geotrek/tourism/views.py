import logging
from itertools import chain

import requests
from requests.exceptions import RequestException
import geojson
from django.conf import settings
from django.http import Http404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from mapentity.views import (JSONResponseMixin, MapEntityCreate,
                             MapEntityUpdate, MapEntityLayer, MapEntityList,
                             MapEntityDetail, MapEntityDelete, MapEntityViewSet,
                             MapEntityFormat, MapEntityDocument)
from rest_framework import permissions as rest_permissions, viewsets
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from geotrek.authent.decorators import same_structure_required
from geotrek.common.utils import plain_text_preserve_linebreaks
from geotrek.common.views import DocumentPublic
from geotrek.tourism.models import DataSource, InformationDesk
from geotrek.trekking.models import Trek
from geotrek.trekking.serializers import POISerializer

from .filters import TouristicContentFilterSet, TouristicEventFilterSet
from .forms import TouristicContentForm, TouristicEventForm
from .helpers import post_process
from .models import TouristicContent, TouristicEvent, TouristicContentCategory
from .serializers import (TouristicContentSerializer, TouristicEventSerializer,
                          InformationDeskSerializer)


logger = logging.getLogger(__name__)


class DataSourceList(JSONResponseMixin, ListView):
    queryset = DataSource.objects.order_by('id')

    def get_context_data(self):
        results = []
        for ds in self.get_queryset():
            results.append({
                'id': ds.id,
                'title': ds.title,
                'url': ds.url,
                'type': ds.type,
                'pictogram_url': ds.pictogram.url,
                'geojson_url': ds.get_absolute_url(),
                'targets': ds.targets
            })
        return results

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DataSourceList, self).dispatch(*args, **kwargs)


class DataSourceGeoJSON(JSONResponseMixin, DetailView):
    model = DataSource

    def get_context_data(self, *args, **kwargs):
        source = self.get_object()

        default_result = geojson.FeatureCollection(features=[])

        try:
            response = requests.get(source.url)
        except RequestException as e:
            logger.error(u"Source '%s' cannot be downloaded" % source.url)
            logger.exception(e)
            return default_result

        try:
            return post_process(source, self.request.LANGUAGE_CODE, response.text)
        except (ValueError, AssertionError) as e:
            return default_result

    @method_decorator(login_required)
    @method_decorator(cache_page(settings.CACHE_TIMEOUT_TOURISM_DATASOURCES, cache="fat"))
    def dispatch(self, *args, **kwargs):
        return super(DataSourceGeoJSON, self).dispatch(*args, **kwargs)


class TouristicContentLayer(MapEntityLayer):
    queryset = TouristicContent.objects.existing()
    properties = ['name']


class TouristicContentList(MapEntityList):
    queryset = TouristicContent.objects.existing()
    filterform = TouristicContentFilterSet
    columns = ['id', 'name', 'category']

    @property
    def categories_list(self):
        used = TouristicContent.objects.values_list('category__pk')
        return TouristicContentCategory.objects.filter(pk__in=used)


class TouristicContentFormatList(MapEntityFormat, TouristicContentList):
    columns = [
        'id', 'eid', 'name', 'category', 'type1', 'type2', 'description_teaser',
        'description', 'themes', 'contact', 'email', 'website', 'practical_info',
        'review', 'published', 'publication_date', 'source',
        'structure', 'date_insert', 'date_update',
        'cities', 'districts', 'areas',
    ]


class TouristicContentDetail(MapEntityDetail):
    queryset = TouristicContent.objects.existing()

    def get_context_data(self, *args, **kwargs):
        context = super(TouristicContentDetail, self).get_context_data(*args, **kwargs)
        context['can_edit'] = self.get_object().same_structure(self.request.user)
        return context


class TouristicContentCreate(MapEntityCreate):
    model = TouristicContent
    form_class = TouristicContentForm

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        initial = super(TouristicContentCreate, self).get_initial()
        try:
            category = int(self.request.GET.get('category'))
            initial['category'] = category
        except (TypeError, ValueError):
            pass
        return initial


class TouristicContentUpdate(MapEntityUpdate):
    queryset = TouristicContent.objects.existing()
    form_class = TouristicContentForm

    @same_structure_required('tourism:touristiccontent_detail')
    def dispatch(self, *args, **kwargs):
        return super(TouristicContentUpdate, self).dispatch(*args, **kwargs)


class TouristicContentDelete(MapEntityDelete):
    model = TouristicContent

    @same_structure_required('tourism:touristiccontent_detail')
    def dispatch(self, *args, **kwargs):
        return super(TouristicContentDelete, self).dispatch(*args, **kwargs)


class TouristicContentDocument(MapEntityDocument):
    queryset = TouristicContent.objects.existing()


class TouristicContentDocumentPublic(DocumentPublic):
    queryset = TouristicContent.objects.existing()

    def get_context_data(self, **kwargs):
        context = super(TouristicContentDocumentPublic, self).get_context_data(**kwargs)
        content = self.get_object()

        context['headerimage_ratio'] = settings.EXPORT_HEADER_IMAGE_SIZE['touristiccontent']

        # Replace HTML text with plain text
        for attr in ['description', 'description_teaser', 'contact', 'practical_info']:
            setattr(content, attr, plain_text_preserve_linebreaks(getattr(content, attr)))

        context['object'] = context['content'] = content

        return context


class TouristicEventLayer(MapEntityLayer):
    queryset = TouristicEvent.objects.existing()
    properties = ['name']


class TouristicEventList(MapEntityList):
    queryset = TouristicEvent.objects.existing()
    filterform = TouristicEventFilterSet
    columns = ['id', 'name', 'type']


class TouristicEventFormatList(MapEntityFormat, TouristicEventList):
    columns = [
        'id', 'eid', 'name', 'type', 'description_teaser', 'description', 'themes',
        'begin_date', 'end_date', 'duration', 'meeting_point', 'meeting_time',
        'contact', 'email', 'website', 'organizer', 'speaker', 'accessibility',
        'participant_number', 'booking', 'target_audience', 'practical_info',
        'structure', 'date_insert', 'date_update', 'source',
        'review', 'published', 'publication_date',
        'cities', 'districts', 'areas',
    ]


class TouristicEventDetail(MapEntityDetail):
    queryset = TouristicEvent.objects.existing()

    def get_context_data(self, *args, **kwargs):
        context = super(TouristicEventDetail, self).get_context_data(*args, **kwargs)
        context['can_edit'] = self.get_object().same_structure(self.request.user)
        return context


class TouristicEventCreate(MapEntityCreate):
    model = TouristicEvent
    form_class = TouristicEventForm


class TouristicEventUpdate(MapEntityUpdate):
    queryset = TouristicEvent.objects.existing()
    form_class = TouristicEventForm

    @same_structure_required('tourism:touristicevent_detail')
    def dispatch(self, *args, **kwargs):
        return super(TouristicEventUpdate, self).dispatch(*args, **kwargs)


class TouristicEventDelete(MapEntityDelete):
    model = TouristicEvent

    @same_structure_required('tourism:touristicevent_detail')
    def dispatch(self, *args, **kwargs):
        return super(TouristicEventDelete, self).dispatch(*args, **kwargs)


class TouristicEventDocument(MapEntityDocument):
    queryset = TouristicEvent.objects.existing()


class TouristicEventDocumentPublic(DocumentPublic):
    queryset = TouristicEvent.objects.existing()

    def get_context_data(self, **kwargs):
        context = super(TouristicEventDocumentPublic, self).get_context_data(**kwargs)
        event = self.get_object()

        context['headerimage_ratio'] = settings.EXPORT_HEADER_IMAGE_SIZE['touristicevent']

        # Replace HTML text with plain text
        for attr in ['description', 'description_teaser', 'contact', 'booking', 'practical_info']:
            setattr(event, attr, plain_text_preserve_linebreaks(getattr(event, attr)))

        context['object'] = context['event'] = event

        return context


class TouristicContentViewSet(MapEntityViewSet):
    model = TouristicContent
    serializer_class = TouristicContentSerializer
    permission_classes = [rest_permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        qs = TouristicContent.objects.existing()
        qs = qs.filter(published=True)
        qs = qs.transform(settings.API_SRID, field_name='geom')
        return qs


class TouristicEventViewSet(MapEntityViewSet):
    model = TouristicEvent
    serializer_class = TouristicEventSerializer
    permission_classes = [rest_permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        qs = TouristicEvent.objects.existing()
        qs = qs.filter(published=True)
        qs = qs.transform(settings.API_SRID, field_name='geom')
        return qs


class TrekInformationDeskViewSet(viewsets.ModelViewSet):
    model = InformationDesk
    permission_classes = [rest_permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_serializer_class(self):
        class Serializer(InformationDeskSerializer, GeoFeatureModelSerializer):
            pass
        return Serializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        try:
            trek = Trek.objects.existing().get(pk=pk, published=True)
        except Trek.DoesNotExist:
            raise Http404
        return trek.information_desks.all().transform(settings.API_SRID, field_name='geom')


class TrekTouristicContentAndPOIViewSet(viewsets.ModelViewSet):
    model = TouristicContent
    permission_classes = [rest_permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_serializer_class(self):
        class Serializer(POISerializer, GeoFeatureModelSerializer):
            pass
        return Serializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        try:
            trek = Trek.objects.existing().get(pk=pk, published=True)
        except Trek.DoesNotExist:
            raise Http404
        qs1 = trek.touristic_contents.filter(published=True).transform(settings.API_SRID, field_name='geom')
        qs2 = trek.pois.filter(published=True).transform(settings.API_SRID, field_name='geom')
        return chain(qs1, qs2)
