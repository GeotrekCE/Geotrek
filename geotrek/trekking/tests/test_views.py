#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
from collections import OrderedDict

import mock
from bs4 import BeautifulSoup

from django.conf import settings
from django.test import TestCase
from django.contrib.gis.geos import LineString, MultiPoint, Point
from django.core.urlresolvers import reverse
from django.db import connection
from django.template.loader import find_template
from django.test import RequestFactory
from django.test.utils import override_settings

from mapentity.tests import MapEntityLiveTest
from mapentity.factories import SuperUserFactory

from geotrek.common.factories import AttachmentFactory, ThemeFactory
from geotrek.common.tests import CommonTest
from geotrek.common.utils.testdata import get_dummy_uploaded_image, get_dummy_uploaded_document
from geotrek.authent.factories import TrekkingManagerFactory
from geotrek.core.factories import PathFactory
from geotrek.zoning.factories import DistrictFactory, CityFactory
from geotrek.trekking.models import POI, Trek
from geotrek.trekking.factories import (POIFactory, POITypeFactory, TrekFactory, TrekWithPOIsFactory,
                                        TrekNetworkFactory, WebLinkFactory, AccessibilityFactory,
                                        TrekRelationshipFactory)
from geotrek.trekking.templatetags import trekking_tags
from geotrek.trekking import views as trekking_views
from geotrek.tourism import factories as tourism_factories

# Make sur to register Trek model
from geotrek.trekking import urls  # NOQA

from .base import TrekkingManagerTest


class POIViewsTest(CommonTest):
    model = POI
    modelfactory = POIFactory
    userfactory = TrekkingManagerFactory

    def get_good_data(self):
        PathFactory.create()
        return {
            'name_fr': 'test',
            'name_en': 'test',
            'description_fr': 'ici',
            'description_en': 'here',
            'type': POITypeFactory.create().pk,
            'topology': '{"lat": 5.1, "lng": 6.6}'
        }

    def test_empty_topology(self):
        self.login()
        data = self.get_good_data()
        data['topology'] = ''
        response = self.client.post(self.model.get_add_url(), data)
        self.assertEqual(response.status_code, 200)
        form = self.get_form(response)
        self.assertEqual(form.errors, {'topology': [u'Topology is empty.']})

    def test_listing_number_queries(self):
        self.login()
        # Create many instances
        for i in range(100):
            self.modelfactory.create()
        for i in range(10):
            DistrictFactory.create()

        # Enable query counting
        settings.DEBUG = True

        for url in [self.model.get_jsonlist_url(),
                    self.model.get_format_list_url()]:

            num_queries_old = len(connection.queries)
            self.client.get(url)
            num_queries_new = len(connection.queries)

            nb_queries = num_queries_new - num_queries_old
            self.assertTrue(0 < nb_queries < 100, '%s queries !' % nb_queries)

        settings.DEBUG = False


class POIJSONDetailTest(TrekkingManagerTest):
    def setUp(self):
        self.login()

        polygon = 'SRID=%s;MULTIPOLYGON(((0 0, 0 3, 3 3, 3 0, 0 0)))' % settings.SRID
        self.city = CityFactory(geom=polygon)
        self.district = DistrictFactory(geom=polygon)

        self.poi = POIFactory.create(geom=Point(0, 0, srid=settings.SRID))

        self.attachment = AttachmentFactory.create(obj=self.poi,
                                                   attachment_file=get_dummy_uploaded_image())

        self.touristic_content = tourism_factories.TouristicContentFactory(geom='SRID=%s;POINT(1 1)' % settings.SRID)
        self.touristic_event = tourism_factories.TouristicEventFactory(geom='SRID=%s;POINT(2 2)' % settings.SRID)

        self.pk = self.poi.pk
        url = '/api/pois/%s/' % self.pk
        self.response = self.client.get(url)
        self.result = json.loads(self.response.content)

    def test_name(self):
        self.assertEqual(self.result['name'],
                         self.poi.name)

    def test_slug(self):
        self.assertEqual(self.result['slug'],
                         self.poi.slug)

    def test_published(self):
        self.assertEqual(self.result['published'], False)

    def test_published_status(self):
        self.assertDictEqual(self.result['published_status'][0],
                             {u'lang': u'en', u'status': False, u'language': u'English'})

    def test_type(self):
        self.assertDictEqual(self.result['type'],
                             {'id': self.poi.type.pk,
                              'label': self.poi.type.label,
                              'pictogram': os.path.join(settings.MEDIA_URL, self.poi.type.pictogram.name),
                              })

    def test_altimetry(self):
        self.assertEqual(self.result['min_elevation'], 0.0)

    def test_cities(self):
        self.assertDictEqual(self.result['cities'][0],
                             {u"code": self.city.code,
                              u"name": self.city.name})

    def test_districts(self):
        self.assertDictEqual(self.result['districts'][0],
                             {u"id": self.district.id,
                              u"name": self.district.name})

    def test_related_urls(self):
        self.assertEqual(self.result['map_image_url'],
                         '/image/poi-%s.png' % self.pk)
        self.assertEqual(self.result['filelist_url'],
                         '/paperclip/get/trekking/poi/%s/' % self.pk)

    def test_touristic_contents(self):
        self.assertDictEqual(self.result['touristic_contents'][0], {
            u'slug': self.touristic_content.slug,
            u'id': self.touristic_content.pk,
            u'name': self.touristic_content.name})

    def test_touristic_events(self):
        self.assertDictEqual(self.result['touristic_events'][0], {
            u'slug': self.touristic_event.slug,
            u'id': self.touristic_event.pk,
            u'name': self.touristic_event.name})


class TrekViewsTest(CommonTest):
    model = Trek
    modelfactory = TrekFactory
    userfactory = TrekkingManagerFactory

    def get_bad_data(self):
        return OrderedDict([
            ('name_en', ''),
            ('trek_relationship_a-TOTAL_FORMS', '0'),
            ('trek_relationship_a-INITIAL_FORMS', '1'),
            ('trek_relationship_a-MAX_NUM_FORMS', '0'),
        ]), u'This field is required.'

    def get_good_data(self):
        path = PathFactory.create()
        return {
            'name_fr': 'Huhu',
            'name_en': 'Hehe',
            'departure_fr': '',
            'departure_en': '',
            'arrival_fr': '',
            'arrival_en': '',
            'published': '',
            'difficulty': '',
            'route': '',
            'description_teaser_fr': '',
            'description_teaser_en': '',
            'description_fr': '',
            'description_en': '',
            'ambiance_fr': '',
            'ambiance_en': '',
            'access_fr': '',
            'access_en': '',
            'disabled_infrastructure_fr': '',
            'disabled_infrastructure_en': '',
            'duration': '0',
            'is_park_centered': '',
            'advised_parking': 'Very close',
            'parking_location': 'POINT (1.0 1.0)',
            'public_transport': 'huhu',
            'advice_fr': '',
            'advice_en': '',
            'themes': ThemeFactory.create().pk,
            'networks': TrekNetworkFactory.create().pk,
            'practice': '',
            'accessibilities': AccessibilityFactory.create().pk,
            'web_links': WebLinkFactory.create().pk,
            'information_desks': tourism_factories.InformationDeskFactory.create().pk,
            'topology': '{"paths": [%s]}' % path.pk,

            'trek_relationship_a-TOTAL_FORMS': '2',
            'trek_relationship_a-INITIAL_FORMS': '0',
            'trek_relationship_a-MAX_NUM_FORMS': '',

            'trek_relationship_a-0-id': '',
            'trek_relationship_a-0-trek_b': TrekFactory.create().pk,
            'trek_relationship_a-0-has_common_edge': 'on',
            'trek_relationship_a-0-has_common_departure': 'on',
            'trek_relationship_a-0-is_circuit_step': '',

            'trek_relationship_a-1-id': '',
            'trek_relationship_a-1-trek_b': TrekFactory.create().pk,
            'trek_relationship_a-1-has_common_edge': '',
            'trek_relationship_a-1-has_common_departure': '',
            'trek_relationship_a-1-is_circuit_step': 'on',
        }

    def test_badfield_goodgeom(self):
        self.login()

        bad_data, form_error = self.get_bad_data()
        bad_data['parking_location'] = 'POINT (1.0 1.0)'  # good data

        url = self.model.get_add_url()
        response = self.client.post(url, bad_data)
        self.assertEqual(response.status_code, 200)
        form = self.get_form(response)
        self.assertEqual(form.data['parking_location'], bad_data['parking_location'])

    def test_basic_format(self):
        super(TrekViewsTest, self).test_basic_format()
        self.modelfactory.create(name="ukélélé")   # trek with utf8
        for fmt in ('csv', 'shp', 'gpx'):
            response = self.client.get(self.model.get_format_list_url() + '?format=' + fmt)
            self.assertEqual(response.status_code, 200)


class TrekViewsLiveTest(MapEntityLiveTest):
    model = Trek
    modelfactory = TrekFactory
    userfactory = SuperUserFactory


class TrekCustomViewTests(TrekkingManagerTest):

    def setUp(self):
        self.login()

    def test_pois_geojson(self):
        trek = TrekWithPOIsFactory.create()
        self.assertEqual(len(trek.pois), 2)
        poi = trek.pois[0]
        poi.published = True
        poi.save()
        AttachmentFactory.create(obj=poi, attachment_file=get_dummy_uploaded_image())
        self.assertNotEqual(poi.thumbnail, None)
        self.assertEqual(len(trek.pois), 2)

        url = reverse('trekking:trek_poi_geojson', kwargs={'pk': trek.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        poislayer = json.loads(response.content)
        poifeature = poislayer['features'][0]
        self.assertTrue('thumbnail' in poifeature['properties'])

    def test_kml(self):
        trek = TrekWithPOIsFactory.create()
        url = reverse('trekking:trek_kml_detail', kwargs={'pk': trek.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.google-earth.kml+xml')

    @mock.patch('mapentity.models.MapEntityMixin.get_attributes_html')
    def test_overriden_document(self, get_attributes_html):
        trek = TrekFactory.create()

        get_attributes_html.return_value = '<p>mock</p>'
        with open(trek.get_map_image_path(), 'w') as f:
            f.write('***' * 1000)
        with open(trek.get_elevation_chart_path('fr'), 'w') as f:
            f.write('***' * 1000)

        response = self.client.get(trek.get_document_public_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.content) > 1000)

        AttachmentFactory.create(obj=trek, title="docprint", attachment_file=get_dummy_uploaded_document(size=100))
        response = self.client.get(trek.get_document_public_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.content) < 1000)

    @mock.patch('django.template.loaders.filesystem.open', create=True)
    def test_overriden_public_template(self, open_patched):
        overriden_template = os.path.join(settings.MEDIA_ROOT, 'templates', 'trekking', 'trek_public.odt')

        def fake_exists(f, *args):
            if f == overriden_template:
                return mock.MagicMock(spec=file)
            raise IOError

        open_patched.side_effect = fake_exists
        find_template('trekking/trek_public.odt')
        open_patched.assert_called_with(overriden_template, 'rb')

    def test_profile_json(self):
        trek = TrekFactory.create()
        url = reverse('trekking:trek_profile', kwargs={'pk': trek.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_elevation_area_json(self):
        trek = TrekFactory.create()
        url = reverse('trekking:trek_elevation_area', kwargs={'pk': trek.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_profile_svg(self):
        trek = TrekFactory.create()
        url = reverse('trekking:trek_profile_svg', kwargs={'pk': trek.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')

    def test_weblink_popup(self):
        url = reverse('trekking:weblink_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @override_settings(TREK_EXPORT_POI_LIST_LIMIT=1)
    @mock.patch('mapentity.models.MapEntityMixin.prepare_map_image')
    @mock.patch('mapentity.models.MapEntityMixin.get_attributes_html')
    def test_trek_export_poi_list_limit(self, mocked_prepare, mocked_attributes):
        trek = TrekWithPOIsFactory.create()
        self.assertEqual(len(trek.pois), 2)
        poi = trek.pois[0]
        poi.published = True
        poi.save()
        view = trekking_views.TrekDocumentPublic()
        view.object = trek
        view.request = RequestFactory().get('/')
        view.kwargs = {}
        view.kwargs[view.pk_url_kwarg] = trek.pk
        context = view.get_context_data()
        self.assertEqual(len(context['pois']), 1)


class TrekJSONDetailTest(TrekkingManagerTest):
    """ Since we migrated some code to Django REST Framework, we should test
    the migration extensively. Geotrek-rando mainly relies on this view.
    """

    def setUp(self):
        self.login()

        polygon = 'SRID=%s;MULTIPOLYGON(((0 0, 0 3, 3 3, 3 0, 0 0)))' % settings.SRID
        self.city = CityFactory(geom=polygon)
        self.district = DistrictFactory(geom=polygon)

        self.trek = TrekFactory.create(
            points_reference=MultiPoint([Point(0, 0), Point(1, 1)], srid=settings.SRID),
            parking_location=Point(0, 0, srid=settings.SRID)
        )

        self.attachment = AttachmentFactory.create(obj=self.trek,
                                                   attachment_file=get_dummy_uploaded_image())

        self.information_desk = tourism_factories.InformationDeskFactory.create()
        self.trek.information_desks.add(self.information_desk)

        self.theme = ThemeFactory.create()
        self.trek.themes.add(self.theme)

        self.accessibility = AccessibilityFactory.create()
        self.trek.accessibilities.add(self.accessibility)

        self.network = TrekNetworkFactory.create()
        self.trek.networks.add(self.network)

        self.weblink = WebLinkFactory.create()
        self.trek.web_links.add(self.weblink)

        self.trek_b = TrekFactory.create()
        TrekRelationshipFactory.create(has_common_departure=True,
                                       has_common_edge=False,
                                       is_circuit_step=True,
                                       trek_a=self.trek,
                                       trek_b=self.trek_b)

        self.touristic_content = tourism_factories.TouristicContentFactory(geom='SRID=%s;POINT(1 1)' % settings.SRID)
        self.touristic_event = tourism_factories.TouristicEventFactory(geom='SRID=%s;POINT(2 2)' % settings.SRID)

        self.pk = self.trek.pk
        url = '/api/treks/%s/' % self.pk
        self.response = self.client.get(url)
        self.result = json.loads(self.response.content)

    def test_old_url_redirects_to_api_detail(self):
        url = '/api/trek/trek-%s.json' % self.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)  # permanent
        self.assertEqual(response.url, 'http://testserver/api/treks/%s/' % self.pk)

    def test_related_urls(self):

        self.assertEqual(self.result['elevation_area_url'],
                         '/api/trek/%s/dem.json' % self.pk)
        self.assertEqual(self.result['map_image_url'],
                         '/image/trek-%s.png' % self.pk)
        self.assertEqual(self.result['altimetric_profile'],
                         "/api/trek/%s/profile.json" % self.pk)
        self.assertEqual(self.result['poi_layer'],
                         "/api/trek/%s/pois.geojson" % self.pk)
        self.assertEqual(self.result['information_desk_layer'],
                         '/api/trek/%s/information_desks.geojson' % self.pk)
        self.assertEqual(self.result['filelist_url'],
                         '/paperclip/get/trekking/trek/%s/' % self.pk)
        self.assertEqual(self.result['gpx'],
                         '/api/trek/trek-%s.gpx' % self.pk)
        self.assertEqual(self.result['kml'],
                         '/api/trek/trek-%s.kml' % self.pk)
        self.assertEqual(self.result['printable'],
                         '/api/trek/trek-%s.pdf' % self.pk)

    def test_thumbnail(self):
        self.assertEqual(self.result['thumbnail'],
                         os.path.join(settings.MEDIA_URL, self.attachment.attachment_file.name) + '.120x120_q85_crop.png')

    def test_published_status(self):
        self.assertDictEqual(self.result['published_status'][0],
                             {u'lang': u'en', u'status': True, u'language': u'English'})

    def test_pictures(self):
        self.assertDictEqual(self.result['pictures'][0],
                             {u'url': os.path.join(settings.MEDIA_URL, self.attachment.attachment_file.name) + '.800x800_q85.png',
                              u'title': self.attachment.title,
                              u'legend': self.attachment.legend,
                              u'author': self.attachment.author})

    def test_cities(self):
        self.assertDictEqual(self.result['cities'][0],
                             {u"code": self.city.code,
                              u"name": self.city.name})

    def test_districts(self):
        self.assertDictEqual(self.result['districts'][0],
                             {u"id": self.district.id,
                              u"name": self.district.name})

    def test_networks(self):
        self.assertDictEqual(self.result['networks'][0],
                             {u"id": self.network.id,
                              u"pictogram": None,
                              u"name": self.network.network})

    def test_practice_not_none(self):
        self.assertDictEqual(self.result['practice'],
                             {u"id": self.trek.practice.id,
                              u"pictogram": os.path.join(settings.MEDIA_URL, self.trek.practice.pictogram.name),
                              u"label": self.trek.practice.name})

    def test_usages(self):  # Rando v1 compat
        self.assertDictEqual(self.result['usages'][0],
                             {u"id": self.trek.practice.id,
                              u"pictogram": os.path.join(settings.MEDIA_URL, self.trek.practice.pictogram.name),
                              u"label": self.trek.practice.name})

    def test_accessibilities(self):
        self.assertDictEqual(self.result['accessibilities'][0],
                             {u"id": self.accessibility.id,
                              u"label": self.accessibility.name})

    def test_themes(self):
        self.assertDictEqual(self.result['themes'][0],
                             {u"id": self.theme.id,
                              u"pictogram": os.path.join(settings.MEDIA_URL, self.theme.pictogram.name),
                              u"label": self.theme.label})

    def test_weblinks(self):
        self.assertDictEqual(self.result['web_links'][0],
                             {u"id": self.weblink.id,
                              u"url": self.weblink.url,
                              u"name": self.weblink.name,
                              u"category": {
                                  u"id": self.weblink.category.id,
                                  u"pictogram": os.path.join(settings.MEDIA_URL, self.weblink.category.pictogram.name),
                                  u"label": self.weblink.category.label}
                              })

    def test_route_not_none(self):
        self.assertDictEqual(self.result['route'],
                             {u"id": self.trek.route.id,
                              u"pictogram": None,
                              u"label": self.trek.route.route})

    def test_difficulty_not_none(self):
        self.assertDictEqual(self.result['difficulty'],
                             {u"id": self.trek.difficulty.id,
                              u"pictogram": os.path.join(settings.MEDIA_URL, self.trek.difficulty.pictogram.name),
                              u"label": self.trek.difficulty.difficulty})

    def test_information_desks(self):
        desk_type = self.information_desk.type
        self.assertDictEqual(self.result['information_desks'][0],
                             {u'description': self.information_desk.description,
                              u'email': self.information_desk.email,
                              u'latitude': self.information_desk.latitude,
                              u'longitude': self.information_desk.longitude,
                              u'name': self.information_desk.name,
                              u'phone': self.information_desk.phone,
                              u'photo_url': self.information_desk.photo_url,
                              u'postal_code': self.information_desk.postal_code,
                              u'street': self.information_desk.street,
                              u'municipality': self.information_desk.municipality,
                              u'website': self.information_desk.website,
                              u'type': {
                                  u'id': desk_type.id,
                                  u'pictogram': desk_type.pictogram.url,
                                  u'label': desk_type.label}})

    def test_relationships(self):
        self.assertDictEqual(self.result['relationships'][0],
                             {u'published': self.trek_b.published,
                              u'has_common_departure': True,
                              u'has_common_edge': False,
                              u'is_circuit_step': True,
                              u'trek': {u'pk': self.trek_b.pk,
                                        u'id': self.trek_b.id,
                                        u'slug': self.trek_b.slug,
                                        u'name': self.trek_b.name,
                                        u'url': u'/trek/%s/' % self.trek_b.id}})

    def test_parking_location_in_wgs84(self):
        parking_location = self.result['parking_location']
        self.assertEqual(parking_location[0], -1.3630812101179004)

    def test_points_reference_are_exported_in_wgs84(self):
        geojson = self.result['points_reference']
        self.assertEqual(geojson['type'], 'MultiPoint')
        self.assertEqual(geojson['coordinates'][0][0], -1.3630812101179)

    def test_touristic_contents(self):
        self.assertDictEqual(self.result['touristic_contents'][0], {
            u'slug': self.touristic_content.slug,
            u'id': self.touristic_content.pk,
            u'name': self.touristic_content.name})

    def test_touristic_events(self):
        self.assertDictEqual(self.result['touristic_events'][0], {
            u'slug': self.touristic_event.slug,
            u'id': self.touristic_event.pk,
            u'name': self.touristic_event.name})

    def test_type1(self):
        self.assertDictEqual(self.result['type1'][0],
                             {u"id": self.trek.practice.id,
                              u"name": self.trek.practice.name})

    def test_type2(self):
        self.assertDictEqual(self.result['type2'][0],
                             {u"id": self.accessibility.id,
                              u"name": self.accessibility.name})

    def test_category(self):
        self.assertDictEqual(self.result['category'],
                             {u"id": -2,
                              u"label": u"Trek",
                              u"type1_label": u"Practice",
                              u"type2_label": u"Accessibilities",
                              u"pictogram": u"/static/trekking/trek.svg"})


class TrekPointsReferenceTest(TrekkingManagerTest):
    def setUp(self):
        self.login()

        self.trek = TrekFactory.create()
        self.trek.points_reference = MultiPoint([Point(0, 0), Point(1, 1)], srid=settings.SRID)
        self.trek.save()

    def test_points_reference_editable_as_hidden_input(self):
        url = self.trek.get_update_url()
        response = self.client.get(url)
        self.assertContains(response, 'name="points_reference"')

    @override_settings(TREK_POINTS_OF_REFERENCE_ENABLED=False)
    def test_points_reference_is_marked_as_disabled_when_disabled(self):
        url = self.trek.get_update_url()
        response = self.client.get(url)
        self.assertNotContains(response, 'name="points_reference"')


class TrekGPXTest(TrekkingManagerTest):

    def setUp(self):
        self.login()

        self.trek = TrekWithPOIsFactory.create()
        self.trek.description_en = 'Nice trek'
        self.trek.description_it = 'Bonnito iti'
        self.trek.description_fr = 'Jolie rando'
        self.trek.save()

        for poi in self.trek.pois.all():
            poi.description_it = poi.description
            poi.save()

        url = reverse('trekking:trek_gpx_detail', kwargs={'pk': self.trek.pk})
        self.response = self.client.get(url, HTTP_ACCEPT_LANGUAGE='it-IT')
        self.parsed = BeautifulSoup(self.response.content)

    def test_gpx_is_served_with_content_type(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response['Content-Type'], 'application/gpx+xml')

    def test_gpx_trek_as_route_points(self):
        self.assertEqual(len(self.parsed.findAll('rte')), 1)
        self.assertEqual(len(self.parsed.findAll('rtept')), 2)

    def test_gpx_translated_using_accept_language(self):
        route = self.parsed.findAll('rte')[0]
        description = route.find('desc').string
        self.assertTrue(description.startswith(self.trek.description_it))

    def test_gpx_contains_pois(self):
        waypoints = self.parsed.findAll('wpt')
        pois = self.trek.pois.all()
        self.assertEqual(len(waypoints), len(pois))
        waypoint = waypoints[0]
        name = waypoint.find('name').string
        description = waypoint.find('desc').string
        self.assertEqual(name, u"%s: %s" % (pois[0].type, pois[0].name))
        self.assertEqual(description, pois[0].description)


class TrekViewTranslationTest(TrekkingManagerTest):
    def setUp(self):
        self.trek = TrekFactory.build()
        self.trek.name_fr = 'Voie lactee'
        self.trek.name_en = 'Milky way'
        self.trek.name_it = 'Via Lattea'

        self.trek.published_fr = True
        self.trek.published_it = False
        self.trek.save()

    def tearDown(self):
        self.client.logout()

    def test_json_translation(self):
        url = '/api/treks/%s/' % self.trek.pk

        for lang, expected in [('fr-FR', self.trek.name_fr),
                               ('it-IT', self.trek.name_it)]:
            self.login()
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            obj = json.loads(response.content)
            self.assertEqual(obj['name'], expected)
            self.client.logout()  # Django 1.6 keeps language in session

    def test_geojson_translation(self):
        url = reverse('trekking:trek_layer')

        for lang, expected in [('fr-FR', self.trek.name_fr),
                               ('it-IT', self.trek.name_it)]:
            self.login()
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            obj = json.loads(response.content)
            self.assertEqual(obj['features'][0]['properties']['name'], expected)
            self.client.logout()  # Django 1.6 keeps language in session

    def test_published_translation(self):
        url = reverse('trekking:trek_layer')

        for lang, expected in [('fr-FR', self.trek.published_fr),
                               ('it-IT', self.trek.published_it)]:
            self.login()
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            obj = json.loads(response.content)
            self.assertEqual(obj['features'][0]['properties']['published'], expected)
            self.client.logout()  # Django 1.6 keeps language in session

    def test_poi_geojson_translation(self):
        # Create a Trek with a POI
        trek = TrekFactory.create(no_path=True)
        p1 = PathFactory.create(geom=LineString((0, 0), (4, 4)))
        poi = POIFactory.create(no_path=True)
        poi.name_fr = "Chapelle"
        poi.name_en = "Chapel"
        poi.name_it = "Capela"
        poi.published_fr = True
        poi.published_en = True
        poi.published_it = True
        poi.save()
        trek.add_path(p1, start=0.5)
        poi.add_path(p1, start=0.6, end=0.6)
        # Check that it applies to GeoJSON also :
        self.assertEqual(len(trek.pois), 1)
        poi = trek.pois[0]
        for lang, expected in [('fr-FR', poi.name_fr),
                               ('it-IT', poi.name_it)]:
            url = reverse('trekking:trek_poi_geojson', kwargs={'pk': trek.pk})
            self.login()
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            obj = json.loads(response.content)
            jsonpoi = obj.get('features', [])[0]
            self.assertEqual(jsonpoi.get('properties', {}).get('name'), expected)
            self.client.logout()  # Django 1.6 keeps language in session


class TrekInformationDeskGeoJSONTest(TrekkingManagerTest):

    def setUp(self):
        self.trek = TrekFactory.create()
        self.information_desk1 = tourism_factories.InformationDeskFactory.create()
        self.information_desk2 = tourism_factories.InformationDeskFactory.create(photo=None)
        self.information_desk3 = tourism_factories.InformationDeskFactory.create()
        self.trek.information_desks.add(self.information_desk1)
        self.trek.information_desks.add(self.information_desk2)
        self.url = reverse('trekking:trek_information_desk_geojson', kwargs={'pk': self.trek.pk})

    def test_trek_layer_is_login_required(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_information_desks_layer_contains_only_trek_records(self):
        self.login()
        resp = self.client.get(self.url)
        dataset = json.loads(resp.content)
        self.assertEqual(len(dataset['features']), 2)

    def test_information_desk_layer_has_null_if_no_photo(self):
        self.login()
        resp = self.client.get(self.url)
        dataset = json.loads(resp.content)
        second = dataset['features'][1]
        self.assertEqual(second['properties']['photo_url'], None)

    def test_information_desk_layer_gives_all_model_attributes(self):
        self.login()
        resp = self.client.get(self.url)
        dataset = json.loads(resp.content)
        first = dataset['features'][0]
        self.assertEqual(sorted(first['properties'].keys()),
                         [u'description',
                          u'email',
                          u'id',
                          u'latitude',
                          u'longitude',
                          u'model',
                          u'municipality',
                          u'name',
                          u'phone',
                          u'photo_url',
                          u'postal_code',
                          u'street',
                          u'type',
                          u'website'])


class TemplateTagsTest(TestCase):
    def test_duration(self):
        self.assertEqual(u"15 min", trekking_tags.duration(0.25))
        self.assertEqual(u"30 min", trekking_tags.duration(0.5))
        self.assertEqual(u"1H", trekking_tags.duration(1))
        self.assertEqual(u"1H45", trekking_tags.duration(1.75))
        self.assertEqual(u"3H30", trekking_tags.duration(3.5))
        self.assertEqual(u"4H", trekking_tags.duration(4))
        self.assertEqual(u"6H", trekking_tags.duration(6))
        self.assertEqual(u"10H", trekking_tags.duration(10))
        self.assertEqual(u"2 days", trekking_tags.duration(11))
        self.assertEqual(u"2 days", trekking_tags.duration(32))
        self.assertEqual(u"2 days", trekking_tags.duration(48))
        self.assertEqual(u"More than 8 days", trekking_tags.duration(24 * 8))
        self.assertEqual(u"More than 8 days", trekking_tags.duration(24 * 9))
