from django.views.generic.list import ListView
from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny
from mapentity import views as mapentity_views

from geotrek.feedback import models as feedback_models
from geotrek.feedback import serializers as feedback_serializers


class ReportLayer(mapentity_views.MapEntityLayer):
    model = feedback_models.Report
    properties = ['name']


class ReportList(mapentity_views.MapEntityList):
    model = feedback_models.Report
    columns = ['id', 'name', 'email', 'category', 'status', 'date_insert']


class ReportFormatList(mapentity_views.MapEntityFormat, ReportList):
    columns = [
        'id', 'name', 'email', 'comment', 'category', 'status',
        'date_insert', 'date_update',
    ]


class CategoryList(mapentity_views.JSONResponseMixin, ListView):
    model = feedback_models.ReportCategory

    def dispatch(self, *args, **kwargs):
        return super(CategoryList, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        return [{'id': c.id,
                 'label': c.category} for c in self.object_list]


class ReportViewSet(mapentity_views.MapEntityViewSet):
    """Disable permissions requirement"""
    model = feedback_models.Report
    serializer_class = feedback_serializers.ReportSerializer

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def report(self, request, lang=None):
        return super(ReportViewSet, self).create(request)
