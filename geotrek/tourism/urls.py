from django.conf import settings
from django.conf.urls import patterns, url

from mapentity import registry

from geotrek.common.urls import PublishableEntityOptions

from . import models
from . import views as tourism_views
from . import serializers as tourism_serializers


urlpatterns = patterns(
    '',
    url(r'^api/datasource/datasources.json$', tourism_views.DataSourceList.as_view(), name="datasource_list_json"),
    url(r'^api/datasource/datasource-(?P<pk>\d+).geojson$', tourism_views.DataSourceGeoJSON.as_view(), name="datasource_geojson"),
    url(r'^api/treks/(?P<pk>\d+)/information_desks.geojson$', tourism_views.TrekInformationDeskViewSet.as_view({'get': 'list'}), name="trek_information_desk_geojson"),
)


class TouristicContentEntityOptions(PublishableEntityOptions):
    document_public_view = tourism_views.TouristicContentDocumentPublic

    def get_serializer(self):
        return tourism_serializers.TouristicContentSerializer

    def get_queryset(self):
        return self.model.objects.existing()

if settings.TOURISM_ENABLED:
    urlpatterns += registry.register(models.TouristicContent, TouristicContentEntityOptions)


class TouristicEventEntityOptions(PublishableEntityOptions):
    document_public_view = tourism_views.TouristicEventDocumentPublic

    def get_serializer(self):
        return tourism_serializers.TouristicEventSerializer

    def get_queryset(self):
        return self.model.objects.existing()

if settings.TOURISM_ENABLED:
    urlpatterns += registry.register(models.TouristicEvent, TouristicEventEntityOptions)
