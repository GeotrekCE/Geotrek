from django.test import TestCase
from django.contrib.gis.geos import LineString
from django.contrib.auth.models import User

from geotrek.core.factories import PathFactory
from geotrek.core.graph import graph_edges_nodes_of_qs
from geotrek.core.models import Path


class SimpleGraph(TestCase):

    def setUp(self):
        user = User.objects.create_user('homer', 'h@s.com', 'dooh')
        success = self.client.login(username=user.username, password='dooh')
        self.assertTrue(success)

    def test_python_graph_from_path(self):
        p_1_1 = (1., 1.)
        p_2_2 = (2., 2.)
        p_3_3 = (3., 3.)
        p_4_4 = (4., 4.)
        p_5_5 = (5., 5.)

        def gen_random_point():
            """Return unique (non-conflicting) point"""
            return ((0., x + 1.) for x in xrange(10, 100))

        r_point = gen_random_point().next

        e_1_2 = PathFactory(geom=LineString(p_1_1, r_point(), p_2_2))
        e_2_3 = PathFactory(geom=LineString(p_2_2, r_point(), p_3_3))

        # Non connex
        e_4_5 = PathFactory(geom=LineString(p_4_4, r_point(), p_5_5))

        graph = {
            'nodes': {
                1: {2: 1},
                2: {1: 1, 3: 2},
                3: {2: 2},
                4: {5: 3},
                5: {4: 3}
            },
            'edges': {
                e_1_2.pk: {'nodes_id': [1, 2], 'length': e_1_2.length, 'id': e_1_2.pk},
                e_2_3.pk: {'nodes_id': [2, 3], 'length': e_2_3.length, 'id': e_2_3.pk},
                e_4_5.pk: {'nodes_id': [4, 5], 'length': e_4_5.length, 'id': e_4_5.pk}
            }
        }

        computed_graph = graph_edges_nodes_of_qs(Path.objects.all())
        self.assertDictEqual(computed_graph, graph)
