from unittest import skipIf

from django.conf import settings
from django.contrib.gis.geos import LineString
from django.test import TestCase

from geotrek.core.path_router import PathRouter
from geotrek.core.models import Path
from geotrek.core.tests.factories import PathFactory


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class PathRouterGraphGenerationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.path_router = PathRouter()

    def test_python_graph_from_path(self):
        p_1_1 = (1., 1.)
        p_2_2 = (2., 2.)
        p_3_3 = (3., 3.)
        p_4_4 = (4., 4.)
        p_5_5 = (5., 5.)

        def gen_random_point():
            """Return unique (non-conflicting) point"""
            return ((0., x + 1.) for x in range(10, 100))

        r_point = gen_random_point().__next__

        e_1_2 = PathFactory(geom=LineString(p_1_1, r_point(), p_2_2))
        e_2_3 = PathFactory(geom=LineString(p_2_2, r_point(), p_3_3))

        # Non connex
        e_4_5 = PathFactory(geom=LineString(p_4_4, r_point(), p_5_5))

        graph = {
            'nodes': {
                1: {2: e_1_2.pk},
                2: {1: e_1_2.pk, 3: e_2_3.pk},
                3: {2: e_2_3.pk},
                4: {5: e_4_5.pk},
                5: {4: e_4_5.pk}
            },
            'edges': {
                e_1_2.pk: {'nodes_id': [1, 2], 'length': e_1_2.length, 'id': e_1_2.pk},
                e_2_3.pk: {'nodes_id': [2, 3], 'length': e_2_3.length, 'id': e_2_3.pk},
                e_4_5.pk: {'nodes_id': [4, 5], 'length': e_4_5.length, 'id': e_4_5.pk}
            }
        }

        graph = self.path_router.graph_edges_nodes_of_qs(Path.objects.order_by('id'))
        self.assertDictEqual(graph, graph)

    def test_json_graph_empty(self):
        graph = self.path_router.graph_edges_nodes_of_qs(Path.objects.all())
        self.assertDictEqual({'edges': {}, 'nodes': {}}, graph)

    def test_json_graph_simple(self):
        path = PathFactory(geom=LineString((0, 0), (1, 1)))
        graph = self.path_router.graph_edges_nodes_of_qs(Path.objects.all())
        length = graph['edges'][path.pk].pop('length')
        self.assertDictEqual({'edges': {path.pk: {'id': path.pk, 'nodes_id': [1, 2]}},
                              'nodes': {1: {2: path.pk}, 2: {1: path.pk}}}, graph)
        self.assertAlmostEqual(length, 1.4142135623731)

    def test_json_graph_simple_cached(self):
        path = PathFactory(geom=LineString((0, 0), (1, 1)))
        graph = self.path_router.graph_edges_nodes_of_qs(Path.objects.all())

        length = graph['edges'][path.pk].pop('length')
        self.assertDictEqual({'edges': {path.pk: {'id': path.pk, 'nodes_id': [1, 2]}},
                              'nodes': {1: {2: path.pk}, 2: {1: path.pk}}}, graph)
        self.assertAlmostEqual(length, 1.4142135623731)
