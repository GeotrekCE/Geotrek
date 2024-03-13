from mapentity.tests.factories import SuperUserFactory
from . import factories
from .base import AuthentFixturesTest


class AdminSiteTest(AuthentFixturesTest):
    @classmethod
    def setUpTestData(cls):
        cls.admin = SuperUserFactory()
        cls.path_manager = factories.PathManagerFactory()
        cls.trek_manager = factories.TrekkingManagerFactory()

    def login(self, user):
        self.client.force_login(user)

    def test_path_manager_cannot_see_trekking_apps(self):
        self.login(self.path_manager)
        response = self.client.get('/admin/core/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/trekking/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/admin/')
        self.assertContains(response, 'Topology')
        self.assertContains(response, 'Maintenance')
        self.assertContains(response, 'Infrastructure')
        self.assertContains(response, 'Signage')
        self.assertContains(response, 'Land')
        self.assertNotContains(response, 'Zoning')
        self.assertNotContains(response, 'Trekking')

    def test_trek_manager_cannot_see_core_apps(self):
        self.login(self.trek_manager)
        response = self.client.get('/admin/core/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/admin/trekking/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/')
        self.assertContains(response, 'Trekking')
        self.assertNotContains(response, 'Core')
        self.assertNotContains(response, 'Maintenance')
        self.assertNotContains(response, 'Infrastructure')
        self.assertNotContains(response, 'Signage')
        self.assertNotContains(response, 'Zoning')
        self.assertNotContains(response, 'Land')
