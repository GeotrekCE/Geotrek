import json

from easy_thumbnails.alias import aliases
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from django.conf import settings
from django.contrib.gis.geos import MultiLineString, Point
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import get_language, gettext_lazy as _
from drf_dynamic_fields import DynamicFieldsMixin
from PIL.Image import DecompressionBombError
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework_gis import serializers as geo_serializers

from geotrek.api.v2.functions import Length, Length3D, Transform
from geotrek.api.v2.utils import build_url, get_translation_or_dict
from geotrek.authent import models as authent_models
from geotrek.common import models as common_models
from geotrek.core.models import simplify_coords

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
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('network', self, obj)

        class Meta:
            model = trekking_models.TrekNetwork
            fields = ('id', 'label', 'pictogram')

    class PracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.Practice
            fields = ('id', 'name', 'order', 'pictogram',)

    class TrekDifficultySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('difficulty', self, obj)

        class Meta:
            model = trekking_models.DifficultyLevel
            fields = ('id', 'cirkwi_level', 'label', 'pictogram')

    class RouteSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        route = serializers.SerializerMethodField(read_only=True)

        def get_route(self, obj):
            return get_translation_or_dict('route', self, obj)

        class Meta:
            model = trekking_models.Route
            fields = ('id', 'pictogram', 'route')

    class WebLinkCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.WebLinkCategory
            fields = ('label', 'id', 'pictogram')

    class WebLinkSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)
        category = WebLinkCategorySerializer()

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.WebLink
            fields = ('name', 'url', 'category')


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
    title = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    facebook_image_url = serializers.SerializerMethodField(read_only=True)

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


class AttachmentSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)
    thumbnail = serializers.SerializerMethodField(read_only=True)
    backend = serializers.SerializerMethodField(read_only=True)

    def get_url(self, obj):
        if obj.attachment_file:
            return build_url(self, obj.attachment_file.url)
        if obj.attachment_video:
            return obj.attachment_video
        if obj.attachment_link:
            return obj.attachment_link
        return ""

    def get_type(self, obj):
        if obj.is_image or obj.attachment_link:
            return "image"
        if obj.attachment_video != '':
            return "video"
        return "file"

    def get_thumbnail(self, obj):
        thumbnailer = get_thumbnailer(obj.attachment_file)
        try:
            thumbnail = thumbnailer.get_thumbnail(aliases.get('apiv2'))
        except (IOError, InvalidImageFormatError, DecompressionBombError):
            return ""
        thumbnail.author = obj.author
        thumbnail.legend = obj.legend
        return build_url(self, thumbnail.url)

    def get_backend(self, obj):
        if obj.attachment_video != '':
            return type(obj).__name__.replace('Backend', '')
        return ""

    class Meta:
        model = common_models.Attachment
        fields = (
            'author', 'backend', 'thumbnail',
            'legend', 'title', 'url', "type"
        )


class LabelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    advice = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        return get_translation_or_dict('name', self, obj)

    def get_advice(self, obj):
        return get_translation_or_dict('advice', self, obj)

    class Meta:
        model = common_models.Label
        fields = ('id', 'advice', 'filter', 'name', 'pictogram')


if 'geotrek.tourism' in settings.INSTALLED_APPS:
    class TouristicContentCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        types = serializers.SerializerMethodField(read_only=True)
        label = serializers.SerializerMethodField(read_only=True)

        class Meta:
            model = tourism_models.TouristicContentCategory
            fields = ('id', 'label', 'order', 'pictogram', 'types')

        def get_types(self, obj):
            return [{
                'id': obj.id * 100 + i,
                'label': get_translation_or_dict('type{}_label'.format(i), self, obj),
                'values': [{
                    'id': t.id,
                    'label': get_translation_or_dict('label', self, t),
                    'pictogram': t.pictogram.url if t.pictogram else None,
                } for t in obj.types.filter(in_list=i)]
            } for i in (1, 2)]

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

    class TouristicContentSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:touristiccontent-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        create_datetime = serializers.DateTimeField(source='date_update')
        update_datetime = serializers.DateTimeField(source='date_insert')
        external_id = serializers.CharField(source='eid')
        types = serializers.SerializerMethodField(read_only=True)
        cities = serializers.SerializerMethodField(read_only=True)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        name = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)
        description_teaser = serializers.SerializerMethodField(read_only=True)
        practical_info = serializers.SerializerMethodField(read_only=True)
        pdf = serializers.SerializerMethodField('get_pdf_url')
        departure_city = serializers.SerializerMethodField(read_only=True)

        class Meta:
            model = tourism_models.TouristicContent
            fields = (
                'id', 'attachments', 'approved', 'category', 'description',
                'description_teaser', 'departure_city', 'geometry',
                'practical_info', 'url', 'cities', 'create_datetime',
                'external_id', 'name', 'pdf', 'portal', 'published',
                'source', 'structure', 'themes',
                'update_datetime', 'types', 'contact', 'email',
                'website', 'reservation_system', 'reservation_id',
            )

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_description_teaser(self, obj):
            return get_translation_or_dict('description_teaser', self, obj)

        def get_practical_info(self, obj):
            return get_translation_or_dict('practical_info', self, obj)

        def get_types(self, obj):
            return {
                obj.category.id * 100 + i: [
                    t.id for t in getattr(obj, 'type{}'.format(i)).all()
                ] for i in (1, 2)
            }

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def _get_pdf_url_lang(self, obj, lang):
            if settings.ONLY_EXTERNAL_PUBLIC_PDF:
                file_type = get_object_or_404(common_models.FileType, type="Topoguide")
                if not common_models.Attachment.objects.attachments_for_object_only_type(obj, file_type).exists():
                    return None
            urlname = 'tourism:touristiccontent_{}printable'.format('booklet_' if settings.USE_BOOKLET_PDF else '')
            url = reverse(urlname, kwargs={'lang': lang, 'pk': obj.pk, 'slug': obj.slug})
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(url)
            return url

        def get_pdf_url(self, obj):
            lang = self.context.get('request').GET.get('language', 'all') if self.context.get('request') else 'all'
            if lang != 'all':
                data = self._get_pdf_url_lang(obj, lang)
            else:
                data = {}
                for language in settings.MODELTRANSLATION_LANGUAGES:
                    data[language] = self._get_pdf_url_lang(obj, language)
            return data

        def get_departure_city(self, obj):
            city = zoning_models.City.objects.all().filter(geom__contains=obj.geom).first()
            return city.code if city else None

    class InformationDeskTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = tourism_models.InformationDeskType
            fields = ('id', 'label', 'pictogram')

    class InformationDeskSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        type = InformationDeskTypeSerializer()
        name = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)
        photo_url = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_photo_url(self, obj):
            return build_url(self, obj.photo_url) if obj.photo_url else ""

        class Meta:
            model = tourism_models.InformationDesk
            geo_field = 'geom'
            fields = (
                'id', 'description', 'email', 'latitude', 'longitude',
                'municipality', 'name', 'phone', 'photo_url',
                'postal_code', 'street', 'type', 'website'
            )


if 'geotrek.core' in settings.INSTALLED_APPS:
    class PathSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:trek-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        length_2d = serializers.SerializerMethodField(read_only=True)
        length_3d = serializers.SerializerMethodField(read_only=True)

        def get_length_2d(self, obj):
            return round(obj.length_2d_m, 1)

        def get_length_3d(self, obj):
            return round(obj.length_3d_m, 1)

        class Meta:
            model = core_models.Path
            fields = (
                'id', 'comments', 'geometry', 'length_2d', 'length_3d',
                'name', 'url'
            )


if 'geotrek.trekking' in settings.INSTALLED_APPS:
    class TrekSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:trek-detail')
        published = serializers.SerializerMethodField(read_only=True)
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        length_2d = serializers.SerializerMethodField(read_only=True)
        length_3d = serializers.SerializerMethodField(read_only=True)
        name = serializers.SerializerMethodField(read_only=True)
        access = serializers.SerializerMethodField(read_only=True)
        ambiance = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)
        description_teaser = serializers.SerializerMethodField(read_only=True)
        departure = serializers.SerializerMethodField(read_only=True)
        disabled_infrastructure = serializers.SerializerMethodField(read_only=True)
        departure_geom = serializers.SerializerMethodField(read_only=True)
        arrival = serializers.SerializerMethodField(read_only=True)
        external_id = serializers.CharField(source='eid')
        second_external_id = serializers.CharField(source='eid2')
        create_datetime = serializers.SerializerMethodField(read_only=True)
        update_datetime = serializers.SerializerMethodField(read_only=True)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')
        gpx = serializers.SerializerMethodField('get_gpx_url')
        kml = serializers.SerializerMethodField('get_kml_url')
        pdf = serializers.SerializerMethodField('get_pdf_url')
        advice = serializers.SerializerMethodField(read_only=True)
        advised_parking = serializers.SerializerMethodField(read_only=True)
        parking_location = serializers.SerializerMethodField(read_only=True)
        children = serializers.ReadOnlyField(source='children_id')
        parents = serializers.ReadOnlyField(source='parents_id')
        public_transport = serializers.SerializerMethodField(read_only=True)
        elevation_area_url = serializers.SerializerMethodField()
        elevation_svg_url = serializers.SerializerMethodField()
        altimetric_profile = serializers.SerializerMethodField('get_altimetric_profile_url')
        points_reference = serializers.SerializerMethodField(read_only=True)
        previous = serializers.ReadOnlyField(source='previous_id')
        next = serializers.ReadOnlyField(source='next_id')
        cities = serializers.SerializerMethodField(read_only=True)
        departure_city = serializers.SerializerMethodField(read_only=True)
        web_links = WebLinkSerializer(many=True)

        def get_update_datetime(self, obj):
            return obj.topo_object.date_update

        def get_create_datetime(self, obj):
            return obj.topo_object.date_insert

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_access(self, obj):
            return get_translation_or_dict('access', self, obj)

        def get_ambiance(self, obj):
            return get_translation_or_dict('ambiance', self, obj)

        def get_disabled_infrastructure(self, obj):
            return get_translation_or_dict('disabled_infrastructure', self, obj)

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
            return get_translation_or_dict('description_teaser', self, obj)

        def get_length_2d(self, obj):
            return round(obj.length_2d_m, 1)

        def get_length_3d(self, obj):
            return round(obj.length_3d_m, 1)

        def get_gpx_url(self, obj):
            return build_url(self, reverse('trekking:trek_gpx_detail', kwargs={'lang': get_language(), 'pk': obj.pk, 'slug': obj.slug}))

        def get_kml_url(self, obj):
            return build_url(self, reverse('trekking:trek_kml_detail', kwargs={'lang': get_language(), 'pk': obj.pk, 'slug': obj.slug}))

        def _get_pdf_url_lang(self, obj, lang):
            if settings.ONLY_EXTERNAL_PUBLIC_PDF:
                file_type = get_object_or_404(common_models.FileType, type="Topoguide")
                if not common_models.Attachment.objects.attachments_for_object_only_type(obj, file_type).exists():
                    return None
            urlname = 'trekking:trek_{}printable'.format('booklet_' if settings.USE_BOOKLET_PDF else '')
            url = reverse(urlname, kwargs={'lang': lang, 'pk': obj.pk, 'slug': obj.slug})
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(url)
            return url

        def get_pdf_url(self, obj):
            lang = self.context.get('request').GET.get('language', 'all') if self.context.get('request') else 'all'
            if lang != 'all':
                data = self._get_pdf_url_lang(obj, lang)
            else:
                data = {}
                for language in settings.MODELTRANSLATION_LANGUAGES:
                    data[language] = self._get_pdf_url_lang(obj, language)
            return data

        def get_advice(self, obj):
            return get_translation_or_dict('advice', self, obj)

        def get_advised_parking(self, obj):
            return get_translation_or_dict('advised_parking', self, obj)

        def get_parking_location(self, obj):
            if not obj.parking_location:
                return None
            point = obj.parking_location.transform(settings.API_SRID, clone=True)
            return [round(point.x, 7), round(point.y, 7)]

        def get_public_transport(self, obj):
            return get_translation_or_dict('public_transport', self, obj)

        def get_elevation_area_url(self, obj):
            return build_url(self, reverse('trekking:trek_elevation_area', kwargs={'lang': get_language(), 'pk': obj.pk}))

        def get_elevation_svg_url(self, obj):
            return build_url(self, reverse('trekking:trek_profile_svg', kwargs={'lang': get_language(), 'pk': obj.pk}))

        def get_altimetric_profile_url(self, obj):
            return build_url(self, reverse('trekking:trek_profile', kwargs={'lang': get_language(), 'pk': obj.pk}))

        def get_points_reference(self, obj):
            if not obj.points_reference:
                return None
            geojson = obj.points_reference.transform(settings.API_SRID, clone=True).geojson
            return json.loads(geojson)

        def get_cities(self, obj):
            return [city.code for city in obj.published_cities]

        def get_departure_city(self, obj):
            geom = self.get_first_point(obj.geom)
            city = zoning_models.City.objects.all().filter(geom__contains=geom).first()
            return city.code if city else None

        class Meta:
            model = trekking_models.Trek
            fields = (
                'id', 'access', 'accessibilities', 'advice', 'advised_parking',
                'altimetric_profile', 'ambiance', 'arrival', 'ascent',
                'attachments', 'children', 'cities', 'create_datetime',
                'departure', 'departure_city', 'departure_geom', 'descent',
                'description', 'description_teaser', 'difficulty',
                'disabled_infrastructure', 'duration', 'elevation_area_url',
                'elevation_svg_url', 'external_id', 'geometry', 'gpx',
                'information_desks', 'kml', 'labels', 'length_2d', 'length_3d',
                'max_elevation', 'min_elevation', 'name', 'networks', 'next',
                'parents', 'parking_location', 'pdf', 'points_reference',
                'portal', 'practice', 'previous', 'public_transport',
                'published', 'reservation_system', 'route', 'second_external_id',
                'source', 'structure', 'themes', 'update_datetime', 'url', 'web_links'
            )

    class TourSerializer(TrekSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:tour-detail')
        count_children = serializers.SerializerMethodField(read_only=True)
        steps = serializers.SerializerMethodField(read_only=True)

        def get_count_children(self, obj):
            return obj.count_children

        def get_steps(self, obj):
            qs = obj.children \
                .select_related('topo_object', 'difficulty') \
                .prefetch_related('topo_object__aggregations', 'themes', 'networks', 'attachments') \
                .annotate(geom3d_transformed=Transform(F('geom_3d'), settings.API_SRID),
                          length_2d_m=Length('geom'),
                          length_3d_m=Length3D('geom_3d'))
            FinalClass = override_serializer(self.context.get('request').GET.get('format'),
                                             TrekSerializer)
            return FinalClass(qs, many=True, context=self.context).data

        class Meta(TrekSerializer.Meta):
            fields = TrekSerializer.Meta.fields + ('count_children', 'steps')

    class POITypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.POIType
            fields = ('id', 'label', 'pictogram')

    class POISerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:poi-detail')
        name = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)
        external_id = serializers.SerializerMethodField(read_only=True, help_text=_("External ID"))
        published = serializers.SerializerMethodField(read_only=True)
        create_datetime = serializers.SerializerMethodField(read_only=True)
        update_datetime = serializers.SerializerMethodField(read_only=True)
        geometry = geo_serializers.GeometryField(read_only=True, source="geom3d_transformed", precision=7)
        attachments = AttachmentSerializer(many=True, source='sorted_attachments')

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)

        def get_external_id(self, obj):
            return obj.eid

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_update_datetime(self, obj):
            return obj.topo_object.date_update

        def get_create_datetime(self, obj):
            return obj.topo_object.date_insert

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = trekking_models.POI
            fields = (
                'id', 'create_datetime', 'description', 'external_id',
                'geometry', 'name', 'attachments', 'published', 'type',
                'update_datetime', 'url'
            )

    class ThemeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = trekking_models.Theme
            fields = ('id', 'label', 'pictogram')

    class AccessibilitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = trekking_models.Accessibility
            fields = ('id', 'name', 'pictogram')


if 'geotrek.sensitivity' in settings.INSTALLED_APPS:
    class SensitiveAreaSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:sensitivearea-detail')
        name = serializers.SerializerMethodField(read_only=True)
        elevation = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)
        period = serializers.SerializerMethodField(read_only=True)
        practices = serializers.SerializerMethodField(read_only=True)
        info_url = serializers.URLField(source='species.url')
        structure = serializers.CharField(source='structure.name')
        create_datetime = serializers.DateTimeField(source='date_insert')
        update_datetime = serializers.DateTimeField(source='date_update')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)
        species_id = serializers.SerializerMethodField(read_only=True)
        kml_url = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj.species)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        def get_period(self, obj):
            return [getattr(obj.species, 'period{:02}'.format(p)) for p in range(1, 13)]

        def get_practices(self, obj):
            return obj.species.practices.values_list('id', flat=True)

        def get_elevation(self, obj):
            return obj.species.radius

        def get_species_id(self, obj):
            if obj.species.category == sensitivity_models.Species.SPECIES:
                return obj.species.id
            return None

        def get_kml_url(self, obj):
            url = reverse('sensitivity:sensitivearea_kml_detail', kwargs={'lang': get_language(), 'pk': obj.pk})
            return build_url(self, url)

        class Meta:
            model = sensitivity_models.SensitiveArea
            fields = (
                'id', 'contact', 'create_datetime', 'description', 'elevation',
                'geometry', 'info_url', 'kml_url', 'name', 'period',
                'practices', 'published', 'species_id', 'structure',
                'update_datetime', 'url'
            )

    class BubbleSensitiveAreaSerializer(SensitiveAreaSerializer):
        radius = serializers.SerializerMethodField(read_only=True)

        def get_radius(self, obj):
            if obj.species.category == sensitivity_models.Species.SPECIES and obj.geom.geom_typeid == 0:
                return obj.species.radius
            else:
                return None

        class Meta:
            model = SensitiveAreaSerializer.Meta.model
            fields = SensitiveAreaSerializer.Meta.fields + ('radius', )

    class SportPracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = sensitivity_models.SportPractice
            fields = (
                'id', 'name'
            )

    class SpeciesSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)
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
        practices = serializers.SerializerMethodField(read_only=True)

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
    class RatingScaleSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.RatingScale
            fields = ('id', 'name', 'practice')

    class RatingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)
        description = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        def get_description(self, obj):
            return get_translation_or_dict('description', self, obj)

        class Meta:
            model = outdoor_models.Rating
            fields = ('id', 'name', 'description', 'scale', 'order', 'color')

    class OutdoorPracticeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.Practice
            fields = ('id', 'name')

    class SiteTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.SerializerMethodField(read_only=True)

        def get_name(self, obj):
            return get_translation_or_dict('name', self, obj)

        class Meta:
            model = outdoor_models.SiteType
            fields = ('id', 'name', 'practice')

    class SiteSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:site-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)

        class Meta:
            model = outdoor_models.Site
            fields = (
                'id', 'geometry', 'url', 'structure', 'name', 'practice', 'description',
                'description_teaser', 'ambiance', 'advice', 'period', 'labels', 'themes',
                'portal', 'source', 'information_desks', 'web_links', 'eid',
                'orientation', 'wind', 'ratings_min', 'ratings_max', 'managers',
            )

    class CourseSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        url = HyperlinkedIdentityField(view_name='apiv2:course-detail')
        geometry = geo_serializers.GeometryField(read_only=True, source="geom_transformed", precision=7)

        class Meta:
            model = outdoor_models.Course
            fields = (
                'id', 'geometry', 'url', 'structure', 'name', 'site', 'description',
                'advice', 'equipment', 'eid', 'height', 'length', 'ratings',
            )

if 'geotrek.feedback' in settings.INSTALLED_APPS:
    class ReportStatusSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportStatus
            fields = ('id', 'label')

    class ReportCategorySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportCategory
            fields = ('id', 'label')

    class ReportActivitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportActivity
            fields = ('id', 'label')

    class ReportProblemMagnitudeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        label = serializers.SerializerMethodField(read_only=True)

        def get_label(self, obj):
            return get_translation_or_dict('label', self, obj)

        class Meta:
            model = feedback_models.ReportProblemMagnitude
            fields = ('id', 'label')


if 'geotrek.flatpages' in settings.INSTALLED_APPS:
    class FlatPageSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        title = serializers.SerializerMethodField(read_only=True)
        content = serializers.SerializerMethodField(read_only=True)
        published = serializers.SerializerMethodField(read_only=True)
        attachments = AttachmentSerializer(many=True)

        class Meta:
            model = flatpages_models.FlatPage
            fields = (
                'id', 'title', 'external_url', 'content', 'target', 'source', 'portal', 'order',
                'published', 'attachments',
            )

        def get_title(self, obj):
            return get_translation_or_dict('title', self, obj)

        def get_content(self, obj):
            return get_translation_or_dict('content', self, obj)

        def get_published(self, obj):
            return get_translation_or_dict('published', self, obj)
