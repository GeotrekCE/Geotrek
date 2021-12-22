from django.contrib.gis.geos.collections import GeometryCollection
from geotrek.trekking.tests.factories import POIFactory
from django.contrib.gis.geos.point import Point
from django.contrib.gis.geos import Polygon
from geotrek.common.tests.factories import OrganismFactory
from geotrek.outdoor.tests.factories import SiteFactory, RatingScaleFactory, SectorFactory
from django.test import TestCase, override_settings


class SiteTest(TestCase):
    @override_settings(PUBLISHED_BY_LANG=False)
    def test_published_children(self):
        parent = SiteFactory(name='parent')
        SiteFactory(name='child1', parent=parent, published=False)
        SiteFactory(name='child2', parent=parent, published=True)
        self.assertQuerysetEqual(parent.published_children, ['<Site: child2>'])

    def test_published_children_by_lang(self):
        parent = SiteFactory(name='parent')
        SiteFactory(name='child1', parent=parent, published=False)
        SiteFactory(name='child2', parent=parent, published_en=True)
        SiteFactory(name='child3', parent=parent, published_fr=True)
        self.assertQuerysetEqual(parent.published_children, ['<Site: child2>', '<Site: child3>'])


class SiteSuperTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        org_a = OrganismFactory(organism='a')
        org_b = OrganismFactory(organism='b')
        org_c = OrganismFactory(organism='c')
        cls.alone = SiteFactory(
            practice=None
        )
        cls.parent = SiteFactory(
            practice__name='Bbb',
            practice__sector__name='Bxx',
            managers=[org_a, org_b],
            orientation=['N', 'S'],
            wind=['N', 'S']
        )
        cls.child = SiteFactory(
            parent=cls.parent,
            practice__name='Aaa',
            practice__sector__name='Axx',
            managers=[org_b, org_c],
            orientation=['E', 'S'],
            wind=['E', 'S']
        )
        cls.grandchild1 = SiteFactory(
            parent=cls.child,
            practice=cls.parent.practice,
            orientation=cls.parent.orientation,
            wind=cls.parent.wind
        )
        cls.grandchild2 = SiteFactory(
            parent=cls.child,
            practice=None,
            orientation=[],
            wind=[]
        )

    def test_super_practices_descendants(self):
        self.assertQuerysetEqual(self.parent.super_practices, ['<Practice: Aaa>', '<Practice: Bbb>'])

    def test_super_practices_ascendants(self):
        self.assertQuerysetEqual(self.grandchild2.super_practices, [])

    def test_super_sectors_descendants(self):
        self.assertQuerysetEqual(self.parent.super_sectors, ['<Sector: Axx>', '<Sector: Bxx>'])

    def test_super_sectors_ascendants(self):
        self.assertQuerysetEqual(self.grandchild2.super_sectors, [])

    def test_super_orientation_descendants(self):
        self.assertEqual(self.parent.super_orientation, ['N', 'E', 'S'])

    def test_super_orientation_ascendants(self):
        self.assertEqual(self.grandchild2.super_orientation, [])

    def test_super_wind_descendants(self):
        self.assertEqual(self.parent.super_wind, ['N', 'E', 'S'])

    def test_super_wind_ascendants(self):
        self.assertEqual(self.grandchild2.super_wind, [])

    def test_super_managers_descendants(self):
        self.assertQuerysetEqual(self.parent.super_managers,
                                 ['<Organism: a>', '<Organism: b>', '<Organism: b>', '<Organism: c>'])

    def test_super_managers_ascendants(self):
        self.assertQuerysetEqual(self.grandchild2.super_managers, [])

    def test_super_practices_display(self):
        self.assertEqual(self.alone.super_practices_display, "")
        self.assertEqual(self.parent.super_practices_display, "<i>Aaa</i>, Bbb")
        self.assertEqual(self.child.super_practices_display, "Aaa, <i>Bbb</i>")
        self.assertEqual(self.grandchild1.super_practices_display, "Bbb")
        self.assertEqual(self.grandchild2.super_practices_display, "")


class SectorTest(TestCase):
    def test_sector_str(self):
        sector = SectorFactory.create(name='Baz')
        self.assertEqual(str(sector), 'Baz')


class RatingScaleTest(TestCase):
    def test_ratingscale_str(self):
        scale = RatingScaleFactory.create(name='Bar', practice__name='Foo')
        self.assertEqual(str(scale), 'Bar (Foo)')


class ExcludedPOIsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.poi1 = POIFactory()
        cls.poi1.geom = Point(0.5, 0.5, srid=2154)
        cls.poi1.save()
        cls.poi2 = POIFactory()
        cls.poi2.geom = Point(0.5, 0.5, srid=2154)
        cls.poi2.save()
        cls.site = SiteFactory(geom=GeometryCollection(Polygon(((0, 0), (0, 1), (1, 0), (1, 1), (0, 0)), srid=2154)))

    def test_no_poi_excluded(self):
        self.assertEqual(self.site.pois.count(), 2)

    def test_one_poi_excluded(self):
        self.site.pois_excluded.set([self.poi1])
        self.assertEqual(self.site.pois.count(), 1)
