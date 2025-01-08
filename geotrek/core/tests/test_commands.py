from io import StringIO
from unittest import mock, skipIf

from django.conf import settings
from django.contrib.gis.geos import LineString, MultiLineString, Point, GEOSGeometry
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.db import connection, IntegrityError

from geotrek.authent.models import Structure
from geotrek.core.models import Path, PathAggregation
from geotrek.core.tests.factories import PathFactory, TopologyFactory
from geotrek.trekking.tests.factories import POIFactory, TrekFactory
import os


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class RemoveDuplicatePathTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        geom_1 = LineString((0, 0), (1, 0), (2, 0))
        cls.p1 = Path.objects.create(name='First Path', geom=geom_1)
        cls.p2 = Path.objects.create(name='Second Path', geom=geom_1)

        geom_2 = LineString((0, 2), (1, 2), (2, 2))
        cls.p3 = Path.objects.create(name='Third Path', geom=geom_2)
        cls.p4 = Path.objects.create(name='Fourth Path', geom=geom_2)

        geom_3 = LineString((2, 2), (1, 2), (0, 2))
        cls.p5 = Path.objects.create(name='Fifth Path', geom=geom_3)

        geom_4 = LineString((4, 0), (6, 0))

        cls.p6 = Path.objects.create(name='Sixth Path', geom=geom_4)
        cls.p7 = Path.objects.create(name='Seventh Path', geom=geom_4)

        geom_5 = LineString((0, 6), (1, 6), (2, 6))

        cls.p8 = Path.objects.create(name='Eighth Path', geom=geom_5)
        cls.p9 = Path.objects.create(name='Nineth Path', geom=geom_5)

        POIFactory.create(name='POI1', paths=[(cls.p1, 0.5, 0.5)])
        POIFactory.create(name='POI2', paths=[(cls.p2, 0.5, 0.5)])
        POIFactory.create(name='POI3', paths=[(cls.p4, 0.5, 0.5)])

    def test_remove_duplicate_path(self):
        """
        This test check that we remove 1 of the duplicate path and keep ones with topologies.

                poi3 (only on p4)
        +-------o------+                    p5 is reversed.
        p3/p4/p5
                poi1/poi2
        +-------o------+        +--------+
        p1/p2                     p6

        We get at the end p1, p3, p5, p6.
        """
        output = StringIO()
        call_command('remove_duplicate_paths', verbosity=2, stdout=output)

        self.assertEqual(Path.objects.count(), 5)
        self.assertCountEqual((self.p1, self.p3, self.p5, self.p6, self.p8),
                              list(Path.objects.all()))
        self.assertIn("Deleting path",
                      output.getvalue())
        self.assertIn("duplicate paths have been deleted",
                      output.getvalue())

    def test_remove_duplicate_path_visible(self):
        """
        This test check that we remove 1 of the duplicate path and keep ones with topologies.

                poi3 (only on p4)
        +-------o------+                    p5 is reversed.
        p3/p4/p5

        +-------o------+        +--------+
        p1/p2   poi1/poi2       p6

        We get at the end p2, p3, p5, p6.
        """
        output = StringIO()
        self.p1.visible = False
        self.p1.save()
        # Will remove only p1 because not visible
        self.p3.visible = False
        self.p3.save()
        # will remove the second because both of them are not visible
        self.p4.visible = False
        self.p4.save()
        call_command('remove_duplicate_paths', verbosity=2, stdout=output)

        self.assertEqual(Path.include_invisible.count(), 5)
        self.assertEqual(Path.objects.count(), 4)
        self.assertCountEqual((self.p2, self.p3, self.p5, self.p6, self.p8),
                              list(Path.include_invisible.all()))
        self.assertCountEqual((self.p2, self.p5, self.p6, self.p8),
                              list(Path.objects.all()))
        self.assertIn("Deleting path",
                      output.getvalue())
        self.assertIn("duplicate paths have been deleted",
                      output.getvalue())

    def test_remove_duplicate_path_fail(self):
        output = StringIO()
        with mock.patch('geotrek.core.models.Path.delete') as mock_delete:
            mock_delete.side_effect = Exception('An ERROR')
            call_command('remove_duplicate_paths', verbosity=2, stdout=output)
        self.assertIn("An ERROR", output.getvalue())
        self.assertEqual(Path.include_invisible.count(), 9)
        self.assertEqual(Path.objects.count(), 9)
        self.assertIn("0 duplicate paths have been deleted",
                      output.getvalue())


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class LoadPathsCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.filename = os.path.join(os.path.dirname(__file__), 'data', 'paths.geojson')
        cls.structure = Structure.objects.create(name='huh')

    def test_load_paths_without_file(self):
        with self.assertRaisesRegex(CommandError, 'Error: the following arguments are required: file_path'):
            call_command('loadpaths')

    @override_settings(SRID=4326, SPATIAL_EXTENT=(5, 10.0, 5, 11))
    def test_load_paths_out_of_spatial_extent(self):
        call_command('loadpaths', self.filename, srid=4326, verbosity=0)
        self.assertEqual(Path.objects.count(), 0)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, -1, 1, 5))
    def test_load_paths_within_spatial_extent(self):
        call_command('loadpaths', self.filename, srid=4326, verbosity=0)
        self.assertEqual(Path.objects.count(), 1)
        value = Path.objects.first()
        self.assertEqual(value.name, 'lulu')
        self.assertEqual(value.structure, self.structure)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, -1, 1, 5))
    def test_load_paths_comments(self):
        output = StringIO()
        call_command('loadpaths', self.filename, srid=4326, verbosity=2, comment=['comment', 'foo'], stdout=output)
        output = output.getvalue()
        self.assertEqual(Path.objects.count(), 1)
        value = Path.objects.first()
        self.assertEqual(value.name, 'lulu')
        self.assertEqual(value.comments, 'Comment 2</br>foo2')
        self.assertEqual(value.structure, self.structure)
        self.assertIn('The comment %s was added on %s' % (value.comments, value.name), output)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, -1, 1, 5))
    def test_load_paths_intersect_spatial_extent(self):
        output = StringIO()
        call_command('loadpaths', self.filename, '-i', srid=4326, verbosity=2, stdout=output)
        output = output.getvalue()
        self.assertIn('All paths in DataSource will be linked to the structure : %s' % self.structure.name, output)
        self.assertEqual(Path.objects.count(), 1)
        path = Path.objects.first()
        self.assertIn('Create path with pk : %s' % path.pk, output)
        value = Path.objects.first()
        self.assertEqual(value.name, 'lulu')
        self.assertEqual(value.structure, self.structure)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, 0, 4, 2))
    def test_load_paths_intersect_spatial_extent_2(self):
        output = StringIO()
        call_command('loadpaths', self.filename, '-i', srid=4326, verbosity=2,
                     stdout=output)
        output = output.getvalue()
        self.assertIn('All paths in DataSource will be linked to the structure : %s' % self.structure.name, output)
        self.assertEqual(Path.objects.count(), 2)
        paths = Path.objects.all()
        self.assertIn('Create path with pk : %s' % paths[0].pk, output)
        self.assertIn('Create path with pk : %s' % paths[1].pk, output)
        value = Path.objects.first()
        self.assertEqual(value.name, 'lulu')
        self.assertEqual(value.structure, self.structure)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, 0, 4, 2))
    def test_load_paths_not_within_spatial_extent(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'point.geojson')
        call_command('loadpaths', filename, structure=self.structure.name, srid=4326, verbosity=2, stdout=output)
        self.assertRegex(output.getvalue(), "Feature FID 0 in Layer<(point|OGRGeoJSON)>'s geometry is not a Linestring")

    def test_load_paths_fail_bad_srid(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'bad_srid.geojson')
        with self.assertRaisesRegex(CommandError, 'SRID is not well configurate, change/add option srid'):
            call_command('loadpaths', filename, verbosity=0)

    def test_load_paths_with_bad_structure(self):
        with self.assertRaisesRegex(CommandError, "Structure does not match with instance's structures"):
            call_command('loadpaths', self.filename, structure='gr', verbosity=0)

    def test_load_paths_with_multiple_structure(self):
        Structure.objects.create(name='other_structure')
        with self.assertRaisesRegex(CommandError, "There are more than 1 structure and you didn't define the option structure\nUse --structure to define it"):
            call_command('loadpaths', self.filename, verbosity=0)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, 0, 4, 2))
    def test_load_paths_dry(self):
        output = StringIO()
        call_command('loadpaths', self.filename, '-i', dry=True, verbosity=2, stdout=output)
        self.assertIn('2 objects will be create, 0 objects failed;', output.getvalue())
        self.assertEqual(Path.objects.count(), 0)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, 0, 4, 2))
    def test_load_paths_fail_with_dry(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'bad_path.geojson')
        output = StringIO()
        call_command('loadpaths', filename, '-i', dry=True, verbosity=2, stdout=output)
        self.assertIn('0 objects will be create, 1 objects failed;', output.getvalue())
        self.assertEqual(Path.objects.count(), 0)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, 0, 4, 2))
    def test_load_paths_fail_without_dry(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'bad_path.geojson')
        output = StringIO()
        with self.assertRaises(IntegrityError):
            call_command('loadpaths', filename, '-i', verbosity=2, stdout=output)

    @override_settings(SRID=4326, SPATIAL_EXTENT=(-1, -1, 1, 5))
    def test_load_paths_within_spatial_extent_no_srid_geom(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'paths_no_srid.shp')
        call_command('loadpaths', filename, srid=4326, verbosity=0)
        self.assertEqual(Path.objects.count(), 1)
        value = Path.objects.first()
        self.assertEqual(value.name, 'lulu')
        self.assertEqual(value.structure, self.structure)


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class ReorderTopologiesPathAggregationTest(TestCase):

    def assertRecursiveAlmostEqual(self, a, b):
        if type(a) is float:
            assert type(b) is float
            self.assertAlmostEqual(a, b)
        else:
            assert len(a) == len(b)
            for i in range(len(a)):
                self.assertRecursiveAlmostEqual(a[i], b[i])

    def setUp(self):
        """
        ⠳               ⠞
          ⠳           ⠞
            ⠳       ⠞
              ⠳   ⠞
                ⠿
              ⠞   ⠳
            ⠞       ⠳
        1 ⠞           ⠳ 2
        ⠞               ⠳
        """
        self.path_1 = PathFactory.create(geom=LineString(Point(700000, 6600000), Point(700100, 6600100),
                                                         srid=settings.SRID))
        self.path_2 = PathFactory.create(geom=LineString(Point(700000, 6600100), Point(700100, 6600000),
                                                         srid=settings.SRID))
        self.path_1_a = Path.objects.get(geom=LineString(Point(700000, 6600000), Point(700050, 6600050),
                                                         srid=settings.SRID))
        self.path_1_b = Path.objects.get(geom=LineString(Point(700050, 6600050), Point(700100, 6600100),
                                                         srid=settings.SRID))
        self.path_2_a = Path.objects.get(geom=LineString(Point(700000, 6600100), Point(700050, 6600050),
                                                         srid=settings.SRID))
        self.path_2_b = Path.objects.get(geom=LineString(Point(700050, 6600050), Point(700100, 6600000),
                                                         srid=settings.SRID))

    def get_geometries(self, topology):
        geometries = []
        for pathagg in topology.aggregations.all():
            cursor = connection.cursor()
            cursor.execute(f"""SELECT * FROM ST_ASTEXT(ST_SmartLineSubstring('{pathagg.path.geom.wkt}'::geometry,
                                                                              {pathagg.start_position},
                                                                              {pathagg.end_position}
                                                       ))
            """)
            geom = cursor.fetchall()[0][0]
            geometries.append(GEOSGeometry(geom, srid=2154))
        return geometries

    def test_split_reorder_1(self):
        """
        Part A

        ⠳               🡥
          ⠳           🡥
            ⠳       🡥
              ⠳   🡥
                🡥              🡥  Topo 1
              🡥   ⠳            ⠳ Paths (1 2)
            🡥       ⠳
        1 🡥           ⠳ 2
        🡥               ⠳

        Part B

        ⠳               🡥
          ⠳           🡥
        ⠳   ⠳       🡥
          ⠳   ⠳   🡥
             ⠳  🡥              🡥  Topo 1
              🡥   ⠳            ⠳ Paths (1 2 3)
            🡥   ⠳   ⠳
        1 🡥       ⠳   ⠳ 2
        🡥         3 ⠳   ⠳
        """
        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 1), (self.path_1_b, 0, 1)])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        PathFactory.create(geom=LineString(Point(700000, 6600090), Point(700090, 6600000), srid=settings.SRID))
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700045, 6600045), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 0, 1])
        output = StringIO()
        call_command('reorder_topologies', stdout=output)
        self.assertEqual('1 topologies has beeen updated\n', output.getvalue())
        geometries = self.get_geometries(topo)
        self.assertRecursiveAlmostEqual(
            geometries,
            [
                LineString((700000, 6600000), (700045, 6600045), srid=2154),
                LineString((700045, 6600045), (700050, 6600050), srid=2154),
                LineString((700050, 6600050), (700100, 6600100), srid=2154)
            ]
        )
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 2])
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700045, 6600045), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )

    def test_split_reorder_2(self):
        """
        Part A

        ⠳                   🡥
          ⠳               🡥
            ⠳           🡥
              ⠳       🡥
                ⠳   🡥
                  🡥              🡥  Topo 1
                0   ⠳            0  Topo 1 (point)
              X       ⠳          x  Topo 1 (2 directions)
            0           ⠳        ⠳  Paths (1 2)
        1 🡥               ⠳ 2
        🡥                   ⠳

        Part B

        ⠳                   🡥
          ⠳               🡥
            ⠳           🡥
        ⠳     ⠳       🡥
          ⠳     ⠳   🡥
            ⠳     🡥              🡥  Topo 1
              ⠳ 0   ⠳            0  Topo 1 (point)
              X ⠳     ⠳          x  Topo 1 (2 directions)
            0     ⠳     ⠳        ⠳  Paths (1 2 3)
        1 🡥         ⠳ 3   ⠳ 2
        🡥             ⠳     ⠳

        """
        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 0.95),
                                             (self.path_1_a, 0.95, 0.95),
                                             (self.path_1_a, 0.95, 0.5),
                                             (self.path_1_a, 0.5, 0.5),
                                             (self.path_1_a, 0.5, 1),
                                             (self.path_1_b, 0, 1)])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700047.5, 6600047.5), (700025, 6600025), (700050, 6600050),
                       (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        PathFactory.create(geom=LineString(Point(700000, 6600090), Point(700090, 6600000), srid=settings.SRID))
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 0, 1, 2, 2, 3, 4, 4, 5])
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700045, 6600045), (700047.5, 6600047.5), (700045, 6600045), (700025, 6600025),
                       (700045, 6600045), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        call_command('reorder_topologies', verbosity=0)
        geometries = self.get_geometries(topo)
        for geom, expected_geom in zip(
                geometries,
                [
                    LineString((700000, 6600000), (700045, 6600045), srid=2154),
                    LineString((700045, 6600045), (700047.5, 6600047.5), srid=2154),
                    Point(700047.5, 6600047.5, srid=2154),
                    LineString((700047.5, 6600047.5), (700045, 6600045), srid=2154),
                    LineString((700045, 6600045), (700025, 6600025), srid=2154),
                    Point(700025, 6600025, srid=2154),
                    LineString((700025, 6600025), (700045, 6600045), srid=2154),
                    LineString((700045, 6600045), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700100, 6600100), srid=2154)
                ]
        ):
            self.assertRecursiveAlmostEqual(geom, expected_geom)

        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 2, 3, 4, 5, 6, 7, 8])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700045, 6600045), (700047.5, 6600047.5), (700045, 6600045),
                       (700025, 6600025), (700045, 6600045), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )

    def test_split_reorder_3(self):
        """
        Part A

        ⠳                   🡥
          ⠳               🡥
            0           🡥
              X       🡥
                X   🡥
                  X              🡥  Topo 1
                🡥   ⠳            0  Topo 1 (point)
              🡥       ⠳          x  Topo 1 (2 directions)
            🡥           ⠳        ⠳  Paths (1 2)
        1 🡥               ⠳ 2
        🡥                   ⠳

        Part B

        ⠳                   🡥
          ⠳               🡥
            0   ⠞  ⠛    🡥
              X       ⠳
           ⠿    X   🡥   ⠳
            ⠳     X       ⠳          🡥  Topo 1
              ⠳ 🡥   ⠳       ⠳ 3      0  Topo 1 (point)
              🡥 ⠳     ⠳       ⠳      x  Topo 1 (2 directions)
            🡥     ⠳     ⠳            ⠳  Paths (1 2 3)
        1 🡥         ⠳     ⠳ 2
        🡥           3 ⠳     ⠳

        """
        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 1),
                                             (self.path_2_a, 1, 0.1),
                                             (self.path_2_a, 0.1, 0.1),
                                             (self.path_2_a, 0.1, 1),
                                             (self.path_1_b, 0, 1)])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700005, 6600095), (700050, 6600050),
                       (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        PathFactory.create(geom=LineString(Point(700070, 6600000),
                                           Point(700020, 6600050),
                                           Point(700060, 6600090),
                                           Point(700100, 6600050),
                                           srid=settings.SRID))
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700035, 6600035), (700050, 6600050), (700035, 6600065),
                       (700007.1428571428, 6600092.857142857), (700035, 6600065), (700050, 6600050),
                       (700075, 6600075), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 0, 1, 1, 2, 3, 3, 4, 4])
        call_command('reorder_topologies', verbosity=0)
        geometries = self.get_geometries(topo)
        for geom, expected_geom in zip(
                geometries,
                [
                    LineString((700000, 6600000), (700035, 6600035), srid=2154),
                    LineString((700035, 6600035), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700035, 6600065), srid=2154),
                    LineString((700035, 6600065), (700007.142857143, 6600092.85714286), srid=2154),
                    Point(700007.142857143, 6600092.85714286, srid=2154),
                    LineString((700007.142857143, 6600092.85714286), (700035, 6600065), srid=2154),
                    LineString((700035, 6600065), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700075, 6600075), srid=2154),
                    LineString((700075, 6600075), (700100, 6600100), srid=2154)
                ]
        ):
            self.assertRecursiveAlmostEqual(geom, expected_geom)

        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 2, 3, 4, 5, 6, 7, 8])
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700035, 6600035), (700050, 6600050), (700035, 6600065),
                       (700007.1428571428, 6600092.857142857), (700035, 6600065), (700050, 6600050),
                       (700075, 6600075), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )

    def test_split_reorder_4(self):
        """
        Part A

        ⠳                   🡥
          ⠳               🡥
            ⠳           🡥
              0       🡥
                X   🡥
                  X              🡥  Topo 1
                🡥   ⠳            0  Topo 1 (point)
              🡥       ⠳          x  Topo 1 (2 directions)
            🡥           ⠳        ⠳  Paths (1 2)
        1 🡥               ⠳ 2
        🡥                   ⠳

        Part B

        ⠳                   🡥
          ⠳               🡥
            ⠳    ⠞  ⠛   🡥
              ⠞       ⠳
           ⠿    X   🡥   ⠳
            ⠳     X       ⠳          🡥  Topo 1
              ⠳ 🡥   ⠳       ⠳ 3      0  Topo 1 (point)
              🡥 ⠳     ⠳       ⠳      x  Topo 1 (2 directions)
            🡥     ⠳     ⠳            ⠳  Paths (1 2 3)
        1 🡥         ⠳     ⠳ 2
        🡥           3 ⠳     ⠳

        """
        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 1),
                                             (self.path_2_a, 1, 0.5),
                                             (self.path_2_a, 0.5, 0.5),
                                             (self.path_2_a, 0.5, 1),
                                             (self.path_1_b, 0, 1)])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700025, 6600075), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        PathFactory.create(geom=LineString(Point(700070, 6600000),
                                           Point(700020, 6600050),
                                           Point(700060, 6600090),
                                           Point(700100, 6600050),
                                           srid=settings.SRID))
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700035, 6600035), (700050, 6600050), (700035, 6600065), (700050, 6600050),
                       (700075, 6600075), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 0, 1, 3, 4, 4])
        call_command('reorder_topologies', verbosity=0)
        geometries = self.get_geometries(topo)
        for geom, expected_geom in zip(
                geometries,
                [
                    LineString((700000, 6600000), (700035, 6600035), srid=2154),
                    LineString((700035, 6600035), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700035, 6600065), srid=2154),
                    LineString((700035, 6600065), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700075, 6600075), srid=2154),
                    LineString((700075, 6600075), (700100, 6600100), srid=2154)
                ]
        ):
            self.assertRecursiveAlmostEqual(geom, expected_geom)

        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 2, 3, 4, 5])
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700035, 6600035), (700050, 6600050), (700035, 6600065), (700050, 6600050),
                       (700075, 6600075), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )

    def test_split_reorder_5(self):
        """
        Part A

        ⠳                   🡥
          ⠳               🡥
            ⠳           🡥
              0       🡥
                X   🡥
                  X              🡥  Topo 1
                🡥   ⠳            0  Topo 1 (point)
              🡥       ⠳          x  Topo 1 (2 directions)
            🡥           ⠳        ⠳  Paths (1 2)
        1 🡥               ⠳ 2
        🡥                   ⠳

        Part B

        ⠳           🡠 🡠 🡠 🡥
          ⠳       🡧       🡥
            ⠳   🡧       🡥
              0       🡥
            🡧   X   🡥
          🡧       X              🡥  Topo 1
        🡧       🡥   ⠳            0  Topo 1 (points)
              🡥       ⠳          x  Topo 1 (2 directions)
            🡥           ⠳        ⠳  Paths (1 2)
        1 🡥               ⠳ 2
        🡥                   ⠳

        """
        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 1),
                                             (self.path_2_a, 1, 0.5),
                                             (self.path_2_a, 0.5, 0.5),
                                             (self.path_2_a, 0.5, 1),
                                             (self.path_1_b, 0, 1)])
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700025, 6600075), (700050, 6600050), (700100, 6600100), srid=settings.SRID),
            topo.geom
        )
        self.path_1_b.geom = LineString(Point(700050, 6600050), Point(700100, 6600100), Point(700050, 6600100),
                                        Point(700000, 6600050), srid=settings.SRID)
        self.path_1_b.save()
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700025, 6600075), (700050, 6600050), (700100, 6600100),
                       (700050, 6600100), (700025, 6600075), (700000, 6600050), srid=settings.SRID),
            topo.geom
        )
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 1, 2, 2, 2, 3, 3, 4, 4])  # /!\ Duplicated Point
        call_command('reorder_topologies', verbosity=0)
        geometries = self.get_geometries(topo)
        for geom, expected_geom in zip(
                geometries,
                [
                    LineString((700000, 6600000), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700025, 6600075), srid=2154),
                    Point(700025, 6600075, srid=2154),
                    LineString((700025, 6600075), (700050, 6600050), srid=2154),
                    LineString((700050, 6600050), (700100, 6600100), (700050, 6600100), (700025, 6600075), srid=2154),
                    Point(700025, 6600075, srid=2154),
                    LineString((700025, 6600075), (700000, 6600050), srid=2154)
                ]
        ):
            self.assertRecursiveAlmostEqual(geom, expected_geom)

        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 1, 2, 3, 4, 5, 6])
        topo.reload()
        self.assertRecursiveAlmostEqual(
            LineString((700000, 6600000), (700050, 6600050), (700025, 6600075), (700050, 6600050), (700100, 6600100),
                       (700050, 6600100), (700025, 6600075), (700000, 6600050), srid=settings.SRID),
            topo.geom
        )

    def test_split_reorder_fail(self):
        """
        Part A

        ⠳                   🡥
          ⠳               🡥
            ⠳           🡥
        ⠳     0       🡥
          ⠳     🡤   🡥
            ⠳     X              🡥  Topo 1
              ⠳ 🡥   ⠳            0  Topo 1 (point)
              🡥 ⠳     ⠳          x  Topo 1 (2 directions)
            🡥     ⠳     ⠳        ⠳  Paths (1 2)
        1 🡥         ⠳ 3   ⠳ 2
        🡥             ⠳     ⠳

        Part B

        FAILED

        """
        topo = TrekFactory.create(paths=[(self.path_1_a, 0, 1),
                                         (self.path_2_a, 1, 0.5),
                                         (self.path_2_a, 0.5, 0.5),
                                         # (self.path_2_a, 0.5, 1), Doesn't exist in this test => MultiLinestring
                                         (self.path_1_b, 0, 1)])
        expected = MultiLineString(
            LineString((700000, 6600000), (700050, 6600050)),
            LineString((700050, 6600050), (700025, 6600075)),
            LineString((700050, 6600050), (700100, 6600100)),
            srid=settings.SRID
        )
        self.assertRecursiveAlmostEqual(expected, topo.geom)
        PathFactory.create(geom=LineString(Point(700000, 6600090), Point(700090, 6600000), srid=settings.SRID))
        topo.reload()
        expected = MultiLineString(
            LineString((700000, 6600000), (700045, 6600045)),
            LineString((700045, 6600045), (700050, 6600050)),
            LineString((700050, 6600050), (700025, 6600075)),
            LineString((700050, 6600050), (700100, 6600100)),
            srid=settings.SRID)
        self.assertRecursiveAlmostEqual(expected, topo.geom)
        self.assertEqual(list(PathAggregation.objects.filter(topo_object=topo).values_list('order', flat=True)),
                         [0, 0, 1, 2, 3])
        output = StringIO()
        call_command('reorder_topologies', stdout=output)
        self.assertIn(f'Topologies with errors :\nTREK id: {topo.pk}\n', output.getvalue())


class MergePathsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        geom_1 = LineString((0, 0), (1, 1))
        cls.p1 = Path.objects.create(geom=geom_1)
        geom_2 = LineString((1, 1), (2, 2))
        cls.p2 = Path.objects.create(geom=geom_2)
        geom_3 = LineString((2, 2), (3, 3))
        cls.p3 = Path.objects.create(geom=geom_3)
        geom_4 = LineString((2, 2), (6, 1))
        cls.p4 = Path.objects.create(geom=geom_4)
        geom_5 = LineString((3, 3), (4, 4))
        cls.p5 = Path.objects.create(geom=geom_5)
        geom_6 = LineString((4, 4), (5, 5))
        cls.p6 = Path.objects.create(geom=geom_6)
        geom_7 = LineString((5, 5), (6, 6))
        cls.p7 = Path.objects.create(geom=geom_7)
        geom_8 = LineString((6, 6), (7, 7))
        cls.p8 = Path.objects.create(geom=geom_8)
        geom_9 = LineString((7, 7), (8, 8))
        cls.p9 = Path.objects.create(geom=geom_9)
        geom_10 = LineString((6, 1), (4, 1))
        cls.p10 = Path.objects.create(geom=geom_10)
        geom_11 = LineString((4, 1), (4, 0))
        cls.p11 = Path.objects.create(geom=geom_11)
        geom_12 = LineString((4, 1), (6, 1))
        cls.p12 = Path.objects.create(geom=geom_12)
        geom_13 = LineString((6, 6), (7, 5))
        cls.p13 = Path.objects.create(geom=geom_13)
        geom_14 = LineString((8, 8), (9, 9))
        cls.p14 = Path.objects.create(geom=geom_14)
        geom_15 = LineString((5, 3), (4, 1))
        cls.p15 = Path.objects.create(geom=geom_15)
        geom_16 = LineString((7, 5), (8, 5), (8, 6), (7, 6), (7, 5))
        cls.p16 = Path.objects.create(geom=geom_16)

    @override_settings(PATH_SNAPPING_DISTANCE=0, PATH_MERGE_SNAPPING_DISTANCE=0)
    def test_find_and_merge_paths(self):
        # Before call
        #    p1      p2      p3      p5     p6     p7      p8     p9     p14
        # +-------+------+-------+------+-------+------+-------+------+------+
        #                |                             |
        #                |  p4                         |  p13
        #                |                             |
        #                +                             +-------
        #                |                             |       |
        #                |  p10                        |   p16 |
        #          p11   |                             |       |
        #         +------+------+ p15                  --------
        #                |
        #                |  p12
        #                |
        #                +
        self.assertEqual(Path.objects.count(), 16)
        output = StringIO()
        call_command('merge_segmented_paths', stdout=output)
        # After call
        #        p1                     p6                       p14
        # +--------------+-----------------------------+---------------------+
        #                |                             |
        #                |  p4                         |  p13
        #                |                             |
        #                +                             +-------
        #                |                             |       |
        #                |  p10                        |   p16 |
        #          p11   |                             |       |
        #         +------+------+ p15                  --------
        #                |
        #                |  p12
        #                |
        #
        output_str = (f"┌ STEP 1\n"
                      f"├ Merged {self.p2.pk} into {self.p1.pk}\n"
                      f"├ Merged {self.p9.pk} into {self.p14.pk}\n"
                      f"├ Cannot merge {self.p16.pk} and {self.p13.pk}\n"
                      f"├ Merged {self.p8.pk} into {self.p14.pk}\n"
                      f"├ Already discarded {self.p16.pk} and {self.p13.pk}\n"
                      f"└ 3 merges\n"
                      f"┌ STEP 2\n"
                      f"├ Cannot merge {self.p1.pk} and {self.p3.pk}\n"
                      f"├ Merged {self.p3.pk} into {self.p5.pk}\n"
                      f"├ Merged {self.p5.pk} into {self.p6.pk}\n"
                      f"├ Cannot merge {self.p14.pk} and {self.p7.pk}\n"
                      f"└ 2 merges\n"
                      f"┌ STEP 3\n"
                      f"├ Cannot merge {self.p6.pk} and {self.p1.pk}\n"
                      f"├ Cannot merge {self.p6.pk} and {self.p4.pk}\n"
                      f"├ Merged {self.p7.pk} into {self.p6.pk}\n"
                      f"├ Cannot merge {self.p7.pk} and {self.p6.pk}\n"
                      f"├ Cannot merge {self.p7.pk} and {self.p13.pk}\n"
                      f"├ Already discarded {self.p7.pk} and {self.p14.pk}\n"
                      f"├ Cannot merge {self.p10.pk} and {self.p4.pk}\n"
                      f"├ Cannot merge {self.p10.pk} and {self.p11.pk}\n"
                      f"├ Cannot merge {self.p10.pk} and {self.p15.pk}\n"
                      f"├ Cannot merge {self.p12.pk} and {self.p4.pk}\n"
                      f"├ Cannot merge {self.p12.pk} and {self.p11.pk}\n"
                      f"├ Cannot merge {self.p12.pk} and {self.p15.pk}\n"
                      f"├ Already discarded {self.p13.pk} and {self.p7.pk}\n"
                      f"├ Cannot merge {self.p13.pk} and {self.p14.pk}\n"
                      f"├ Already discarded {self.p13.pk} and {self.p16.pk}\n"
                      f"└ 1 merges\n"
                      f"\n"
                      f"--- RAN 6 MERGES - FROM 16 TO 10 PATHS ---\n")
        self.assertEqual(Path.objects.count(), 10)
        self.assertIn(output_str, output.getvalue())
