from django.test import TestCase
from django.contrib.gis.geos import LineString, Polygon, MultiPolygon, MultiLineString

from bs4 import BeautifulSoup

from geotrek.core.factories import PathFactory, PathAggregationFactory
from geotrek.common.factories import AttachmentFactory
from geotrek.common.utils.testdata import get_dummy_uploaded_image
from geotrek.land.factories import DistrictFactory, CityFactory
from geotrek.trekking.factories import (POIFactory, TrekFactory, TrekWithPOIsFactory,
                                        WebLinkFactory)
from geotrek.trekking.models import Trek


class TrekTest(TestCase):
    def test_is_publishable(self):
        t = TrekFactory.create()
        t.geom = LineString((0, 0), (1, 1))
        self.assertTrue(t.has_geom_valid())

        t.description_teaser = ''
        self.assertFalse(t.is_complete())
        self.assertFalse(t.is_publishable())
        t.description_teaser = 'ba'
        t.departure = 'zin'
        t.arrival = 'ga'
        self.assertTrue(t.is_complete())
        self.assertTrue(t.is_publishable())

        t.geom = MultiLineString([LineString((0, 0), (1, 1)), LineString((2, 2), (3, 3))])
        self.assertFalse(t.has_geom_valid())
        self.assertFalse(t.is_publishable())

    def test_kml_coordinates_should_be_3d(self):
        trek = TrekWithPOIsFactory.create()
        kml = trek.kml()
        parsed = BeautifulSoup(kml)
        for placemark in parsed.findAll('placemark'):
            coordinates = placemark.find('coordinates')
            tuples = [s.split(',') for s in coordinates.string.split(' ')]
            self.assertTrue(all([len(i) == 3 for i in tuples]))

    def test_pois_types(self):
        trek = TrekWithPOIsFactory.create()
        type0 = trek.pois[0].type
        type1 = trek.pois[1].type
        self.assertEqual(2, len(trek.poi_types))
        self.assertIn(type0, trek.poi_types)
        self.assertIn(type1, trek.poi_types)

    def test_delete_cascade(self):
        p1 = PathFactory.create()
        p2 = PathFactory.create()
        t = TrekFactory.create(no_path=True)
        t.add_path(p1)
        t.add_path(p2)

        # Everything should be all right before delete
        self.assertTrue(t.published)
        self.assertFalse(t.deleted)
        self.assertEqual(t.aggregations.count(), 2)

        # When a path is deleted
        p1.delete()
        t = Trek.objects.get(pk=t.pk)
        self.assertFalse(t.published)
        self.assertFalse(t.deleted)
        self.assertEqual(t.aggregations.count(), 1)

        # Reset published status
        t.published = True
        t.save()

        # When all paths are deleted
        p2.delete()
        t = Trek.objects.get(pk=t.pk)
        self.assertFalse(t.published)
        self.assertTrue(t.deleted)
        self.assertEqual(t.aggregations.count(), 0)

    def test_treks_are_sorted_by_name(self):
        TrekFactory.create(name='Cb')
        TrekFactory.create(name='Ca')
        TrekFactory.create(name='A')
        TrekFactory.create(name='B')
        self.assertEqual([u'A', u'B', u'Ca', u'Cb'],
                         list(Trek.objects.all().values_list('name', flat=True)))


class RelatedObjectsTest(TestCase):
    def test_helpers(self):
        trek = TrekFactory.create(no_path=True)
        p1 = PathFactory.create(geom=LineString((0, 0), (4, 4)))
        p2 = PathFactory.create(geom=LineString((4, 4), (8, 8)))
        poi = POIFactory.create(no_path=True)
        PathAggregationFactory.create(topo_object=trek, path=p1,
                                      start_position=0.5)
        PathAggregationFactory.create(topo_object=trek, path=p2)
        PathAggregationFactory.create(topo_object=poi, path=p1,
                                      start_position=0.6, end_position=0.6)
        # /!\ District are automatically linked to paths at DB level
        d1 = DistrictFactory.create(geom=MultiPolygon(
            Polygon(((-2, -2), (3, -2), (3, 3), (-2, 3), (-2, -2)))))

        # Ensure related objects are accessible
        self.assertItemsEqual(trek.pois, [poi])
        self.assertItemsEqual(poi.treks, [trek])
        self.assertItemsEqual(trek.districts, [d1])

        # Ensure there is no duplicates
        PathAggregationFactory.create(topo_object=trek, path=p1,
                                      end_position=0.5)
        self.assertItemsEqual(trek.pois, [poi])
        self.assertItemsEqual(poi.treks, [trek])

        d2 = DistrictFactory.create(geom=MultiPolygon(
            Polygon(((3, 3), (9, 3), (9, 9), (3, 9), (3, 3)))))
        self.assertItemsEqual(trek.districts, [d1, d2])

    def test_deleted_pois(self):
        p1 = PathFactory.create(geom=LineString((0, 0), (4, 4)))
        trek = TrekFactory.create(no_path=True)
        trek.add_path(p1)
        poi = POIFactory.create(no_path=True)
        poi.add_path(p1, start=0.6, end=0.6)
        self.assertItemsEqual(trek.pois, [poi])
        poi.delete()
        self.assertItemsEqual(trek.pois, [])

    def test_pois_should_be_ordered_by_progression(self):
        p1 = PathFactory.create(geom=LineString((0, 0), (4, 4)))
        p2 = PathFactory.create(geom=LineString((4, 4), (8, 8)))
        self.trek = TrekFactory.create(no_path=True)
        self.trek.add_path(p1)
        self.trek.add_path(p2, order=1)

        self.trek_reverse = TrekFactory.create(no_path=True)
        self.trek_reverse.add_path(p2, start=0.8, end=0, order=0)
        self.trek_reverse.add_path(p1, start=1, end=0.2, order=1)

        self.poi1 = POIFactory.create(no_path=True)
        self.poi1.add_path(p1, start=0.8, end=0.8)
        self.poi2 = POIFactory.create(no_path=True)
        self.poi2.add_path(p1, start=0.3, end=0.3)
        self.poi3 = POIFactory.create(no_path=True)
        self.poi3.add_path(p2, start=0.5, end=0.5)

        pois = self.trek.pois
        self.assertEqual([self.poi2, self.poi1, self.poi3], list(pois))
        pois = self.trek_reverse.pois
        self.assertEqual([self.poi3, self.poi1, self.poi2], list(pois))

    def test_city_departure(self):
        trek = TrekFactory.create(no_path=True)
        p1 = PathFactory.create(geom=LineString((0, 0), (5, 5)))
        trek.add_path(p1)
        self.assertEqual(trek.city_departure, '')

        city1 = CityFactory.create(geom=MultiPolygon(Polygon(((-1, -1), (3, -1), (3, 3),
                                                              (-1, 3), (-1, -1)))))
        city2 = CityFactory.create(geom=MultiPolygon(Polygon(((3, 3), (9, 3), (9, 9),
                                                              (3, 9), (3, 3)))))
        self.assertEqual(trek.cities, [city1, city2])
        self.assertEqual(trek.city_departure, unicode(city1))

    def test_picture(self):
        trek = TrekFactory.create()
        AttachmentFactory.create(obj=trek)
        self.assertEqual(len(trek.attachments), 1)
        self.assertEqual(trek.thumbnail, None)
        self.assertEqual(trek.pictures, [])

        AttachmentFactory.create(obj=trek, attachment_file=get_dummy_uploaded_image())
        self.assertEqual(len(trek.attachments), 2)
        self.assertEqual(len(trek.pictures), 1)
        self.assertNotEqual(trek.thumbnail, None)


class WebLinkTest(TestCase):
    def test_category_serializable(self):
        wl = WebLinkFactory()
        dictcat = wl.serializable_category
        self.assertDictEqual(dictcat,
                             {'pictogram': wl.category.pictogram.url,
                              'label': wl.category.label})
