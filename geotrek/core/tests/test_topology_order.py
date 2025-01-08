import json
import math
from unittest import skipIf

from django.test import TestCase
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS
from django.contrib.gis.geos import Point, LineString

from geotrek.common.utils import dbnow
from geotrek.core.tests.factories import (PathFactory, PathAggregationFactory,
                                          TopologyFactory)
from geotrek.core.models import Path, Topology, PathAggregation


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class TopologyOrderTest(TestCase):

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


        ⠳ 2a         1b ⠞
          ⠳           ⠞
            ⠳       ⠞
              ⠳   ⠞
                ⠿
              ⠞   ⠳
            ⠞       ⠳
       1a ⠞           ⠳ 2b
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

    def get_list_aggregations(self):
        return [
            (geom.wkt, float(start), float(end), order)
            for geom, start, end, order in
            PathAggregation.objects.values_list('path__geom',
                                                'start_position',
                                                'end_position',
                                                'order')
        ]

    def test_topology_order_0(self):
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
        # Part A

        topo = TopologyFactory.create(paths=[(self.path_1_a, 0, 1),
                                             (self.path_1_b, 0, 1)])
        # Part B
        PathFactory.create(geom=LineString(Point(700000, 6600090), Point(700090, 6600000),
                                           srid=settings.SRID))
        topo.reload()
        self.assertEqual(
            self.get_list_aggregations(),
            [
                ('LINESTRING (700000 6600000, 700045 6600045)', 0.0, 1.0, 0),
                ('LINESTRING (700045 6600045, 700050 6600050)', 0.0, 1.0, 1),
                ('LINESTRING (700050 6600050, 700100 6600100)', 0.0, 1.0, 2),
            ]
        )
