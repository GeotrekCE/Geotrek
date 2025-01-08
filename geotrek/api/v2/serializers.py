import json

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import MultiLineString, Point, GEOSGeometry
from django.db.models import F
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from drf_dynamic_fields import DynamicFieldsMixin
from easy_thumbnails.alias import aliases
from easy_thumbnails.engine import NoSourceGenerator
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer

from geotrek.flatpages.models import MenuItem
from modeltranslation.utils import build_localized_fieldname
from PIL.Image import DecompressionBombError
from rest_framework import serializers, serializers as rest_serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework_gis import serializers as geo_serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from geotrek.api.v2.filters import get_published_filter_expression
from geotrek.api.v2.functions import Length3D
from geotrek.api.v2.mixins import PDFSerializerMixin, PublishedRelatedObjectsSerializerMixin
from geotrek.api.v2.utils import build_url, get_translation_or_dict, is_published
from geotrek.authent import models as authent_models
from geotrek.common import models as common_models
from geotrek.common.utils import simplify_coords

if 'geotrek.core' in settings.INSTALLED_APPS:
    from geotrek.core import models as core_models
if 'geotrek.feedback' in settings.INSTALLED_APPS:
    from geotrek.feedback import models as feedback_models
if 'geotrek.tourism' in settings.INSTALLED_APPS:
    from geotrek.tourism import models as tourism_models
if 'geotrek.trekking' in settings.INSTALLED_APPS:
    from geotrek.trekking import models as trekking_models
if 'geotrek.sensitivity' in settings.INSTALLED_APPS:
    from geotrek.sensitivity import models as sensitivity_models
if 'geotrek.zoning' in settings.INSTALLED_APPS:
    from geotrek.zoning import models as zoning_models
if 'geotrek.outdoor' in settings.INSTALLED_APPS:
    from geotrek.outdoor import models as outdoor_models
if 'geotrek.flatpages' in settings.INSTALLED_APPS:
    from geotrek.flatpages import models as flatpages_models
if 'geotrek.infrastructure' in settings.INSTALLED_APPS:
    from geotrek.infrastructure import models as infrastructure_models
if 'geotrek.signage' in settings.INSTALLED_APPS:
    from geotrek.signage import models as signage_models


class BaseGeoJSONSerializer(geo_serializers.GeoFeatureModelSerializer):
    """
    Mixin used to serialize geojson
    """

    def to_representation(self, instance):
        """Round bbox coordinates"""
        feature = super().to_representation(instance)
        feature['bbox'] = simplify_coords(feature['bbox'])
        return feature

    class Meta:
        geo_field = 'geometry'
        auto_bbox = True


class TimeStampedSerializer(serializers.ModelSerializer):
    create_datetime = serializers.DateTimeField(source='date_insert')
    update_datetime = serializers.DateTimeField(source='date_update')

    class Meta:
        fields = ('create_datetime', 'update_datetime')


def override_serializer(format_output, base_serializer_class):
    """
    Override Serializer switch output format and dimension data
    """
    if format_output == 'geojson':
        class GeneratedGeoSerializer(BaseGeoJSONSerializer,
                                     base_serializer_class):
            class Meta(BaseGeoJSONSerializer.Meta,
                       base_serializer_class.Meta):
                pass

        final_class = GeneratedGeoSerializer
    else:
        final_class = base_serializer_class

    return final_class


if 'geotrek.trekking' in settings.INSTALLED_APPS:
    class NetworkSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('network', self, obj)

        class Meta:
            model = trekking_models.TrekNetwork
            fields = ('id', 'label', 'pictogram')

    class PracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.Practice
            fields = ('id', 'name', 'order', 'pictogram',)

    class TrekRatingScaleSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.RatingScale
            fields = ('id', 'name', 'practice')

    class TrekRatingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = trekking_models.Rating
            fields = ('id', 'name', 'description', 'scale', 'order', 'color')

    class TrekDifficultySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('difficulty', self, obj)

        class Meta:
            model = trekking_models.DifficultyLevel
            fields = ('id', 'cirkwi_level', 'label', 'pictogram')

    class RouteSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        route = serializers.SerializerMethodField()

        def get_route(self, obj):
            return get_translation_or_dict('route', self, obj)

        class Meta:
            model = trekking_models.Route
            fields = ('id', 'pictogram', 'route')

    class WebLinkCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.WebLinkCategory
            fields = ('label', 'id', 'pictogram')

    class WebLinkSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        category = WebLinkCategorySerializer()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.WebLink
            fields = ('name', 'url', 'category')

    class ServiceTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.ServiceType
            fields = ('id', 'name', 'practices', 'pictogram')

    class ServiceSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)

        class Meta:
            model = trekking_models.Service
            fields = ('id', 'eid', 'geometry', 'provider', 'structure', 'type', 'uuid')


class ReservationSystemSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = common_models.ReservationSystem
        fields = ('id', 'name')


class StructureSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = authent_models.Structure
        fields = (
            'id', 'name'
        )


class TargetPortalSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    facebook_image_url = serializers.SerializerMethodField()

    def get_title(self, obj):
        return get_translation_or_dict('title', self, obj)

    def get_description(self, obj):
        return get_translation_or_dict('description', self, obj)

    def get_facebook_image_url(self, obj):
        return build_url(self, obj.facebook_image_url) if obj.facebook_image_url else ""

    class Meta:
        model = common_models.TargetPortal
        fields = (
            'id', 'description', 'facebook_id',
            'facebook_image_height', 'facebook_image_url',
            'facebook_image_width', 'name', 'title', 'website'
        )


class TouristicOrganismSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = tourism_models.TouristicEventOrganizer
        fields = (
            'id',
        )


class OrganismSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(source='organism')

    class Meta:
        model = common_models.Organism
        fields = (
            'id', 'name'
        )


class RecordSourceSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = common_models.RecordSource
        fields = ('id', 'name', 'pictogram', 'website')


class AttachmentsSerializerMixin(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    license = serializers.SlugRelatedField(
        read_only=True,
        slug_field='label'
    )

    def get_attachment_file(self, obj):
        return obj.attachment_file

    def get_thumbnail(self, obj):
        thumbnailer = get_thumbnailer(self.get_attachment_file(obj))
        if hasattr(obj, 'is_image') and not obj.is_image:
            return ""
        try:
            thumbnail = thumbnailer.get_thumbnail(aliases.get('apiv2'))
        except (IOError, InvalidImageFormatError, DecompressionBombError, NoSourceGenerator):
            return ""
        thumbnail.author = obj.author
        thumbnail.legend = obj.legend
        return build_url(self, thumbnail.url)

    def get_url(self, obj):
        if obj.attachment_file:
            return build_url(self, obj.attachment_file.url)
        if obj.attachment_video:
            return obj.attachment_video
        if obj.attachment_link:
            return obj.attachment_link
        return ""

    class Meta:
        model = common_models.Attachment
        fields = (
            'author', 'license', 'thumbnail', 'legend', 'title', 'url', 'uuid'
        )


class FileTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = common_models.FileType
        fields = ('id', 'structure', 'type')


class AttachmentSerializer(DynamicFieldsMixin, AttachmentsSerializerMixin):
    type = serializers.SerializerMethodField()
    backend = serializers.SerializerMethodField()
    filetype = FileTypeSerializer(many=False)

    def get_type(self, obj):
        if obj.is_image or obj.attachment_link:
            return "image"
        if obj.attachment_video != '':
            return "video"
        return "file"

    def get_backend(self, obj):
        if obj.attachment_video != '':
            return type(obj).__name__.replace('Backend', '')
        return ""

    class Meta:
        model = common_models.Attachment
        fields = (
            'backend', 'type', 'filetype',
        ) + AttachmentsSerializerMixin.Meta.fields


class AttachmentAccessibilitySerializer(DynamicFieldsMixin, AttachmentsSerializerMixin):
    def get_attachment_file(self, obj):
        return obj.attachment_accessibility_file

    def get_url(self, obj):
        return build_url(self, obj.attachment_accessibility_file.url)

    class Meta:
        model = common_models.AccessibilityAttachment
        fields = (
            'info_accessibility',
        ) + AttachmentsSerializerMixin.Meta.fields


class LabelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    advice = serializers.SerializerMethodField()

    def get_name(self, obj):
        return get_translation_or_dict('name', self, obj)

    def get_advice(self, obj):
        return get_translation_or_dict('advice', self, obj)

    class Meta:
        model = common_models.Label
        fields = ('id', 'advice', 'filter', 'name', 'pictogram')


class HDViewPointSerializer(TimeStampedSerializer):
    geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
    picture_tiles_url = serializers.SerializerMethodField()
    annotations = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    metadata_url = serializers.SerializerMethodField()
    trek = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()
    poi = serializers.SerializerMethodField()
    license = serializers.SlugRelatedField(
        read_only=True,
        slug_field='label'
    )

    def get_picture_tiles_url(self, obj):
        return build_url(self, obj.get_generic_picture_tile_url())

    def get_thumbnail_url(self, obj):
        return build_url(self, obj.thumbnail_url)

    def get_metadata_url(self, obj):
        return build_url(self, obj.metadata_url)

    def get_trek(self, obj):
        related_obj = obj.content_object
        if isinstance(related_obj, trekking_models.Trek):
            return {'uuid': related_obj.uuid, 'id': related_obj.id}
        return None

    def get_site(self, obj):
        related_obj = obj.content_object
        if isinstance(related_obj, outdoor_models.Site):
            return {'uuid': related_obj.uuid, 'id': related_obj.id}
        return None

    def get_poi(self, obj):
        related_obj = obj.content_object
        if isinstance(related_obj, trekking_models.POI):
            return {'uuid': related_obj.uuid, 'id': related_obj.id}
        return None

    def get_annotations(self, obj):
        annotations = obj.annotations
        annotations_categories = obj.annotations_categories
        for feature in annotations.get("features", []):
            feat_id = feature["properties"]["annotationId"]
            if str(feat_id) in annotations_categories.keys():
                feature["properties"]['category'] = int(annotations_categories[str(feat_id)])
            else:
                feature["properties"]['category'] = None
        return annotations

    class Meta(TimeStampedSerializer.Meta):
        model = common_models.HDViewPoint
        fields = TimeStampedSerializer.Meta.fields + (
            'id', 'annotations', 'author', 'geometry', 'legend', 'license', 'metadata_url',
            'picture_tiles_url', 'poi', 'title', 'site', 'trek', 'thumbnail_url', 'uuid'
        )


if 'geotrek.tourism' in settings.INSTALLED_APPS:
    class LabelAccessibilitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = tourism_models.LabelAccessibility
            fields = ('id', 'label', 'pictogram')

    class TouristicContentCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        types = serializers.SerializerMethodField()
        label = serializers.SerializerMethodField()

        class Meta:
            model = tourism_models.TouristicContentCategory
            fields = ('id', 'label', 'order', 'pictogram', 'types')

        def get_types(self, obj):
            request = self.context['request']
            portals = request.GET.get('portals')
            if portals:
                portals = portals.split(',')
            language = request.GET.get('language')
            return [{
                'id': obj.id * 100 + i,
                'label': get_translation_or_dict('type{}_label'.format(i), self, obj),
                'values': [{
                    'id': t.id,
                    'label': get_translation_or_dict('label', self, t),
                    'pictogram': t.pictogram.url if t.pictogram else None,
                } for t in obj.types.has_content_published_not_deleted_in_list(i, obj.pk, portals, language)]
            } for i in (1, 2)]

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

    class TouristicEventTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        type = serializers.SerializerMethodField()

        def get_type(self, obj):
            return get_translation_or_dict('type', self, obj)

        class Meta:
            model = tourism_models.TouristicEventType
            fields = ('id', 'pictogram', 'type')

    class TouristicModelSerializer(PDFSerializerMixin, DynamicFieldsMixin, TimeStampedSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        accessibility = serializers.SerializerMethodField()
        external_id = serializers.CharField(source='eid')
        cities = serializers.SerializerMethodField()
        districts = serializers.SerializerMethodField()
        name = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        description_teaser = serializers.SerializerMethodField()
        practical_info = serializers.SerializerMethodField()
        pdf = serializers.SerializerMethodField('get_pdf_url')

        def get_accessibility(self, obj):
            return get_translation_or_dict('accessibility', self, obj)

        def get_practical_info(self, obj):
            return get_translation_or_dict('practical_info', self, obj)

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def get_districts(self, obj):
            return [district.pk for district in obj.published_districts]

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_description_teaser(self, obj):
            return get_translation_or_dict('description_teaser', self, obj)

    class TouristicContentSerializer(TouristicModelSerializer):
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        departure_city = serializers.SerializerMethodField()
        types = serializers.SerializerMethodField()
        url = HyperlinkedIdentityField(view_name='apiv2:touristiccontent-detail')

        class Meta(TimeStampedSerializer.Meta):
            model = tourism_models.TouristicContent
            fields = TimeStampedSerializer.Meta.fields + (
                'id', 'accessibility', 'attachments', 'approved', 'category', 'description',
                'description_teaser', 'departure_city', 'geometry', 'label_accessibility',
                'practical_info', 'url', 'cities', 'districts',
                'external_id', 'name', 'pdf', 'portal', 'provider', 'published',
                'source', 'structure', 'themes',
                'types', 'contact', 'email',
                'website', 'reservation_system', 'reservation_id', 'uuid'
            )

        def get_types(self, obj):
            return {
                obj.category.id * 100 + i: [
                    t.id for t in getattr(obj, 'type{}'.format(i)).all()
                ] for i in (1, 2)
            }

        def get_departure_city(self, obj):
            city = zoning_models.City.objects.all().filter(geom__contains=obj.geom).first()
            return city.code if city else None

    class TouristicEventSerializer(TouristicModelSerializer):
        organizers = serializers.SerializerMethodField()
        organizer = serializers.SerializerMethodField()
        organizers_id = serializers.PrimaryKeyRelatedField(many=True, source='organizers', read_only=True)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        url = HyperlinkedIdentityField(view_name='apiv2:touristicevent-detail')
        begin_date = serializers.DateField()
        end_date = serializers.SerializerMethodField()
        type = serializers.SerializerMethodField()
        cancellation_reason = serializers.SerializerMethodField()
        place = serializers.SlugRelatedField(
            read_only=True,
            slug_field='name'
        )
        meeting_time = serializers.ReadOnlyField(
            source='start_time',
            help_text=_("This field is deprecated and will be removed in next releases. Please start using '%(field)s'") % {"field": "start_time"}
        )
        participant_number = serializers.SerializerMethodField(
            help_text=_("This field is deprecated and will be removed in next releases. Please start using '%(field)s'") % {"field": "capacity"}
        )

        def get_cancellation_reason(self, obj):
            if not obj.cancellation_reason:
                return None
            return get_translation_or_dict('label', self, obj.cancellation_reason)

        def get_type(self, obj):
            obj_type = obj.type
            if obj_type:
                return obj_type.pk
            return None

        def get_participant_number(self, obj):
            return str(obj.capacity)

        def get_end_date(self, obj):
            return obj.end_date or obj.begin_date

        def get_organizers(self, obj):
            return ", ".join(
                map(lambda org: org.label, obj.organizers.all())
            )

        # for retrocompatibility of API
        get_organizer = get_organizers

        class Meta(TimeStampedSerializer.Meta):
            model = tourism_models.TouristicEvent
            fields = TimeStampedSerializer.Meta.fields + (
                'id', 'accessibility', 'approved', 'attachments', 'begin_date', 'bookable',
                'booking', 'cancellation_reason', 'cancelled', 'capacity', 'cities',
                'contact', 'description', 'description_teaser', 'districts', 'duration',
                'email', 'end_date', 'end_time', 'external_id', 'geometry', 'meeting_point',
                'meeting_time', 'name', 'organizers', 'organizer', 'organizers_id', 'participant_number', 'pdf', 'place',
                'portal', 'practical_info', 'provider', 'published', 'source', 'speaker',
                'start_time', 'structure', 'target_audience', 'themes', 'type',
                'url', 'uuid', 'website', 'price'
            )

    class TouristicEventPlaceSerializer(serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)

        class Meta:
            model = tourism_models.TouristicEventPlace
            fields = ('id', 'geometry', 'name')

    class TouristicEventOrganizerSerializer(serializers.ModelSerializer):
        class Meta:
            model = tourism_models.TouristicEventOrganizer
            fields = ('id', 'label')

    class InformationDeskTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = tourism_models.InformationDeskType
            fields = ('id', 'label', 'pictogram')

    class InformationDeskSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        accessibility = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        name = serializers.SerializerMethodField()
        photo_url = serializers.SerializerMethodField()
        type = InformationDeskTypeSerializer()

        def get_accessibility(self, obj):
            return get_translation_or_dict('accessibility', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_photo_url(self, obj):
            return build_url(self, obj.photo_url) if obj.photo_url else ""

        class Meta:
            model = tourism_models.InformationDesk
            geo_field = 'geom'
            fields = (
                'id', 'accessibility', 'description', 'email', 'label_accessibility', 'latitude', 'longitude',
                'municipality', 'name', 'phone', 'photo_url', 'uuid',
                'postal_code', 'provider', 'street', 'type', 'website'
            )


if 'geotrek.core' in settings.INSTALLED_APPS:
    class PathSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:path-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        length_2d = serializers.FloatField(source="length_2d_display")
        length_3d = serializers.SerializerMethodField()

        def get_length_3d(self, obj):
            return round(obj.length_3d_m, 1)

        class Meta:
            model = core_models.Path
            fields = (
                'arrival', 'comfort', 'comments', 'departure', 'geometry', 'id', 'length_2d',
                'length_3d', 'name', 'networks', 'provider', 'source', 'stake', 'url', 'usages', 'uuid'
            )


if 'geotrek.trekking' in settings.INSTALLED_APPS:
    class TrekSerializer(PDFSerializerMixin, DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:trek-detail')
        published = serializers.SerializerMethodField()
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        length_2d = serializers.FloatField(source='length_2d_display')
        length_3d = serializers.SerializerMethodField()
        name = serializers.SerializerMethodField()
        access = serializers.SerializerMethodField()
        accessibility_advice = serializers.SerializerMethodField()
        accessibility_covering = serializers.SerializerMethodField()
        accessibility_exposure = serializers.SerializerMethodField()
        accessibility_signage = serializers.SerializerMethodField()
        accessibility_slope = serializers.SerializerMethodField()
        accessibility_width = serializers.SerializerMethodField()
        ambiance = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        description_teaser = serializers.SerializerMethodField()
        departure = serializers.SerializerMethodField()
        disabled_infrastructure = serializers.SerializerMethodField()
        departure_geom = serializers.SerializerMethodField()
        arrival = serializers.SerializerMethodField()
        external_id = serializers.CharField(source='eid')
        second_external_id = serializers.CharField(source='eid2')
        create_datetime = serializers.DateTimeField(source='topo_object.date_insert')
        update_datetime = serializers.DateTimeField(source='topo_object.date_update')
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        attachments_accessibility = AttachmentAccessibilitySerializer(many=True)
        gear = serializers.SerializerMethodField()
        gpx = serializers.SerializerMethodField('get_gpx_url')
        kml = serializers.SerializerMethodField('get_kml_url')
        pdf = serializers.SerializerMethodField('get_pdf_url')
        advice = serializers.SerializerMethodField()
        advised_parking = serializers.SerializerMethodField()
        parking_location = serializers.SerializerMethodField()
        ratings_description = serializers.SerializerMethodField()
        children = serializers.ReadOnlyField(source='children_id')
        parents = serializers.ReadOnlyField(source='parents_id')
        public_transport = serializers.SerializerMethodField()
        elevation_area_url = serializers.SerializerMethodField()
        elevation_svg_url = serializers.SerializerMethodField()
        altimetric_profile = serializers.SerializerMethodField('get_altimetric_profile_url')
        points_reference = serializers.SerializerMethodField()
        previous = serializers.ReadOnlyField(source='previous_id')
        next = serializers.ReadOnlyField(source='next_id')
        cities = serializers.SerializerMethodField()
        districts = serializers.SerializerMethodField()
        departure_city = serializers.SerializerMethodField()
        labels = serializers.SerializerMethodField()
        web_links = WebLinkSerializer(many=True)
        view_points = HDViewPointSerializer(many=True)

        def get_gear(self, obj):
            return get_translation_or_dict('gear', self, obj)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return self._replace_image_paths_with_urls(get_translation_or_dict('description', self, obj))

        def get_access(self, obj):
            return get_translation_or_dict('access', self, obj)

        def get_accessibility_advice(self, obj):
            return get_translation_or_dict('accessibility_advice', self, obj)

        def get_accessibility_covering(self, obj):
            return get_translation_or_dict('accessibility_covering', self, obj)

        def get_accessibility_exposure(self, obj):
            return get_translation_or_dict('accessibility_exposure', self, obj)

        def get_accessibility_signage(self, obj):
            return get_translation_or_dict('accessibility_signage', self, obj)

        def get_accessibility_slope(self, obj):
            return get_translation_or_dict('accessibility_slope', self, obj)

        def get_accessibility_width(self, obj):
            return get_translation_or_dict('accessibility_width', self, obj)

        def get_ambiance(self, obj):
            return self._replace_image_paths_with_urls(get_translation_or_dict('ambiance', self, obj))

        def get_disabled_infrastructure(self, obj):
            return get_translation_or_dict('accessibility_infrastructure', self, obj)

        def get_departure(self, obj):
            return get_translation_or_dict('departure', self, obj)

        def get_first_point(self, geom):
            if isinstance(geom, Point):
                return geom
            if isinstance(geom, MultiLineString):
                return Point(geom[0][0])
            return Point(geom[0])

        def get_departure_geom(self, obj):
            return self.get_first_point(obj.geom3d_transformed)[:2]

        def get_arrival(self, obj):
            return get_translation_or_dict('arrival', self, obj)

        def get_description_teaser(self, obj):
            return self._replace_image_paths_with_urls(get_translation_or_dict('description_teaser', self, obj))

        def get_length_3d(self, obj):
            return round(obj.length_3d_m, 1)

        def get_gpx_url(self, obj):
            return build_url(self, reverse('trekking:trek_gpx_detail', kwargs={'lang': get_language(), 'pk': obj.pk, 'slug': obj.slug}))

        def get_kml_url(self, obj):
            return build_url(self, reverse('trekking:trek_kml_detail', kwargs={'lang': get_language(), 'pk': obj.pk, 'slug': obj.slug}))

        def get_advice(self, obj):
            return get_translation_or_dict('advice', self, obj)

        def get_advised_parking(self, obj):
            return get_translation_or_dict('advised_parking', self, obj)

        def get_parking_location(self, obj):
            if not obj.parking_location:
                return None
            point = obj.parking_location.transform(settings.API_SRID, clone=True)
            return [round(point.x, 7), round(point.y, 7)]

        def get_ratings_description(self, obj):
            return get_translation_or_dict('ratings_description', self, obj)

        def get_public_transport(self, obj):
            return get_translation_or_dict('public_transport', self, obj)

        def get_elevation_area_url(self, obj):
            return build_url(self, reverse('apiv2:trek-dem', args=(obj.pk,)))

        def get_elevation_svg_url(self, obj):
            return build_url(self, reverse('apiv2:trek-profile', args=(obj.pk,)) + f"?language={get_language()}&format=svg")

        def get_altimetric_profile_url(self, obj):
            return build_url(self, reverse('apiv2:trek-profile', args=(obj.pk,)))

        def get_points_reference(self, obj):
            if not obj.points_reference:
                return None
            geojson = obj.points_reference.transform(settings.API_SRID, clone=True).geojson
            return json.loads(geojson)

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def get_districts(self, obj):
            return [district.pk for district in obj.published_districts]

        def get_labels(self, obj):
            return [label.pk for label in obj.published_labels]

        def get_departure_city(self, obj):
            geom = self.get_first_point(obj.geom)
            city = zoning_models.City.objects.all().filter(geom__contains=geom).first()
            return city.code if city else None

        def _replace_image_paths_with_urls(self, data):
            def replace(html_content):
                if not html_content:
                    return html_content
                soup = BeautifulSoup(html_content, features="html.parser")
                imgs = soup.find_all('img')
                for img in imgs:
                    if img.attrs['src'][0] == '/':
                        img['src'] = self.context.get("request").build_absolute_uri(img.attrs["src"])
                return str(soup)

            try:
                for k, v in data.items():
                    data[k] = replace(v)
            except AttributeError:
                data = replace(data)

            return data

        class Meta:
            model = trekking_models.Trek
            fields = (
                'id', 'access', 'accessibilities', 'accessibility_advice', 'accessibility_covering',
                'accessibility_exposure', 'accessibility_level', 'accessibility_signage', 'accessibility_slope',
                'accessibility_width', 'advice', 'advised_parking', 'altimetric_profile', 'ambiance', 'arrival',
                'ascent', 'attachments', 'attachments_accessibility', 'children', 'cities', 'create_datetime',
                'departure', 'departure_city', 'departure_geom', 'descent',
                'description', 'description_teaser', 'difficulty', 'districts',
                'disabled_infrastructure', 'duration', 'elevation_area_url',
                'elevation_svg_url', 'external_id', 'gear', 'geometry', 'gpx',
                'information_desks', 'kml', 'labels', 'length_2d', 'length_3d',
                'max_elevation', 'min_elevation', 'name', 'networks', 'next',
                'parents', 'parking_location', 'pdf', 'points_reference',
                'portal', 'practice', 'provider', 'ratings', 'ratings_description', 'previous', 'public_transport',
                'published', 'reservation_system', 'reservation_id', 'route', 'second_external_id',
                'source', 'structure', 'themes', 'update_datetime', 'url', 'uuid', 'view_points', 'web_links'
            )

    class TourSerializer(TrekSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:tour-detail')
        count_children = serializers.SerializerMethodField()
        steps = serializers.SerializerMethodField()

        def get_count_children(self, obj):
            return obj.count_children

        def get_steps(self, obj):
            qs = obj.children \
                .select_related('topo_object', 'difficulty') \
                .prefetch_related('topo_object__aggregations', 'themes', 'networks', 'attachments') \
                .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID),
                          length_3d_m=Length3D('geom_3d'))
            FinalClass = override_serializer(self.context.get('request').GET.get('format'),
                                             TrekSerializer)
            return FinalClass(qs, many=True, context=self.context).data

        class Meta(TrekSerializer.Meta):
            fields = TrekSerializer.Meta.fields + ('count_children', 'steps')

    class POITypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.POIType
            fields = ('id', 'label', 'pictogram')

    class POISerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:poi-detail')
        type_label = serializers.SerializerMethodField()
        type_pictogram = serializers.FileField(source='type.pictogram')
        name = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        external_id = serializers.CharField(source='eid')
        published = serializers.SerializerMethodField()
        create_datetime = serializers.DateTimeField(source='topo_object.date_insert')
        update_datetime = serializers.DateTimeField(source='topo_object.date_update')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        view_points = HDViewPointSerializer(many=True)

        def get_type_label(self, obj):
            return get_translation_or_dict('label', self, obj.type)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = trekking_models.POI
            fields = (
                'id', 'description', 'external_id',
                'geometry', 'name', 'attachments', 'provider', 'published', 'structure',
                'type', 'type_label', 'type_pictogram', 'url', 'uuid',
                'create_datetime', 'update_datetime', 'view_points'
            )

    class ThemeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.Theme
            fields = ('id', 'label', 'pictogram')

    class AnnotationCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = common_models.AnnotationCategory
            fields = ('id', 'label', 'pictogram')

    class AccessibilitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.Accessibility
            fields = ('id', 'name', 'pictogram')

    class AccessibilityLevelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.AccessibilityLevel
            fields = ('id', 'name')

if 'geotrek.sensitivity' in settings.INSTALLED_APPS:

    class RuleSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = sensitivity_models.Rule
            fields = ('id', 'code', 'name', 'pictogram', 'description', 'url')

    class SensitiveAreaSerializer(DynamicFieldsMixin, TimeStampedSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:sensitivearea-detail')
        name = serializers.CharField(source='area_name')
        elevation = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        period = serializers.SerializerMethodField()
        practices = serializers.PrimaryKeyRelatedField(many=True, source='species.practices', read_only=True)
        info_url = serializers.URLField(source='species.url')
        published = serializers.BooleanField()
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        species_id = serializers.SerializerMethodField()
        kml_url = serializers.SerializerMethodField()
        openair_url = serializers.SerializerMethodField(read_only=True)
        rules = RuleSerializer(many=True)
        attachments = AttachmentSerializer(many=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_period(self, obj):
            return [getattr(obj.species, 'period{:02}'.format(p)) for p in range(1, 13)]

        def get_elevation(self, obj):
            return obj.species.radius

        def get_species_id(self, obj):
            if obj.species.category == sensitivity_models.Species.SPECIES:
                return obj.species_id
            return None

        def get_kml_url(self, obj):
            url = reverse('sensitivity:sensitivearea_kml_detail', kwargs={'lang': get_language(), 'pk': obj.pk})
            return build_url(self, url)

        def get_openair_url(self, obj):
            is_aerial = obj.species.practices.filter(name__in=settings.SENSITIVITY_OPENAIR_SPORT_PRACTICES).exists()
            if is_aerial:
                url = reverse('sensitivity:sensitivearea_openair_detail', kwargs={'lang': get_language(), 'pk': obj.pk})
                return self.context['request'].build_absolute_uri(url)
            else:
                return None

        class Meta(TimeStampedSerializer.Meta):
            model = sensitivity_models.SensitiveArea
            fields = TimeStampedSerializer.Meta.fields + (
                'id', 'contact', 'description', 'elevation',
                'geometry', 'info_url', 'kml_url', 'openair_url', 'name', 'period',
                'practices', 'published', 'species_id', 'provider', 'structure',
                'url', 'attachments', 'rules'
            )

    class BubbleSensitiveAreaSerializer(SensitiveAreaSerializer):
        radius = serializers.SerializerMethodField()

        def get_radius(self, obj):
            if obj.species.category == sensitivity_models.Species.SPECIES and obj.geom.geom_typeid == 0:
                return obj.species.radius
            else:
                return None

        class Meta:
            model = SensitiveAreaSerializer.Meta.model
            fields = SensitiveAreaSerializer.Meta.fields + ('radius', )

    class SportPracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = sensitivity_models.SportPractice
            fields = (
                'id', 'name'
            )

    class SpeciesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        period01 = serializers.BooleanField(read_only=True)
        period02 = serializers.BooleanField(read_only=True)
        period03 = serializers.BooleanField(read_only=True)
        period04 = serializers.BooleanField(read_only=True)
        period05 = serializers.BooleanField(read_only=True)
        period06 = serializers.BooleanField(read_only=True)
        period07 = serializers.BooleanField(read_only=True)
        period08 = serializers.BooleanField(read_only=True)
        period09 = serializers.BooleanField(read_only=True)
        period10 = serializers.BooleanField(read_only=True)
        period11 = serializers.BooleanField(read_only=True)
        period12 = serializers.BooleanField(read_only=True)
        url = serializers.URLField(read_only=True)
        radius = serializers.IntegerField(read_only=True)
        practices = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_practices(self, obj):
            return obj.practices.values_list('id', flat=True)

        class Meta:
            model = sensitivity_models.Species
            fields = (
                'id', 'name', 'period01', 'period02', 'period03',
                'period04', 'period05', 'period06', 'period07',
                'period08', 'period09', 'period10', 'period11',
                'period12', 'practices', 'radius', 'url'
            )


if 'geotrek.zoning' in settings.INSTALLED_APPS:
    class CitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom", precision=7)
        id = serializers.ReadOnlyField(source='code')

        class Meta:
            model = zoning_models.City
            fields = ('id', 'geometry', 'name', 'published')

    class DistrictsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom", precision=7)

        class Meta:
            model = zoning_models.District
            fields = ('id', 'geometry', 'name', 'published')


if 'geotrek.outdoor' in settings.INSTALLED_APPS:
    class OutdoorRatingScaleSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.RatingScale
            fields = ('id', 'name', 'practice')

    class OutdoorRatingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = outdoor_models.Rating
            fields = ('id', 'name', 'description', 'scale', 'order', 'color')

    class OutdoorPracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.Practice
            fields = ('id', 'name', 'sector', 'pictogram')

    class SiteTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.SiteType
            fields = ('id', 'name', 'practice')

    class CourseTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.CourseType
            fields = ('id', 'name', 'practice')

    class SectorSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.Practice
            fields = ('id', 'name')

    class SiteSerializer(PDFSerializerMixin, DynamicFieldsMixin, PublishedRelatedObjectsSerializerMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        accessibility = serializers.SerializerMethodField()
        ambiance = serializers.SerializerMethodField()
        advice = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        description_teaser = serializers.SerializerMethodField()
        published = serializers.SerializerMethodField()
        period = serializers.SerializerMethodField()
        url = HyperlinkedIdentityField(view_name='apiv2:site-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        sector = serializers.SerializerMethodField()
        courses = serializers.SerializerMethodField()
        courses_uuids = serializers.SerializerMethodField()
        children = serializers.SerializerMethodField()
        children_uuids = serializers.SerializerMethodField()
        parent = serializers.SerializerMethodField()
        parent_uuid = serializers.SerializerMethodField()
        pdf = serializers.SerializerMethodField('get_pdf_url')
        cities = serializers.SerializerMethodField()
        districts = serializers.SerializerMethodField()
        labels = serializers.SerializerMethodField()
        web_links = WebLinkSerializer(many=True)
        view_points = HDViewPointSerializer(many=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_accessibility(self, obj):
            return get_translation_or_dict('accessibility', self, obj)

        def get_advice(self, obj):
            return get_translation_or_dict('advice', self, obj)

        def get_ambiance(self, obj):
            return get_translation_or_dict('ambiance', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_description_teaser(self, obj):
            return get_translation_or_dict('description_teaser', self, obj)

        def get_period(self, obj):
            return get_translation_or_dict('period', self, obj)

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def get_districts(self, obj):
            return [district.pk for district in obj.published_districts]

        def get_labels(self, obj):
            return [label.pk for label in obj.published_labels]

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_courses(self, obj):
            return self.get_values_on_published_related_objects(obj.children_courses.all(), 'pk')

        def get_courses_uuids(self, obj):
            return self.get_values_on_published_related_objects(obj.children_courses.all(), 'uuid')

        def get_parent(self, obj):
            return self.get_value_on_published_related_object(obj.parent, 'pk')

        def get_parent_uuid(self, obj):
            return self.get_value_on_published_related_object(obj.parent, 'uuid')

        def get_children(self, obj):
            return self.get_values_on_published_related_objects(obj.get_children(), 'pk')

        def get_children_uuids(self, obj):
            return self.get_values_on_published_related_objects(obj.get_children(), 'uuid')

        def get_sector(self, obj):
            if obj.practice and obj.practice.sector:
                return obj.practice.sector_id
            return None

        class Meta:
            model = outdoor_models.Site
            fields = (
                'id', 'accessibility', 'advice', 'ambiance', 'attachments', 'cities', 'children', 'children_uuids', 'description',
                'description_teaser', 'districts', 'eid', 'geometry', 'information_desks', 'labels', 'managers',
                'name', 'orientation', 'pdf', 'period', 'parent', 'parent_uuid', 'portal', 'practice', 'provider',
                'ratings', 'sector', 'source', 'structure', 'themes', 'view_points', 'published',
                'type', 'url', 'uuid', 'courses', 'courses_uuids', 'web_links', 'wind',
            )

    class CourseSerializer(PDFSerializerMixin, DynamicFieldsMixin, PublishedRelatedObjectsSerializerMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        advice = serializers.SerializerMethodField()
        description = serializers.SerializerMethodField()
        url = HyperlinkedIdentityField(view_name='apiv2:course-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        children = serializers.SerializerMethodField()
        parents = serializers.SerializerMethodField()
        parents_uuids = serializers.SerializerMethodField()
        published = serializers.SerializerMethodField()
        children_uuids = serializers.SerializerMethodField()
        accessibility = serializers.SerializerMethodField()
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        equipment = serializers.SerializerMethodField()
        gear = serializers.SerializerMethodField()
        ratings_description = serializers.SerializerMethodField()
        sites = serializers.SerializerMethodField()
        sites_uuids = serializers.SerializerMethodField()
        points_reference = serializers.SerializerMethodField()
        pdf = serializers.SerializerMethodField('get_pdf_url')
        cities = serializers.SerializerMethodField()
        districts = serializers.SerializerMethodField()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_advice(self, obj):
            return get_translation_or_dict('advice', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_accessibility(self, obj):
            return get_translation_or_dict('accessibility', self, obj)

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def get_districts(self, obj):
            return [district.pk for district in obj.published_districts]

        def get_equipment(self, obj):
            return get_translation_or_dict('equipment', self, obj)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_gear(self, obj):
            return get_translation_or_dict('gear', self, obj)

        def get_ratings_description(self, obj):
            return get_translation_or_dict('ratings_description', self, obj)

        def get_values_on_published_related_ordered_course(self, ordered_course_queryset, related_course, field):
            """
            Retrieve dict of values for `field` on objects from `ordered_course_queryset` only if they are published according to requested language
            """
            request = self.context['request']
            language = request.GET.get('language')
            if language:
                published_by_lang = f"{related_course}__{build_localized_fieldname('published', language)}"
                all_values = ordered_course_queryset.filter(**{published_by_lang: True}).values_list(f"{related_course}__{field}", flat=True)
                return list(all_values)
            else:
                all_values = []
                for item in ordered_course_queryset:
                    related_object = getattr(item, related_course)
                    if getattr(related_object, "any_published"):
                        all_values.append(getattr(related_object, field))
            return all_values

        def get_sites(self, obj):
            return self.get_values_on_published_related_objects(obj.parent_sites.all(), 'pk')

        def get_children(self, obj):
            return self.get_values_on_published_related_ordered_course(obj.course_children.order_by('order'), 'child', 'pk')

        def get_parents(self, obj):
            return self.get_values_on_published_related_ordered_course(obj.course_parents.order_by('order'), 'parent', 'pk')

        def get_sites_uuids(self, obj):
            return self.get_values_on_published_related_objects(obj.parent_sites.all(), 'uuid')

        def get_children_uuids(self, obj):
            return self.get_values_on_published_related_ordered_course(obj.course_children.order_by('order'), 'child', 'uuid')

        def get_parents_uuids(self, obj):
            return self.get_values_on_published_related_ordered_course(obj.course_parents.order_by('order'), 'parent', 'uuid')

        def get_points_reference(self, obj):
            if not obj.points_reference:
                return None
            geojson = obj.points_reference.transform(settings.API_SRID, clone=True).geojson
            return json.loads(geojson)

        class Meta:
            model = outdoor_models.Course
            fields = (
                'id', 'accessibility', 'advice', 'attachments', 'children', 'children_uuids', 'cities', 'description', 'districts', 'duration', 'eid',
                'equipment', 'gear', 'geometry', 'height', 'length', 'max_elevation', 'min_elevation', 'name', 'parents',
                'parents_uuids', 'pdf', 'points_reference', 'published', 'provider', 'ratings', 'ratings_description',
                'sites', 'sites_uuids', 'structure', 'type', 'url', 'uuid'
            )

if 'geotrek.feedback' in settings.INSTALLED_APPS:
    class ReportStatusSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportStatus
            fields = ('color', 'id', 'label', 'identifier')

    class ReportCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportCategory
            fields = ('id', 'label')

    class ReportActivitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportActivity
            fields = ('id', 'label')

    class ReportProblemMagnitudeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField()

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportProblemMagnitude
            fields = ('id', 'label')


if 'geotrek.flatpages' in settings.INSTALLED_APPS:

    class FlatPageSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        title = serializers.SerializerMethodField()
        content = serializers.SerializerMethodField()
        published = serializers.SerializerMethodField()
        attachments = AttachmentSerializer(many=True)
        children = serializers.SerializerMethodField()
        parent = serializers.SerializerMethodField()

        class Meta:
            model = flatpages_models.FlatPage
            fields = (
                'id',
                'title',
                'content',
                'source',
                'portals',
                'published',
                'attachments',
                'children',
                'parent',
            )

        def get_title(self, obj):
            return get_translation_or_dict('title', self, obj)

        def get_content(self, obj):
            return get_translation_or_dict('content', self, obj)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_children(self, obj):
            """Returns the filtered (published, portals) list of children page IDs"""
            children = obj.get_children()

            language = self.context["request"].query_params.get("language")
            expr = get_published_filter_expression(flatpages_models.FlatPage, language)
            children = children.filter(expr)

            portals = self.context["request"].query_params.get("portals")
            if portals:
                children = children.filter(portals__in=portals.split(","))

            return children.values_list('id', flat=True).all()

        def get_parent(self, obj):
            """Returns the parent page ID if it exists and is visible (published, portals)"""
            parent = obj.get_parent()
            if not parent:
                return None

            language = self.context["request"].query_params.get("language")
            if not is_published(parent, language):
                return None

            portals = self.context["request"].query_params.get("portals")
            if portals:
                portals = map(lambda x: int(x), portals.split(","))
                for portal in parent.portals.all():
                    if portal.id in portals:
                        break
                else:
                    return None

            return parent.id

    class MenuItemSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        title = serializers.SerializerMethodField()
        link_url = serializers.SerializerMethodField()
        published = serializers.SerializerMethodField()
        page_title = serializers.SerializerMethodField()
        attachments = AttachmentSerializer(many=True)

        class Meta:
            model = flatpages_models.MenuItem
            fields = (
                'id',
                'title',
                'target_type',
                'link_url',
                'page',
                'portals',
                'published',
                'page_title',
                'open_in_new_tab',
                'pictogram',
                'attachments',
            )

        def get_title(self, obj):
            return get_translation_or_dict('title', self, obj)

        def get_link_url(self, obj):
            return get_translation_or_dict('link_url', self, obj)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_page_title(self, obj):
            if not obj.page:
                return None
            return get_translation_or_dict('title', self, obj.page)

    class MenuItemDetailsSerializer(MenuItemSerializer):
        children = serializers.SerializerMethodField()
        parent = serializers.SerializerMethodField()

        class Meta(MenuItemSerializer.Meta):
            fields = MenuItemSerializer.Meta.fields + (
                'children',
                'parent',
            )

        def get_children(self, obj):
            language = self._context["request"].GET.get('language', 'all')
            return (
                obj.get_children()
                .filter(get_published_filter_expression(MenuItem, language))
                .values_list('id', flat=True).all()
            )

        def get_parent(self, obj):
            parent = obj.get_parent()

            if not parent:
                return None

            language = self._context["request"].GET.get('language', 'all')
            try:
                published_parent = (
                    MenuItem.objects
                    .filter(get_published_filter_expression(MenuItem, language))
                    .get(pk=parent.id)
                )
            except MenuItem.DoesNotExist:
                return None

            return published_parent.id


if "geotrek.infrastructure" in settings.INSTALLED_APPS:

    class InfrastructureTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        type = serializers.SerializerMethodField()

        def get_type(self, obj):
            type_label = infrastructure_models.INFRASTRUCTURE_TYPES.for_value(obj.type).display
            return _(type_label)

        class Meta:
            model = infrastructure_models.InfrastructureType
            fields = ('id', 'label', 'pictogram', 'structure', 'type')

    class InfrastructureSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        accessibility = serializers.SerializerMethodField()
        attachments = AttachmentSerializer(many=True)

        def get_accessibility(self, obj):
            return get_translation_or_dict('accessibility', self, obj)

        class Meta:
            model = infrastructure_models.Infrastructure
            fields = ('id', 'accessibility', 'attachments', 'conditions', 'description', 'eid', 'geometry', 'name',
                      'implantation_year', 'maintenance_difficulty', 'provider', 'structure', 'type', 'usage_difficulty', 'uuid')

    class InfrastructureConditionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

        class Meta:
            model = infrastructure_models.InfrastructureType
            fields = ('id', 'label', 'structure')

    class InfrastructureMaintenanceDifficultyLevelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

        class Meta:
            model = infrastructure_models.InfrastructureMaintenanceDifficultyLevel
            fields = ('id', 'label', 'structure')

    class InfrastructureUsageDifficultyLevelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

        class Meta:
            model = infrastructure_models.InfrastructureUsageDifficultyLevel
            fields = ('id', 'label', 'structure')

if 'geotrek.signage' in settings.INSTALLED_APPS:

    class LinePictogramSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

        class Meta:
            model = signage_models.LinePictogram
            fields = ('label', 'code', 'pictogram', 'description')

    class LineSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        pictograms = LinePictogramSerializer(many=True)

        class Meta:
            model = signage_models.Line
            fields = ('id', 'direction', 'text', 'pictograms', 'distance', 'time')

    class BladeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        lines = LineSerializer(many=True)

        class Meta:
            model = signage_models.Blade
            fields = ('id', 'number', 'color', 'direction', 'lines')

    class SignageConditionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

        class Meta:
            model = signage_models.SignageCondition
            fields = ('id', 'label', 'structure')

    class SignageSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        attachments = AttachmentSerializer(many=True)
        blades = BladeSerializer(source='blades_set', many=True)
        condition = serializers.SerializerMethodField(
            help_text=_("This field is deprecated and will be removed in next releases. Please start using '%(field)s'") % {"field": "conditions"}
        )

        def get_condition(self, obj):
            condition = obj.conditions.first()
            return condition.pk if condition else None

        class Meta:
            model = signage_models.Signage
            fields = ('id', 'attachments', 'blades', 'code', 'condition', 'conditions', 'description', 'eid',
                      'geometry', 'implantation_year', 'name', 'printed_elevation', 'provider', 'sealing',
                      'structure', 'type', 'uuid')

    class SignageTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        class Meta:
            model = signage_models.SignageType
            fields = ('id', 'label', 'pictogram', 'structure')

    class DirectionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        class Meta:
            model = signage_models.Direction
            fields = ('id', 'label')

    class SealingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        class Meta:
            model = signage_models.Sealing
            fields = ('id', 'label', 'structure')

    class ColorSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        class Meta:
            model = signage_models.Color
            fields = ('id', 'label')

    class BladeTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        class Meta:
            model = signage_models.BladeType
            fields = ('id', 'label', 'structure')


class ReportAPISerializer(rest_serializers.ModelSerializer):
    class Meta:
        model = feedback_models.Report
        id_field = 'id'
        fields = ('id', 'email', 'activity', 'comment', 'category',
                  'status', 'problem_magnitude', 'related_trek',
                  'geom')
        extra_kwargs = {
            'geom': {'write_only': True},
        }

    def create(self, validated_data):
        validated_data['provider'] = "API"
        return super().create(validated_data)

    def validate_geom(self, value):
        return GEOSGeometry(value, srid=4326)

    def validate_comment(self, value):
        return escape(value)


class ReportAPIGeojsonSerializer(GeoFeatureModelSerializer, ReportAPISerializer):
    # Annotated geom field with API_SRID
    api_geom = GeometryField(read_only=True, precision=7)

    class Meta(ReportAPISerializer.Meta):
        geo_field = 'api_geom'
        fields = ReportAPISerializer.Meta.fields + ('api_geom', )
