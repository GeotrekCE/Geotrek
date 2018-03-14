# -*- coding: utf-8 -*-
import os
import json

from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase

from geotrek.authent.factories import StructureFactory, UserProfileFactory
from geotrek.authent.tests.base import AuthentFixturesTest
from geotrek.trekking.tests import TrekkingManagerTest
from geotrek.common.tests import TranslationResetMixin
from geotrek.sensitivity.factories import SensitiveAreaFactory

User = get_user_model()


class SensitiveAreaViewsSameStructureTests(AuthentFixturesTest):
    def setUp(self):
        profile = UserProfileFactory.create(user__username='homer',
                                            user__password='dooh')
        user = profile.user
        user.user_permissions.add(Permission.objects.get(codename=u"add_sensitivearea"))
        user.user_permissions.add(Permission.objects.get(codename=u"change_sensitivearea"))
        user.user_permissions.add(Permission.objects.get(codename=u"delete_sensitivearea"))
        user.user_permissions.add(Permission.objects.get(codename=u"read_sensitivearea"))
        user.user_permissions.add(Permission.objects.get(codename=u"export_sensitivearea"))
        self.client.login(username=user.username, password='dooh')
        self.area1 = SensitiveAreaFactory.create()
        structure = StructureFactory.create()
        self.area2 = SensitiveAreaFactory.create(structure=structure)

    def tearDown(self):
        self.client.logout()

    def test_can_edit_same_structure(self):
        url = "/sensitivearea/edit/{pk}/".format(pk=self.area1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_other_structure(self):
        url = "/sensitivearea/edit/{pk}/".format(pk=self.area2.pk)
        response = self.client.get(url)
        self.assertRedirects(response, "/sensitivearea/{pk}/".format(pk=self.area2.pk))

    def test_can_delete_same_structure(self):
        url = "/sensitivearea/delete/{pk}/".format(pk=self.area1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_delete_other_structure(self):
        url = "/sensitivearea/delete/{pk}/".format(pk=self.area2.pk)
        response = self.client.get(url)
        self.assertRedirects(response, "/sensitivearea/{pk}/".format(pk=self.area2.pk))


class SensitiveAreaTemplatesTest(TestCase):
    def setUp(self):
        self.area = SensitiveAreaFactory.create()
        self.login()

    def login(self):
        User.objects.create_superuser('splash', 'splash@toto.com', password='booh')
        success = self.client.login(username='splash', password='booh')
        self.assertTrue(success)

    def tearDown(self):
        self.client.logout()

    def test_species_name_shown_in_detail_page(self):
        url = "/sensitivearea/{pk}/".format(pk=self.area.pk)
        response = self.client.get(url)
        self.assertContains(response, self.area.species.name)


class BasicJSONAPITest(TranslationResetMixin, TrekkingManagerTest):
    maxDiff = None

    def setUp(self):
        super(TrekkingManagerTest, self).setUp()
        self.sensitivearea = SensitiveAreaFactory.create()
        self.species = self.sensitivearea.species
        self.pk = self.sensitivearea.pk
        url = '/api/en/sensitiveareas/{pk}.json'.format(pk=self.pk)
        self.response = self.client.get(url)
        self.result = json.loads(self.response.content)

    def test_expected_properties(self):
        self.assertDictEqual(self.result, {
            u'id': self.pk,
            u'publication_date': unicode(self.sensitivearea.publication_date.strftime('%Y-%m-%d')),
            u'published': True,
            u'description': u"Blabla",
            u'contact': u'<a href="mailto:toto@tata.com">toto@tata.com</a>',
            u'kml_url': u'/api/en/sensitiveareas/{pk}.kml'.format(pk=self.pk),
            u'geometry': {
                u'type': u'Polygon',
                u'coordinates': [[
                    [3.0000000000000004, 46.49999999999995],
                    [3.0000000000000004, 46.50002701349549],
                    [3.0000391186749895, 46.5000270134888],
                    [3.00003911865561, 46.49999999999326],
                    [3.0000000000000004, 46.49999999999995],
                ]],
            },
            u'species': {
                u"id": self.species.id,
                u"name": self.species.name,
                u'pictogram': os.path.join(settings.MEDIA_URL, self.species.pictogram.name),
                u"period": [False, False, False, False, False, True, True, False, False, False, False, False],
                u'practices': [
                    {u'id': self.species.practices.all()[0].pk, u'name': self.species.practices.all()[0].name},
                    {u'id': self.species.practices.all()[1].pk, u'name': self.species.practices.all()[1].name},
                ],
                u'url': self.species.url,
            },
        })
