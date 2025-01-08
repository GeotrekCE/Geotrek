import os
import smtplib

from crispy_forms.helper import FormHelper
from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.db.models import CharField, F, Value
from django.db.models.functions import Concat
from django.urls.base import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from mapentity import views as mapentity_views
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated

from geotrek.common.mixins.views import CustomColumnsMixin
from geotrek.common.viewsets import GeotrekMapentityViewSet

from . import models as feedback_models
from . import serializers as feedback_serializers
from .filters import ReportFilterSet, ReportEmailFilterSet
from .forms import ReportForm

import logging

logger = logging.getLogger(__name__)


class ReportList(CustomColumnsMixin, mapentity_views.MapEntityList):
    queryset = (
        feedback_models.Report.objects.existing()
        .select_related(
            "activity", "category", "problem_magnitude", "status", "related_trek", "assigned_user"
        )
        .prefetch_related("attachments")
    )
    model = feedback_models.Report
    filterform = ReportEmailFilterSet
    mandatory_columns = ['id', 'eid', 'activity']
    default_extra_columns = ['category', 'status', 'date_update']
    searchable_columns = ['id', 'eid']

    def get_queryset(self):
        qs = super().get_queryset()  # Filtered by FilterSet
        if settings.SURICATE_WORKFLOW_ENABLED and not settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION") and not (self.request.user.is_superuser or self.request.user.pk in list(
                feedback_models.WorkflowManager.objects.values_list('user', flat=True))):
            qs = qs.filter(assigned_user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Remove email from available filters in workflow mode for supervisors
        if settings.SURICATE_WORKFLOW_ENABLED and not (self.request.user.is_superuser or self.request.user.pk in list(
                feedback_models.WorkflowManager.objects.values_list('user', flat=True))):
            self._filterform = ReportFilterSet()
            self._filterform.helper = FormHelper()
            self._filterform.helper.field_class = 'form-control-sm'
            self._filterform.helper.submit = None
        context['filterform'] = self._filterform
        return context


class ReportFormatList(mapentity_views.MapEntityFormat, ReportList):
    mandatory_columns = ['id', 'email']
    default_extra_columns = [
        'activity', 'comment', 'category',
        'problem_magnitude', 'status', 'related_trek',
        'date_insert', 'date_update', 'assigned_user',
        'provider'
    ]

    def get_columns(self):
        """ Override columns to remove email if user is noy superuser nor in workflow managers """
        columns = super().get_columns()
        if not self.request.user.is_superuser:
            if (settings.SURICATE_WORKFLOW_ENABLED
                    and not feedback_models.WorkflowManager.objects.filter(user_id=self.request.user.pk).exists()):
                columns.remove('email')
        return columns


class ReportCreate(mapentity_views.MapEntityCreate):
    model = feedback_models.Report
    form_class = ReportForm

    def get_success_url(self):
        if settings.SURICATE_WORKFLOW_ENABLED:
            return reverse('feedback:report_list')
        return super().get_success_url()


class ReportUpdate(mapentity_views.MapEntityUpdate):
    queryset = feedback_models.Report.objects.existing().select_related(
        "activity", "category", "problem_magnitude", "status", "related_trek"
    ).prefetch_related("attachments")
    form_class = ReportForm


class ReportViewSet(GeotrekMapentityViewSet):
    model = feedback_models.Report
    serializer_class = feedback_serializers.ReportSerializer
    geojson_serializer_class = feedback_serializers.ReportGeojsonSerializer
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    filterset_class = ReportEmailFilterSet
    mapentity_list_class = ReportList

    def get_queryset(self):
        qs = self.model.objects.existing().select_related("status")
        if not self.request.user.is_superuser:
            if (settings.SURICATE_WORKFLOW_ENABLED
                    and not settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION")
                    and not feedback_models.WorkflowManager.objects.filter(user_id=self.request.user.pk).exists()):
                qs = qs.filter(assigned_user=self.request.user)

        if self.format_kwarg == 'geojson':
            number = 'eid' if settings.SURICATE_WORKFLOW_ENABLED else 'id'
            qs = qs.annotate(name=Concat(Value(_("Report")), Value(" "), F(number), output_field=CharField()),
                             api_geom=Transform('geom', settings.API_SRID))
            qs = qs.only('id', 'status')
            return qs

        qs = qs.select_related("activity", "category", "problem_magnitude", "related_trek")\
               .prefetch_related("attachments")
        return qs

    def view_cache_key(self):
        """ Used by the ``view_cache_response_content`` decorator. """
        language = get_language()
        geojson_lookup = None
        latest_saved = feedback_models.Report.latest_updated()
        if latest_saved:
            geojson_lookup = '%s_report_%s_%s_geojson_layer' % (
                language,
                latest_saved.isoformat(),
                self.request.user.pk if settings.SURICATE_WORKFLOW_ENABLED else ''
            )
        return geojson_lookup


class ReportAPIViewSet(APIViewSet):
    queryset = feedback_models.Report.objects.existing()\
                              .select_related("activity", "category", "problem_magnitude", "status", "related_trek")\
                              .prefetch_related("attachments")
    parser_classes = [FormParser, MultiPartParser]
    serializer_class = feedback_serializers.ReportAPISerializer
    geojson_serializer_class = feedback_serializers.ReportAPIGeojsonSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            "activity", "category", "problem_magnitude", "status", "related_trek"
        )

    @action(detail=False, methods=["post"])
    def report(self, request, lang=None):
        response = super().create(request)
        creator, created = get_user_model().objects.get_or_create(
            username="feedback", defaults={"is_active": False}
        )
        for file in request._request.FILES.values():
            attachment = Attachment(
                filetype=FileType.objects.get_or_create(type=settings.REPORT_FILETYPE)[
                    0
                ],
                content_type=ContentType.objects.get_for_model(feedback_models.Report),
                object_id=response.data.get("id"),
                creator=creator,
                attachment_file=file,
            )
            name, extension = os.path.splitext(file.name)
            try:
                attachment.full_clean()  # Check that file extension and mimetypes are allowed
            except ValidationError as e:
                logger.error(f"Invalid attachment {name}{extension} for report {response.data.get('id')} : " + str(e))
            else:
                try:
                    # Reencode file to bitmap then back to jpeg lfor safety
                    if not os.path.exists(f"{settings.TMP_DIR}/report_file/"):
                        os.mkdir(f"{settings.TMP_DIR}/report_file/")
                    tmp_bmp_path = os.path.join(f"{settings.TMP_DIR}/report_file/", f"{name}.bmp")
                    tmp_jpeg_path = os.path.join(f"{settings.TMP_DIR}/report_file/", f"{name}.jpeg")
                    Image.open(file).save(tmp_bmp_path)
                    Image.open(tmp_bmp_path).save(tmp_jpeg_path)
                    with open(tmp_jpeg_path, 'rb') as converted_file:
                        attachment.attachment_file = File(converted_file, name=f"{name}.jpeg")
                        attachment.save()
                    os.remove(tmp_bmp_path)
                    os.remove(tmp_jpeg_path)
                except Exception as e:
                    logger.error(f"Failed to convert attachment {name}{extension} for report {response.data.get('id')}: " + str(e))

        if settings.SEND_REPORT_ACK and response.status_code == 201:
            try:
                send_mail(
                    _("Geotrek : Signal a mistake"),
                    _(
                        """Hello,

We acknowledge receipt of your feedback, thank you for your interest in Geotrek.

Best regards,

The Geotrek Team
http://www.geotrek.fr"""
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [request.data.get("email")],
                )
            except (smtplib.SMTPException, ConnectionError, OSError) as error:
                logger.error("Error while sending feedback acknowledgment email: %s", error)
        return response
