from django.conf import settings
from django.urls import path, re_path, register_converter
from mapentity.registry import registry

from geotrek.altimetry.urls import AltimetryEntityOptions
from geotrek.common.urls import LangConverter
from .models import Path, Trail
from .views import (
    PathGPXDetail, PathKMLDetail, TrailGPXDetail, TrailKMLDetail,
    MultiplePathDelete, TrekGeometry
)

register_converter(LangConverter, 'lang')

app_name = 'core'

urlpatterns = [
    re_path(r'^path/delete/(?P<pk>\d+(,\d+)+)/', MultiplePathDelete.as_view(), name="multiple_path_delete"),
    path('api/<lang:lang>/paths/<int:pk>/path_<slug:slug>.gpx', PathGPXDetail.as_view(),
         name="path_gpx_detail"),
    path('api/<lang:lang>/paths/<int:pk>/path_<slug:slug>.kml', PathKMLDetail.as_view(),
         name="path_kml_detail"),
    path('api/<lang:lang>/trails/<int:pk>/trail_<slug:slug>.gpx', TrailGPXDetail.as_view(),
         name="trail_gpx_detail"),
    path('api/<lang:lang>/trails/<int:pk>/trail_<slug:slug>.kml', TrailKMLDetail.as_view(),
         name="trail_kml_detail"),
    path('api/treks/geometry', TrekGeometry.as_view(), name="trek_geometry"),
]

urlpatterns += registry.register(Path, AltimetryEntityOptions, menu=(settings.PATH_MODEL_ENABLED and settings.TREKKING_TOPOLOGY_ENABLED))
urlpatterns += registry.register(Trail, menu=(settings.TRAIL_MODEL_ENABLED and settings.TREKKING_TOPOLOGY_ENABLED))
