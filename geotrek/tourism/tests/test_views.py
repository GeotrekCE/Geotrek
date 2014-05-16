# -*- coding: utf-8 -*-
import os
import json

import mock
from requests.exceptions import ConnectionError
from django.core.urlresolvers import reverse

from geotrek.trekking.tests import TrekkingManagerTest
from geotrek.tourism.models import DATA_SOURCE_TYPES
from geotrek.tourism.factories import DataSourceFactory


class TourismAdminViewsTests(TrekkingManagerTest):

    def setUp(self):
        self.source = DataSourceFactory.create()
        self.login()

    def test_trekking_managers_can_access_data_sources_admin_site(self):
        url = reverse('admin:tourism_datasource_changelist')
        response = self.client.get(url)
        self.assertContains(response, 'datasource/%s' % self.source.id)

    def test_datasource_title_is_translated(self):
        url = reverse('admin:tourism_datasource_add')
        response = self.client.get(url)
        self.assertContains(response, 'title_fr')


class DataSourceListViewTests(TrekkingManagerTest):
    def setUp(self):
        self.source = DataSourceFactory.create(title_it='titolo')
        self.login()
        self.url = reverse('tourism:datasource_list_json')
        self.response = self.client.get(self.url)

    def tearDown(self):
        self.client.logout()

    def test_sources_are_listed_as_json(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response['Content-Type'], 'application/json')

    def test_sources_properties_are_provided(self):
        datasources = json.loads(self.response.content)
        self.assertEqual(len(datasources), 1)
        self.assertEqual(datasources[0]['id'], self.source.id)
        self.assertEqual(datasources[0]['url'], self.source.url)

    def test_sources_respect_request_language(self):
        response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='it-IT')
        self.assertEqual(response.status_code, 200)
        datasources = json.loads(response.content)
        self.assertEqual(datasources[0]['title'],
                         self.source.title_it)

    def test_sources_provide_geojson_absolute_url(self):
        datasources = json.loads(self.response.content)
        self.assertEqual(datasources[0]['geojson_url'],
                         u'/api/datasource/datasource-%s.geojson' % self.source.id)


class DataSourceViewTests(TrekkingManagerTest):
    def setUp(self):
        self.source = DataSourceFactory.create(type=DATA_SOURCE_TYPES.GEOJSON)
        self.url = reverse('tourism:datasource_geojson', kwargs={'pk': self.source.pk})
        self.login()

    def tearDown(self):
        self.client.logout()

    def test_source_is_fetched_upon_view_call(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = '{}'
            self.client.get(self.url)
            mocked.assert_called_with(self.source.url)

    def test_empty_source_response_return_empty_data(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = '{}'
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            datasource = json.loads(response.content)
            self.assertEqual(datasource['features'], [])

    def test_source_is_returned_as_geojson_when_invalid_geojson(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = '{"bar": "foo"}'
            response = self.client.get(self.url)
            geojson = json.loads(response.content)
            self.assertEqual(geojson['type'], 'FeatureCollection')
            self.assertEqual(geojson['features'], [])

    def test_source_is_returned_as_geojson_when_invalid_response(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = '404 page not found'
            response = self.client.get(self.url)
            geojson = json.loads(response.content)
            self.assertEqual(geojson['type'], 'FeatureCollection')
            self.assertEqual(geojson['features'], [])

    def test_source_is_returned_as_geojson_when_network_problem(self):
        with mock.patch('requests.get') as mocked:
            mocked.side_effect = ConnectionError
            response = self.client.get(self.url)
            geojson = json.loads(response.content)
            self.assertEqual(geojson['type'], 'FeatureCollection')
            self.assertEqual(geojson['features'], [])


class DataSourceTourInFranceViewTests(TrekkingManagerTest):
    def setUp(self):
        here = os.path.dirname(__file__)
        filename = os.path.join(here, 'data', 'sit-averyon-02.01.14.xml')
        self.sample = open(filename).read()

        self.source = DataSourceFactory.create(type=DATA_SOURCE_TYPES.TOURINFRANCE)
        self.url = reverse('tourism:datasource_geojson', kwargs={'pk': self.source.pk})
        self.login()

    def tearDown(self):
        self.client.logout()

    def test_source_is_returned_as_geojson_when_tourinfrance(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = "<xml></xml>"
            response = self.client.get(self.url)
            geojson = json.loads(response.content)
            self.assertEqual(geojson['type'], 'FeatureCollection')

    def test_source_is_returned_in_language_request(self):
        with mock.patch('requests.get') as mocked:
            mocked().text = self.sample
            response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE='es-ES')
            geojson = json.loads(response.content)
            feature = geojson['features'][0]
            self.assertEqual(feature['properties']['description'],
                             u'Ubicada en la región minera del Aveyron, nuestra casa rural os permitirá decubrir la naturaleza y el patrimonio industrial de la cuenca de Aubin y Decazeville.')
