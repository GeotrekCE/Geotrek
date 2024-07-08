import re
import json
from unittest import mock, skipIf

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import LineString, MultiPolygon, Point, Polygon
from django.core.cache import caches
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mapentity.tests.factories import UserFactory

from geotrek.authent.tests.base import AuthentFixturesTest
from geotrek.authent.tests.factories import PathManagerFactory, StructureFactory
from geotrek.common.tests import CommonTest
from geotrek.core.models import Path, PathSource, Trail
from geotrek.core.tests.factories import (
    ComfortFactory,
    PathFactory,
    StakeFactory,
    TopologyFactory,
    TrailFactory,
)
from geotrek.infrastructure.tests.factories import InfrastructureFactory
from geotrek.maintenance.tests.factories import InterventionFactory
from geotrek.signage.tests.factories import SignageFactory
from geotrek.trekking.tests.factories import POIFactory, ServiceFactory, TrekFactory
from geotrek.zoning.tests.factories import (
    CityFactory,
    DistrictFactory,
    RestrictedAreaFactory,
    RestrictedAreaTypeFactory,
)


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class MultiplePathViewsTest(AuthentFixturesTest, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PathManagerFactory.create(password='booh')

    def setUp(self):
        self.login()

    def login(self):
        self.client.force_login(user=self.user)

    def logout(self):
        self.client.logout()

    def test_show_delete_multiple_path_in_list(self):
        path_1 = PathFactory.create(name="path_1", geom=LineString((0, 0), (4, 0)))
        PathFactory.create(name="path_2", geom=LineString((2, 2), (2, -2)))
        POIFactory.create(paths=[(path_1, 0, 0)])
        response = self.client.get(reverse('core:path_list'))
        self.assertContains(response, '<a href="#delete" id="btn-delete" role="button">')

    def test_delete_view_multiple_path(self):
        path_1 = PathFactory.create(name="path_1", geom=LineString((0, 0), (4, 0)))
        path_2 = PathFactory.create(name="path_2", geom=LineString((2, 2), (2, -2)))
        response = self.client.get(reverse('core:multiple_path_delete', args=['%s,%s' % (path_1.pk, path_2.pk)]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Do you really wish to delete')

    def test_delete_view_multiple_path_one_wrong_structure(self):
        other_structure = StructureFactory(name="Other")
        path_1 = PathFactory.create(name="path_1", geom=LineString((0, 0), (4, 0)))
        path_2 = PathFactory.create(name="path_2", geom=LineString((2, 2), (2, -2)), structure=other_structure)
        POIFactory.create(paths=[(path_1, 0, 0)])
        response = self.client.get(reverse('core:multiple_path_delete', args=['%s,%s' % (path_1.pk, path_2.pk)]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:path_list'))
        self.assertIn(response.content, b'Access to the requested resource is restricted by structure.')
        self.assertEqual(Path.objects.count(), 4)

    def test_delete_multiple_path(self):
        path_1 = PathFactory.create(name="path_1", geom=LineString((0, 0), (4, 0)))
        path_2 = PathFactory.create(name="path_2", geom=LineString((2, 2), (2, -2)))
        POIFactory.create(paths=[(path_1, 0, 0)], name="POI_1")
        InfrastructureFactory.create(paths=[(path_1, 0, 1)], name="INFRA_1")
        signage = SignageFactory.create(paths=[(path_1, 0, 1)], name="SIGNA_1")
        TrailFactory.create(paths=[(path_2, 0, 1)], name="TRAIL_1")
        ServiceFactory.create(paths=[(path_2, 0, 1)])
        InterventionFactory.create(target=signage, name="INTER_1")
        response = self.client.get(reverse('core:multiple_path_delete', args=['%s,%s' % (path_1.pk, path_2.pk)]))
        self.assertContains(response, "POI_1")
        self.assertContains(response, "INFRA_1")
        self.assertContains(response, "SIGNA_1")
        self.assertContains(response, "TRAIL_1")
        self.assertContains(response, "Service type")
        self.assertContains(response, "INTER_1")
        response = self.client.post(reverse('core:multiple_path_delete', args=['%s,%s' % (path_1.pk, path_2.pk)]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Path.objects.count(), 2)
        self.assertEqual(Path.objects.filter(pk__in=[path_1.pk, path_2.pk]).count(), 0)


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class PathViewsTest(CommonTest):
    model = Path
    modelfactory = PathFactory
    userfactory = PathManagerFactory
    expected_json_geom = {
        'type': 'LineString',
        'coordinates': [[3.0, 46.5], [3.001304, 46.5009004]],
    }
    length = 141.4
    extra_column_list = ['length_2d', 'eid']
    expected_column_list_extra = ['id', 'checkbox', 'name', 'length', 'length_2d', 'eid']
    expected_column_formatlist_extra = ['id', 'length_2d', 'eid']

    def get_expected_geojson_geom(self):
        return self.expected_json_geom

    def get_expected_geojson_attrs(self):
        return {
            'id': self.obj.pk,
            'name': self.obj.name,
            'draft': self.obj.draft
        }

    def get_expected_datatables_attrs(self):
        return {
            'checkbox': self.obj.checkbox_display,
            'id': self.obj.pk,
            'length': 141.4,
            'length_2d': 141.4,
            'name': self.obj.name_display
        }

    def get_bad_data(self):
        return {'geom': '{"geom": "LINESTRING (0.0 0.0, 1.0 1.0)"}'}, _("Linestring invalid snapping.")

    def get_good_data(self):
        return {
            'name': '',
            'stake': '',
            'comfort': ComfortFactory.create().pk,
            'trail': '',
            'comments': '',
            'departure': '',
            'arrival': '',
            'source': '',
            'valid': 'on',
            'geom': '{"geom": "LINESTRING (99.0 89.0, 100.0 88.0)", "snap": [null, null]}',
        }

    def _post_add_form(self):
        # Avoid overlap, delete all !
        for p in Path.objects.all():
            p.delete()
        super()._post_add_form()

    def get_route_geometry(self, body):
        return self.client.post(reverse('core:path-drf-route-geometry'), body, content_type='application/json')

    def test_draft_permission_detail(self):
        path = PathFactory(name="DRAFT_PATH", draft=True)
        user = UserFactory(password='booh')
        p = user.profile
        p.save()
        perm_add_draft_path = Permission.objects.get(codename='add_draft_path')
        perm_delete_draft_path = Permission.objects.get(codename='delete_draft_path')
        perm_change_draft_path = Permission.objects.get(codename='change_draft_path')
        perm_read_path = Permission.objects.get(codename='read_path')
        user.user_permissions.add(perm_delete_draft_path)
        user.user_permissions.add(perm_read_path)
        user.user_permissions.add(perm_change_draft_path)
        user.user_permissions.add(perm_add_draft_path)
        self.client.force_login(user=user)
        response = self.client.get(path.get_update_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, path.get_delete_url())

    def test_structurerelated_filter(self):
        def test_structure(structure, stake):
            user = self.userfactory(password='booh')
            p = user.profile
            p.structure = structure
            p.save()
            success = self.client.login(username=user.username, password='booh')
            self.assertTrue(success)
            response = self.client.get(Path.get_add_url())
            self.assertEqual(response.status_code, 200)
            self.assertTrue('form' in response.context)
            form = response.context['form']
            self.assertTrue('stake' in form.fields)
            stakefield = form.fields['stake']
            self.assertTrue((stake.pk, str(stake)) in stakefield.choices)
            self.client.logout()
        # Test for two structures
        s1 = StructureFactory.create()
        s2 = StructureFactory.create()
        st1 = StakeFactory.create(structure=s1)
        StakeFactory.create(structure=s1)
        st2 = StakeFactory.create(structure=s2)
        StakeFactory.create(structure=s2)
        test_structure(s1, st1)
        test_structure(s2, st2)

    def test_structurerelated_filter_with_none(self):
        s1 = StructureFactory.create()
        s2 = StructureFactory.create()
        st0 = StakeFactory.create(structure=None)
        st1 = StakeFactory.create(structure=s1)
        st2 = StakeFactory.create(structure=s2)
        user = self.userfactory(password='booh')
        p = user.profile
        p.structure = s1
        p.save()
        self.client.force_login(user=user)
        response = self.client.get(Path.get_add_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        form = response.context['form']
        self.assertTrue('stake' in form.fields)
        stakefield = form.fields['stake']
        self.assertTrue((st0.pk, str(st0)) in stakefield.choices)
        self.assertTrue((st1.pk, str(st1)) in stakefield.choices)
        self.assertFalse((st2.pk, str(st2)) in stakefield.choices)

    def test_set_structure_with_permission_object_linked_none_structure(self):
        if not hasattr(self.model, 'structure'):
            return
        perm = Permission.objects.get(codename='can_bypass_structure')
        self.user.user_permissions.add(perm)
        structure = StructureFactory()
        st0 = StakeFactory.create(structure=None)
        self.assertNotEqual(structure, self.user.profile.structure)
        data = self.get_good_data()
        data['stake'] = st0.pk
        data['structure'] = self.user.profile.structure.pk
        response = self.client.post(self._get_add_url(), data)
        self.assertEqual(response.status_code, 302)
        obj = self.model.objects.last()
        self.assertEqual(obj.structure, self.user.profile.structure)

    def test_basic_format(self):
        self.modelfactory.create()
        self.modelfactory.create(name="ãéè")
        super().test_basic_format()

    def test_path_form_is_not_valid_if_no_geometry_provided(self):
        data = self.get_good_data()
        data['geom'] = ''
        response = self.client.post(Path.get_add_url(), data)
        self.assertEqual(response.status_code, 200)

    def test_manager_can_delete(self):
        path = PathFactory()
        response = self.client.get(path.get_detail_url())
        self.assertEqual(response.status_code, 200)
        response = self.client.post(path.get_delete_url())
        self.assertEqual(response.status_code, 302)

    def test_delete_show_topologies(self):
        path = PathFactory(name="PATH_AB", geom=LineString((0, 0), (4, 0)))
        poi = POIFactory.create(name='POI', paths=[(path, 0.5, 0.5)])
        trail = TrailFactory.create(name='Trail', paths=[(path, 0.1, 0.2)])
        trek = TrekFactory.create(name='Trek', paths=[(path, 0.2, 0.3)])
        service = ServiceFactory.create(paths=[(path, 0.2, 0.3)], type__name='ServiceType')
        signage = SignageFactory.create(name='Signage', paths=[(path, 0.2, 0.2)])
        infrastructure = InfrastructureFactory.create(name='Infrastructure', paths=[(path, 0.2, 0.2)])
        intervention1 = InterventionFactory.create(target=signage, name='Intervention1')
        t = TopologyFactory.create(paths=[(path, 0.2, 0.5)])
        intervention2 = InterventionFactory.create(target=t, name='Intervention2')
        response = self.client.get(path.get_delete_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Different topologies are linked with this path')
        self.assertContains(response, '<a href="/poi/%d/">POI</a>' % poi.pk)
        self.assertContains(response, '<a href="/trail/%d/">Trail</a>' % trail.pk)
        self.assertContains(response, '<a href="/trek/%d/">Trek</a>' % trek.pk)
        self.assertContains(response, '<a href="/service/%d/">ServiceType</a>' % service.pk)
        self.assertContains(response, '<a href="/signage/%d/">Signage</a>' % signage.pk)
        self.assertContains(response, '<a href="/infrastructure/%d/">Infrastructure</a>' % infrastructure.pk)
        self.assertContains(response, '<a href="/intervention/%d/">Intervention1</a>' % intervention1.pk)
        self.assertContains(response, '<a href="/intervention/%d/">Intervention2</a>' % intervention2.pk)

    def test_elevation_area_json(self):
        path = self.modelfactory.create()
        url = '/api/en/paths/{pk}/dem.json'.format(pk=path.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_sum_path_zero(self):
        response = self.client.get('/api/path/drf/paths/filter_infos.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '0 (0 km)')

    def test_sum_path_two(self):
        PathFactory()
        PathFactory()
        response = self.client.get('/api/path/drf/paths/filter_infos.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '2 (0.3 km)')

    def test_sum_path_filter_cities(self):
        p1 = PathFactory(geom=LineString((0, 0), (0, 1000), srid=settings.SRID))
        city = CityFactory(code='09000', geom=MultiPolygon(Polygon(((200, 0), (300, 0), (300, 100), (200, 100), (200, 0)), srid=settings.SRID)))
        city2 = CityFactory(code='09001', geom=MultiPolygon(
            Polygon(((0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)), srid=settings.SRID)))
        self.assertEqual(len(p1.cities), 1)
        response = self.client.get('/api/path/drf/paths/filter_infos.json?city=%s' % city.code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '0 (0 km)')
        response = self.client.get('/api/path/drf/paths/filter_infos.json?city=%s' % city2.code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '1 (1.0 km)')

    def test_sum_path_filter_districts(self):
        p1 = PathFactory(geom=LineString((0, 0), (0, 1000), srid=settings.SRID))
        district = DistrictFactory(geom=MultiPolygon(Polygon(((200, 0), (300, 0), (300, 100), (200, 100), (200, 0)), srid=settings.SRID)))
        district2 = DistrictFactory(geom=MultiPolygon(
            Polygon(((0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)), srid=settings.SRID)))
        self.assertEqual(len(p1.districts), 1)
        response = self.client.get('/api/path/drf/paths/filter_infos.json?district=%s' % district.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '0 (0 km)')
        response = self.client.get('/api/path/drf/paths/filter_infos.json?district=%s' % district2.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], '1 (1.0 km)')

    def test_merge_fails_parameters(self):
        """
        Should fail if path[] length != 2
        """
        p1 = PathFactory.create()
        p2 = PathFactory.create()
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk]})
        self.assertEqual({'error': 'You should select two paths'}, response.json())

        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p1.pk, p2.pk]})
        self.assertEqual({'error': 'You should select two paths'}, response.json())

    def test_merge_fails_donttouch(self):
        p3 = PathFactory.create(name="AB", geom=LineString((0, 0), (1, 0)))
        p4 = PathFactory.create(name="BC", geom=LineString((500, 0), (1000, 0)))

        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p3.pk, p4.pk]})
        self.assertEqual({'error': 'No matching points to merge paths found'}, response.json())

    def test_merge_fails_other_path_intersection_less_than_snapping(self):
        """
        Merge should fail if other path share merge intersection

                          |
                          C
                          |

        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((11, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((10, 1), (10, 10)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        json_response = response.json()
        self.assertIn('error', json_response)
        self.assertEqual(json_response['error'], "You can't merge 2 paths with a 3rd path in the intersection")

    def test_merge_fails_other_path_intersection(self):
        """
        Merge should fail if other path share merge intersection

                          |
                          C
                          |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((10, 0), (10, 10)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        json_response = response.json()
        self.assertIn('error', json_response)
        self.assertEqual(json_response['error'], "You can't merge 2 paths with a 3rd path in the intersection")

    def test_merge_fails_other_path_intersection_2(self):
        """
        Merge should fail if other path share merge intersection

                          |
                          C (reversed)
                          |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((10, 10), (10, 0)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        json_response = response.json()
        self.assertIn('error', json_response)
        self.assertEqual(json_response['error'], "You can't merge 2 paths with a 3rd path in the intersection")

    def test_merge_fails_other_path_intersection_3(self):
        """
        Merge should fail if other path share merge intersection

        |--------C--------|
        C                 C
        |                 |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((0, 0), (0, 10), (10, 10), (10, 0)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        json_response = response.json()
        self.assertIn('error', json_response)
        self.assertEqual(json_response['error'], "You can't merge 2 paths with a 3rd path in the intersection")

    def test_merge_not_fail_draftpath_intersection(self):
        """
        Merge should not fail
                          .
                          C (draft)
                          .
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((10, 0), (10, 10)), draft=True)
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        self.assertIn('success', response.json())

    def test_merge_not_fail_start_point_end_point(self):
        """
        Merge should not fail
        |
        C
        |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((0, 0), (0, 10)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        self.assertIn('success', response.json())

    def test_merge_not_fail_start_point_end_point_2(self):
        """
        Merge should not fail
        |
        C (reversed)
        |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((0, 10), (0, 0)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        self.assertIn('success', response.json())

    def test_merge_not_fail_start_point_end_point_3(self):
        """
        Merge should not fail
                                                  |
                                                  C
                                                  |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((20, 0), (20, 10)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        self.assertIn('success', response.json())

    def test_merge_not_fail_start_point_end_point_4(self):
        """
        Merge should not fail
                                                  |
                                                  C (reversed)
                                                  |
        |--------A--------|-----------B-----------|

        """
        path_a = PathFactory.create(name="A", geom=LineString((0, 0), (10, 0)))
        path_b = PathFactory.create(name="B", geom=LineString((10, 0), (20, 0)))
        PathFactory.create(name="C", geom=LineString((20, 10), (20, 0)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [path_a.pk, path_b.pk]})
        self.assertIn('success', response.json())

    def test_merge_works(self):
        p1 = PathFactory.create(name="AB", geom=LineString((0, 0), (1, 0)))
        p2 = PathFactory.create(name="BC", geom=LineString((1, 0), (2, 0)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p2.pk]})
        self.assertIn('success', response.json())

    def test_merge_works_wrong_structure(self):
        other_structure = StructureFactory(name="Other")
        p1 = PathFactory.create(name="AB", geom=LineString((0, 0), (1, 0)))
        p2 = PathFactory.create(name="BC", geom=LineString((1, 0), (2, 0)), structure=other_structure)
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p2.pk]})
        self.assertEqual({'error': "You don't have the right to change these paths"}, response.json())

    def test_merge_works_other_line(self):
        p1 = PathFactory.create(name="AB", geom=LineString((0, 0), (1, 0)))
        p2 = PathFactory.create(name="BC", geom=LineString((1, 0), (2, 0)))

        PathFactory.create(name="CD", geom=LineString((2, 1), (3, 1)))
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p2.pk]})
        self.assertIn('success', response.json())

    def test_merge_fails_draft_with_nodraft(self):
        """
            Draft               Not Draft
        A---------------B + C-------------------D

        Do not merge !
        """
        p1 = PathFactory.create(name="PATH_AB", geom=LineString((0, 1), (10, 1)), draft=True)
        p2 = PathFactory.create(name="PATH_CD", geom=LineString((10, 1), (20, 1)), draft=False)
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p2.pk]})
        self.assertIn('error', response.json())

    def test_merge_ok_draft_with_draft(self):
        """
            Draft               Draft
        A---------------B + C-------------------D

        Merge !
        """
        p1 = PathFactory.create(name="PATH_AB", geom=LineString((0, 1), (10, 1)), draft=True)
        p2 = PathFactory.create(name="PATH_CD", geom=LineString((10, 1), (20, 1)), draft=True)
        response = self.client.post(reverse('core:path-drf-merge-path'), {'path[]': [p1.pk, p2.pk]})
        self.assertIn('success', response.json())

    def test_structure_is_not_changed_with_permission_error(self):
        perm = Permission.objects.get(codename='can_bypass_structure')
        self.user.user_permissions.add(perm)
        structure = StructureFactory()
        structure_2 = StructureFactory()
        source = PathSource.objects.create(source="Source_1", structure=structure)
        self.assertNotEqual(structure, self.user.profile.structure)
        obj = self.modelfactory.create(structure=structure)
        data = self.get_good_data().copy()
        data['source'] = source.pk
        data['structure'] = structure_2.pk
        response = self.client.post(obj.get_update_url(), data)
        self.assertContains(response, "Please select a choice related to all structures")

    def test_restricted_area_urls_fragment(self):
        area_type = RestrictedAreaTypeFactory(name="Test")
        obj = self.modelfactory()
        response = self.client.get(obj.get_detail_url())
        self.assertNotContains(response, '/api/restrictedarea/type/{}/restrictedarea.geojson'.format(area_type.pk))

        self.restricted_area = RestrictedAreaFactory(area_type=area_type, name="Tel",
                                                     geom=MultiPolygon(Polygon(((0, 0), (300, 0), (300, 100), (200, 100), (0, 0)),
                                                                               srid=settings.SRID)))
        response = self.client.get(obj.get_detail_url())
        self.assertContains(response, '/api/restrictedarea/type/{}/restrictedarea.geojson'.format(area_type.pk))

    def test_draft_path_layer(self):
        obj = self.modelfactory(draft=False)
        self.modelfactory(draft=False)
        self.modelfactory(draft=True)
        response = self.client.get(obj.get_layer_url(), {"_no_draft": "true"})
        self.assertEqual(len(response.json()['features']), 2)

    def test_draft_path_layer_cache(self):
        """

        This test check draft path's cache is not the same as path's cache and works independently
        """
        cache = caches[settings.MAPENTITY_CONFIG['GEOJSON_LAYERS_CACHE_BACKEND']]

        obj = self.modelfactory(draft=False)
        self.modelfactory(draft=True)

        with self.assertNumQueries(4):
            response = self.client.get(obj.get_layer_url(), {"_no_draft": "true"})
        self.assertEqual(len(response.json()['features']), 1)

        # We check the content was created and cached with no_draft key
        # We check that any cached content can be found with no_draft (we still didn't ask for it)
        last_update = Path.no_draft_latest_updated()
        last_update_draft = Path.latest_updated()
        geojson_lookup = 'en_path_%s_nodraft_json_layer' % last_update.strftime('%y%m%d%H%M%S%f')
        geojson_lookup_last_update_draft = 'en_path_%s_json_layer' % last_update_draft.strftime('%y%m%d%H%M%S%f')
        content = cache.get(geojson_lookup)
        content_draft = cache.get(geojson_lookup_last_update_draft)

        self.assertEqual(response.content, content.content)
        self.assertIsNone(content_draft)

        # We have 1 less query because the generation of paths was cached
        with self.assertNumQueries(3):
            self.client.get(obj.get_layer_url(), {"_no_draft": "true"})

        self.modelfactory(draft=True)

        # Cache was not updated, the path was a draft
        with self.assertNumQueries(3):
            self.client.get(obj.get_layer_url(), {"_no_draft": "true"})

        self.modelfactory(draft=False)

        # Cache was updated, the path was not a draft : we get 7 queries
        with self.assertNumQueries(4):
            self.client.get(obj.get_layer_url(), {"_no_draft": "true"})

    def test_path_layer_cache(self):
        """

        This test check path's cache is not the same as draft path's cache and works independently
        """
        cache = caches[settings.MAPENTITY_CONFIG['GEOJSON_LAYERS_CACHE_BACKEND']]

        obj = self.modelfactory(draft=False)
        self.modelfactory(draft=True)

        with self.assertNumQueries(4):
            response = self.client.get(obj.get_layer_url())
        self.assertEqual(len(response.json()['features']), 2)

        # We check the content was created and cached without no_draft key
        # We check that any cached content can be found without no_draft (we still didn't ask for it)
        last_update_no_draft = Path.no_draft_latest_updated()
        last_update = Path.latest_updated()
        geojson_lookup_no_draft = 'en_path_%s_nodraft_json_layer' % last_update_no_draft.strftime('%y%m%d%H%M%S%f')
        geojson_lookup = 'en_path_%s_json_layer' % last_update.strftime('%y%m%d%H%M%S%f')
        content_no_draft = cache.get(geojson_lookup_no_draft)
        content = cache.get(geojson_lookup)

        self.assertIsNone(content_no_draft)
        self.assertEqual(response.content, content.content)

        # We have 1 less query because the generation of paths was cached
        with self.assertNumQueries(3):
            self.client.get(obj.get_layer_url())

        self.modelfactory(draft=True)

        # Cache is updated when we add a draft path
        with self.assertNumQueries(4):
            self.client.get(obj.get_layer_url())

        self.modelfactory(draft=False)

        # Cache is updated when we add a path
        with self.assertNumQueries(4):
            self.client.get(obj.get_layer_url())

    def test_route_geometry_fail_no_steps_array(self):
        response = self.get_route_geometry({})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_empty_steps_array(self):
        response = self.get_route_geometry({"steps": []})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_one_step(self):
        response = self.get_route_geometry({"steps": [{"lat": 48.866667, "lng": 2.333333}]})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_no_lat(self):
        response = self.get_route_geometry({"steps": [{"lng": 2.333333}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_no_lng(self):
        response = self.get_route_geometry({"steps": [{"lat": 48.866667}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_incorrect_lat(self):
        response = self.get_route_geometry({"steps": [{"lat": 1000, "lng": 2.333333}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)
        response = self.get_route_geometry({"steps": [{"lat": "abc", "lng": 2.333333}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_incorrect_lng(self):
        response = self.get_route_geometry({"steps": [{"lat": 48.866667, "lng": 1000}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)
        response = self.get_route_geometry({"steps": [{"lat": 48.866667, "lng": "abc"}, {"lat": 47.866667, "lng": 1.333333}]})
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_steps_not_on_paths(self):
        path_geom = LineString([
            [1.3664246, 43.4569065],
            [1.6108704, 43.4539158],
        ], srid=settings.API_SRID)
        path_geom.transform(settings.SRID)
        PathFactory(geom=path_geom)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 40.5267991, "lng": 0.5305685},
                {"lat": 40.5266465, "lng": 0.5765381}
            ]
        })
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_fail_paths_not_linked(self):
        pathGeom1 = LineString([
            [1.3664246, 43.4569065],
            [1.6108704, 43.4539158],
        ], srid=settings.API_SRID)
        pathGeom1.transform(settings.SRID)
        PathFactory(geom=pathGeom1)

        pathGeom2 = LineString([
            [1.5305685, 43.5267991],
            [1.5765381, 43.5266465],
        ], srid=settings.API_SRID)
        pathGeom2.transform(settings.SRID)
        PathFactory(geom=pathGeom2)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 43.4569065, "lng": 1.3664246},
                {"lat": 43.5266465, "lng": 1.5765381}
            ]
        })
        self.assertEqual(response.status_code, 400)

    def test_route_geometry_not_fail_no_via_point_one_path(self):
        path_geom = LineString([
            [1.3664246, 43.4569065],
            [1.6108704, 43.4539158],
        ], srid=settings.API_SRID)
        path_geom.transform(settings.SRID)
        PathFactory(geom=path_geom)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 43.456434372150945, "lng": 1.4050149210509666},
                {"lat": 43.45443525706161, "lng": 1.568413282119847}
            ]
        })
        self.assertEqual(response.status_code, 200)
        geometries = response.data.get('geojson').get('geometries')
        self.assertEqual(len(geometries), 1)
        self.assertEqual(len(geometries[0].get('coordinates')), 2)
        for coords in geometries[0].get('coordinates'):
            self.assertEqual(len(coords), 2)
        serialized = response.data.get('serialized')
        self.assertEqual(len(serialized), 1)
        self.assertEqual(len(serialized[0].get('positions').items()), 1)
        self.assertEqual(len(serialized[0].get('positions').get(0)), 2)
        self.assertEqual(len(serialized[0].get('paths')), 1)

    def test_route_geometry_not_fail_no_via_point_several_paths(self):
        pathGeom1 = LineString([
            [1.3904572, 43.5271443],
            [1.4451303, 43.5270311],
        ], srid=settings.API_SRID)
        pathGeom1.transform(settings.SRID)
        PathFactory(geom=pathGeom1)

        pathGeom2 = LineString([
            [1.4447021, 43.5803909],
            [1.4451303, 43.5270311],
        ], srid=settings.API_SRID)
        pathGeom2.transform(settings.SRID)
        PathFactory(geom=pathGeom2)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 43.5271443, "lng": 1.3904572},
                {"lat": 43.5803909, "lng": 1.4447021}
            ]
        })
        self.assertEqual(response.status_code, 200)
        geometries = response.data.get('geojson').get('geometries')
        self.assertEqual(len(geometries), 1)
        self.assertEqual(len(geometries[0].get('coordinates')), 3)
        for coords in geometries[0].get('coordinates'):
            self.assertEqual(len(coords), 2)
        serialized = response.data.get('serialized')
        self.assertEqual(len(serialized), 1)
        self.assertEqual(len(serialized[0].get('positions').items()), 2)
        self.assertEqual(len(serialized[0].get('positions').get(0)), 2)
        self.assertEqual(len(serialized[0].get('positions').get(1)), 2)
        self.assertEqual(len(serialized[0].get('paths')), 2)

    def test_route_geometry_not_fail_with_via_point_one_path(self):
        path_geom = LineString([
            [1.3664246, 43.4569065],
            [1.6108704, 43.4539158],
        ], srid=settings.API_SRID)
        path_geom.transform(settings.SRID)
        PathFactory(geom=path_geom)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 43.45672005573014, "lng": 1.3816640340701447},
                {"lat": 43.45549487037786, "lng": 1.4818060951734013},
                {"lat": 43.4543343323152, "lng": 1.5766622578279499}
            ]
        })

        self.assertEqual(response.status_code, 200)
        geometries = response.data.get('geojson').get('geometries')
        self.assertEqual(len(geometries), 2)
        for geom in geometries:
            self.assertEqual(len(geom.get('coordinates')), 2)
            for coords in geom.get('coordinates'):
                self.assertEqual(len(coords), 2)
        serialized = response.data.get('serialized')
        self.assertEqual(len(serialized), 2)
        for ser in serialized:
            self.assertEqual(len(ser.get('positions').items()), 1)
            self.assertEqual(len(ser.get('positions').get(0)), 2)
            self.assertEqual(len(ser.get('paths')), 1)

    def test_route_geometry_not_fail_with_via_points_several_paths(self):
        pathGeom1 = LineString([
            [1.4451303, 43.5270311],
            [1.5305685, 43.5267991],
        ], srid=settings.API_SRID)
        pathGeom1.transform(settings.SRID)
        PathFactory(geom=pathGeom1)

        pathGeom2 = LineString([
            [1.5305685, 43.5267991],
            [1.5277863, 43.6251412],
        ], srid=settings.API_SRID)
        pathGeom2.transform(settings.SRID)
        PathFactory(geom=pathGeom2)

        response = self.get_route_geometry({
            "steps": [
                {"lat": 43.55713801872145, "lng": 1.5297106650186976},
                {"lat": 43.5357564571998, "lng": 1.530315275025278},
                {"lat": 43.526894753922015, "lng": 1.49534225136577},
                {"lat": 43.526909669925175, "lng": 1.4898491643494793}
            ]
        })
        self.assertEqual(response.status_code, 200)
        geometries = response.data.get('geojson').get('geometries')
        self.assertEqual(len(geometries), 3)
        self.assertEqual(len(geometries[0].get('coordinates')), 2)
        self.assertEqual(len(geometries[1].get('coordinates')), 3)
        self.assertEqual(len(geometries[2].get('coordinates')), 2)
        for geom in geometries:
            for coords in geom.get('coordinates'):
                self.assertEqual(len(coords), 2)
        serialized = response.data.get('serialized')
        self.assertEqual(len(serialized), 3)
        self.assertEqual(len(serialized[0].get('positions').items()), 1)
        self.assertEqual(len(serialized[0].get('positions').get(0)), 2)
        self.assertEqual(len(serialized[0].get('paths')), 1)

        self.assertEqual(len(serialized[1].get('positions').items()), 2)
        self.assertEqual(len(serialized[1].get('positions').get(0)), 2)
        self.assertEqual(len(serialized[1].get('positions').get(1)), 2)
        self.assertEqual(len(serialized[1].get('paths')), 2)

        self.assertEqual(len(serialized[2].get('positions').items()), 1)
        self.assertEqual(len(serialized[2].get('positions').get(0)), 2)
        self.assertEqual(len(serialized[2].get('paths')), 1)

@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class PathKmlGPXTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(is_staff=True, is_superuser=True)
        cls.path = PathFactory.create(comments='exportable path')

    def setUp(self):
        self.client.force_login(self.user)
        self.gpx_response = self.client.get(reverse('core:path_gpx_detail', args=('en', self.path.pk, 'slug')))
        self.gpx_parsed = BeautifulSoup(self.gpx_response.content, features='xml')

        self.kml_response = self.client.get(reverse('core:path_kml_detail', args=('en', self.path.pk, 'slug')))

    def test_gpx_is_served_with_content_type(self):
        self.assertEqual(self.gpx_response.status_code, 200)
        self.assertEqual(self.gpx_response['Content-Type'], 'application/gpx+xml')

    def test_gpx_trek_as_track_points(self):
        self.assertEqual(len(self.gpx_parsed.findAll('trk')), 1)
        self.assertEqual(len(self.gpx_parsed.findAll('trkpt')), 2)
        self.assertEqual(len(self.gpx_parsed.findAll('ele')), 2)

    def test_kml_is_served_with_content_type(self):
        self.assertEqual(self.kml_response.status_code, 200)
        self.assertEqual(self.kml_response['Content-Type'], 'application/vnd.google-earth.kml+xml')


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class DenormalizedTrailTest(AuthentFixturesTest):
    @classmethod
    def setUpTestData(cls):
        cls.path = PathFactory()
        cls.trail1 = TrailFactory(paths=[cls.path])
        cls.trail2 = TrailFactory(paths=[cls.path])

    def test_path_and_trails_are_linked(self):
        self.assertIn(self.trail1, self.path.trails.all())
        self.assertIn(self.trail2, self.path.trails.all())

    def login(self):
        user = PathManagerFactory(password='booh')
        success = self.client.login(username=user.username, password='booh')
        self.assertTrue(success)

    def test_denormalized_path_trails(self):
        PathFactory.create_batch(size=50)
        TrailFactory.create_batch(size=50)
        self.login()
        with self.assertNumQueries(5):
            self.client.get(reverse('core:path-drf-list', kwargs={'format': 'datatables'}))


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class TrailViewsTest(CommonTest):
    model = Trail
    modelfactory = TrailFactory
    userfactory = PathManagerFactory
    expected_json_geom = {
        'type': 'LineString',
        'coordinates': [[3.0, 46.5], [3.001304, 46.5009004]],
    }
    extra_column_list = ['length', 'eid', 'departure', 'arrival']
    expected_column_list_extra = ['id', 'name', 'length', 'eid', 'departure', 'arrival']
    expected_column_formatlist_extra = ['id', 'length', 'eid', 'departure', 'arrival']

    def get_expected_geojson_geom(self):
        return self.expected_json_geom

    def get_expected_geojson_attrs(self):
        return {
            'id': self.obj.pk,
            'name': self.obj.name
        }

    def get_expected_datatables_attrs(self):
        return {
            'arrival': self.obj.arrival,
            'departure': self.obj.departure,
            'id': self.obj.pk,
            'length': round(self.obj.length, 1),
            'name': self.obj.name_display
        }

    def get_good_data(self):
        good_data = {
            'name': 't',
            'departure': 'Below',
            'arrival': 'Above',
            'comments': 'No comment',

            'certifications-TOTAL_FORMS': '0',
            'certifications-INITIAL_FORMS': '0',
            'certifications-MAX_NUM_FORMS': '1000',
            'certifications-MIN_NUM_FORMS': '',
        }
        if settings.TREKKING_TOPOLOGY_ENABLED:
            path = PathFactory.create()
            good_data['topology'] = '{"paths": [%s]}' % path.pk
        else:
            good_data['geom'] = 'SRID=4326;LINESTRING (0.0 0.0, 1.0 1.0)'
        return good_data

    def get_bad_data(self):
        return {
            'name': '',
            'certifications-TOTAL_FORMS': '0',
            'certifications-INITIAL_FORMS': '1',
            'certifications-MAX_NUM_FORMS': '0',
        }, _('This field is required.')

    def test_detail_page(self):
        trail = TrailFactory()
        response = self.client.get(trail.get_detail_url())
        self.assertEqual(response.status_code, 200)

    @mock.patch('mapentity.helpers.requests')
    def test_document_export(self, mock_requests):
        trail = TrailFactory(date_update="2000-01-01")
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'<p id="properties">Mock</p>'
        with open(default_storage.path(trail.get_map_image_path()), 'wb') as f:
            f.write(b'***' * 1000)

        self.assertEqual(default_storage.size(trail.get_map_image_path()), 3000)
        response = self.client.get(trail.get_document_url())
        self.assertEqual(response.status_code, 200)

    def test_add_trail_from_existing_topology_does_not_use_pk(self):
        import bs4

        trail = TrailFactory(offset=3.14)
        response = self.client.get(Trail.get_add_url() + '?topology=%s' % trail.pk)
        soup = bs4.BeautifulSoup(response.content, features='html.parser')
        textarea_field = soup.find(id="id_topology")
        self.assertIn('"kind": "TMP"', textarea_field.text)
        self.assertIn('"offset": 3.14', textarea_field.text)
        self.assertNotIn('"pk": %s' % trail.pk, textarea_field.text)

    def test_add_trail_from_existing_topology(self):
        trail = TrailFactory()
        form_data = self.get_good_data()
        form_data['topology'] = trail.serialize(with_pk=False)
        response = self.client.post(Trail.get_add_url(), form_data)
        self.assertEqual(response.status_code, 302)  # success, redirects to detail view
        p = re.compile(r"/trail/(\d+)/")
        m = p.match(response['Location'])
        new_pk = int(m.group(1))
        new_trail = Trail.objects.get(pk=new_pk)
        self.assertIn(trail, new_trail.trails.all())

    def test_perfs_export_csv(self):
        self.modelfactory.create()
        with self.assertNumQueries(12):
            self.client.get(self.model.get_format_list_url() + '?format=csv')


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class TrailKmlGPXTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(is_staff=True, is_superuser=True)
        cls.trail = TrailFactory.create(comments='exportable trail')

    def setUp(self):
        self.client.force_login(self.user)

        self.gpx_response = self.client.get(reverse('core:trail_gpx_detail', args=('en', self.trail.pk, 'slug')))
        self.gpx_parsed = BeautifulSoup(self.gpx_response.content, features='xml')

        self.kml_response = self.client.get(reverse('core:trail_kml_detail', args=('en', self.trail.pk, 'slug')))

    def test_gpx_is_served_with_content_type(self):
        self.assertEqual(self.gpx_response.status_code, 200)
        self.assertEqual(self.gpx_response['Content-Type'], 'application/gpx+xml')

    def test_gpx_trek_as_track_points(self):
        self.assertEqual(len(self.gpx_parsed.findAll('trk')), 1)
        self.assertEqual(len(self.gpx_parsed.findAll('trkpt')), 2)
        self.assertEqual(len(self.gpx_parsed.findAll('ele')), 2)

    def test_kml_is_served_with_content_type(self):
        self.assertEqual(self.kml_response.status_code, 200)
        self.assertEqual(self.kml_response['Content-Type'], 'application/vnd.google-earth.kml+xml')


@skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
class RemovePathKeepTopology(TestCase):
    def test_remove_poi(self):
        """
        poi is linked with AB

            poi
             +                D
             *                |
             *                |
        A---------B           C
             |----|
               e1

        we got after remove AB :

             poi
              + * * * * * * * D
                              |
                              |
                              C

        poi is linked with DC and e1 is deleted
        """
        ab = PathFactory.create(name="AB", geom=LineString((0, 0), (1, 0)))
        PathFactory.create(name="CD", geom=LineString((2, 0), (2, 1)))
        poi = POIFactory.create(paths=[(ab, 0.5, 0.5)], offset=1)
        e1 = TopologyFactory.create(paths=[(ab, 0.5, 1)])

        self.assertAlmostEqual(1, poi.offset)
        self.assertEqual(poi.geom, Point(0.5, 1.0, srid=2154))

        ab.delete()
        poi.reload()
        e1.reload()

        self.assertEqual(Path.objects.all().count(), 1)

        self.assertEqual(e1.deleted, True)
        self.assertEqual(poi.deleted, False)

        self.assertAlmostEqual(1.5, poi.offset)
