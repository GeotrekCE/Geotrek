import os

from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.shortcuts import get_object_or_404
from django.test.utils import override_settings
from django.utils import translation
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from django.conf import settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

# Workaround https://code.djangoproject.com/ticket/22865
from freezegun import freeze_time

from geotrek.common.models import Attachment, AccessibilityAttachment, FileType  # NOQA
from geotrek.common.tests.factories import AttachmentFactory, AttachmentAccessibilityFactory
from geotrek.common.utils.testdata import get_dummy_uploaded_image

from mapentity.tests.factories import SuperUserFactory, UserFactory
from mapentity.registry import app_settings
from mapentity.tests import MapEntityTest, MapEntityLiveTest

from geotrek.authent.tests.factories import StructureFactory
from geotrek.authent.tests.base import AuthentFixturesTest


class TranslationResetMixin:
    def setUp(self):
        translation.deactivate()
        super().setUp()


class CommonTest(AuthentFixturesTest, TranslationResetMixin, MapEntityTest):

    def get_bad_data(self):
        if settings.TREKKING_TOPOLOGY_ENABLED:
            return {'topology': 'doh!'}, _('Topology is not valid.')
        else:
            return {'geom': 'doh!'}, _('Invalid geometry value.')

    @mock.patch('mapentity.helpers.requests')
    def test_document_public_booklet_export(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run
        try:
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_booklet_printable')
        except NoReverseMatch:
            return  # No public booklet export
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'<p id="properties">Mock</p>'

        obj = self.modelfactory.create()
        response = self.client.get(
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_booklet_printable',
                    kwargs={'lang': 'en', 'pk': obj.pk, 'slug': obj.slug}))
        self.assertEqual(response.status_code, 200)

    @mock.patch('mapentity.helpers.requests')
    def test_duplicate_object_without_structure(self, mock_requests):
        if self.model is None or not getattr(self.model, 'can_duplicate') or hasattr(self.model, 'structure'):
            return

        obj_1 = self.modelfactory.create()
        obj_1.refresh_from_db()
        response_duplicate = self.client.post(
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_duplicate',
                    kwargs={"pk": obj_1.pk})
        )

        self.assertEqual(response_duplicate.status_code, 302)
        self.client.get(response_duplicate['location'])
        self.assertEqual(self.model.objects.count(), 2)
        if 'name' in [field.name for field in self.model._meta.get_fields()]:
            self.assertEqual(self.model.objects.filter(name__endswith='(copy)').count(), 2)
        for field in self.model._meta.get_fields():
            fields_name_different = ['id', 'uuid', 'date_insert', 'date_update', 'name', 'name_en']
            if not field.related_model and field.name not in fields_name_different:
                self.assertEqual(str(getattr(obj_1, field.name)), str(getattr(self.model.objects.last(), field.name)))

    @mock.patch('mapentity.helpers.requests')
    def test_duplicate_object_with_structure(self, mock_requests):
        if self.model is None or not getattr(self.model, 'can_duplicate'):
            return
        fields_name = [field.name for field in self.model._meta.get_fields()]
        if "structure" not in fields_name:
            return
        structure = StructureFactory.create()
        obj_1 = self.modelfactory.create(structure=structure)
        obj_1.refresh_from_db()

        AttachmentFactory.create(content_object=obj_1,
                                 attachment_file=get_dummy_uploaded_image())

        attachments_accessibility = 'attachments_accessibility' in fields_name

        if attachments_accessibility:
            AttachmentAccessibilityFactory.create(content_object=obj_1,
                                                  attachment_accessibility_file=get_dummy_uploaded_image())
        response = self.client.post(
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_duplicate',
                    kwargs={"pk": obj_1.pk})
        )
        self.assertEqual(response.status_code, 302)

        msg = [str(message) for message in messages.get_messages(response.wsgi_request)]
        self.assertEqual(msg[0],
                         f"{self.model._meta.verbose_name} has been duplicated successfully")

        self.assertEqual(self.model.objects.count(), 2)
        self.assertEqual(Attachment.objects.filter(object_id=obj_1.pk).count(), 1)
        self.assertEqual(Attachment.objects.filter(object_id=self.model.objects.last().pk).count(), 1)
        if attachments_accessibility:
            self.assertEqual(AccessibilityAttachment.objects.filter(object_id=obj_1.pk).count(), 1)
            self.assertEqual(AccessibilityAttachment.objects.filter(object_id=self.model.objects.last().pk).count(), 1)

        if 'name' in fields_name:
            self.assertEqual(self.model.objects.filter(name__endswith='(copy)').count(), 1)
        self.assertEqual(self.model.objects.filter(structure=structure).count(), 1)
        for field in self.model._meta.get_fields():
            fields_name_different = ['id', 'uuid', 'date_insert', 'date_update', 'name', 'name_en']
            if not field.related_model and field.name not in fields_name_different:
                self.assertEqual(str(getattr(obj_1, field.name)), str(getattr(self.model.objects.last(), field.name)))

    @mock.patch('mapentity.helpers.requests')
    def test_document_public_export(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run
        try:
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_printable')
        except NoReverseMatch:
            return  # No public booklet export
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'<p id="properties">Mock</p>'

        obj = self.modelfactory.create()
        response = self.client.get(
            reverse(f'{self.model._meta.app_label}:{self.model._meta.model_name}_printable',
                    kwargs={'lang': 'en', 'pk': obj.pk, 'slug': obj.slug}))
        self.assertEqual(response.status_code, 200)

    def test_structure_is_set(self):
        if not hasattr(self.model, 'structure'):
            return
        response = self.client.post(self._get_add_url(), self.get_good_data())
        self.assertEqual(response.status_code, 302)
        obj = self.model.objects.last()
        self.assertEqual(obj.structure, self.user.profile.structure)

    @override_settings(FORCED_LAYERS=[('OSM', [(42, 100000), (43.87017822557581, 7.506408691406249),
                                               (43.90185050527358, 7.555847167968749), (42, 100000)])])
    def test_forced_layers(self):
        if self.model is None:
            return  # Abstract test should not run

        obj = self.modelfactory()

        response = self.client.get(obj.get_list_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "forced_layers_data")
        self.assertContains(response, "[42, 100000]")

    def test_structure_is_not_changed_without_permission(self):
        if not hasattr(self.model, 'structure'):
            return
        structure = StructureFactory()
        self.assertNotEqual(structure, self.user.profile.structure)
        self.assertFalse(self.user.has_perm('authent.can_bypass_structure'))
        obj = self.modelfactory.create(structure=structure)
        result = self.client.post(obj.get_update_url(), self.get_good_data())
        self.assertEqual(result.status_code, 302)
        self.assertEqual(self.model.objects.first().structure, structure)
        self.logout()

    def test_structure_is_changed_with_permission(self):
        if not self.model or 'structure' not in self.model._meta.get_fields():
            return
        perm = Permission.objects.get(codename='can_bypass_structure')
        self.user.user_permissions.add(perm)
        structure = StructureFactory()
        self.assertNotEqual(structure, self.user.profile.structure)
        obj = self.modelfactory.create(structure=structure)
        data = self.get_good_data()
        data['structure'] = self.user.profile.structure.pk
        result = self.client.post(obj.get_update_url(), data)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(self.model.objects.first().structure, self.user.profile.structure)
        self.logout()

    def test_set_structure_with_permission(self):
        if not hasattr(self.model, 'structure'):
            return
        perm = Permission.objects.get(codename='can_bypass_structure')
        self.user.user_permissions.add(perm)
        structure = StructureFactory()
        self.assertNotEqual(structure, self.user.profile.structure)
        data = self.get_good_data()
        data['structure'] = self.user.profile.structure.pk
        response = self.client.post(self._get_add_url(), data)
        self.assertEqual(response.status_code, 302)
        obj = self.model.objects.last()
        self.assertEqual(obj.structure, self.user.profile.structure)
        self.logout()

    def test_detail_other_language(self):
        if self.model is None:
            return  # Abstract test should not run

        obj = self.modelfactory()

        response = self.client.get('%s?lang=fr' % obj.get_detail_url())
        self.assertEqual(response.status_code, 200)

    def test_detail_with_context(self):
        if self.model is None:
            return  # Abstract test should not run

        obj = self.modelfactory()

        response = self.client.get('%s?context={"mapsize":{"width":5,"height":6}}' % obj.get_detail_url())
        self.assertEqual(response.status_code, 200)

    def test_permission_published(self):
        if not self.model:
            return
        if 'published' not in [field.name for field in self.model._meta.get_fields()]:
            return
        self.user = self.userfactory(password='booh')
        codename = 'publish_%s' % self.model._meta.model_name
        if not Permission.objects.filter(codename=codename).count():
            return
        perm = Permission.objects.get(codename=codename)
        group = self.user.groups.first()
        if group:
            group.permissions.remove(perm)
        self.user.user_permissions.remove(perm)
        self.user.save()
        self.user = get_object_or_404(User, pk=self.user.pk)
        success = self.client.login(username=self.user.username, password='booh')
        self.assertTrue(success)
        response = self.client.post(self._get_add_url(), self.get_good_data())
        self.assertEqual(response.status_code, 302)

    def test_stay_publish_no_permission(self):
        if not self.model:
            return
        if 'published' not in [field.name for field in self.model._meta.get_fields()]:
            return
        self.user = self.userfactory(password='booh')
        codename = 'publish_%s' % self.model._meta.model_name
        if not Permission.objects.filter(codename=codename).count():
            return
        perm = Permission.objects.get(codename=codename)
        group = self.user.groups.first()
        if group:
            group.permissions.remove(perm)
        self.user.user_permissions.remove(perm)
        self.user.save()
        self.user = get_object_or_404(User, pk=self.user.pk)
        self.client.force_login(user=self.user)
        obj = self.modelfactory(published=True)

        response = self.client.post(obj.get_update_url(), self.get_good_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.model.objects.get(pk=obj.pk).published)

    def test_custom_columns_mixin_on_list(self):
        # Assert columns equal mandatory columns plus custom extra columns
        if self.model is None:
            return
        with override_settings(COLUMNS_LISTS={f'{self.model._meta.model_name}_view': self.extra_column_list}):
            self.assertEqual(import_string(f'geotrek.{self.model._meta.app_label}.views.{self.model.__name__}List')().columns,
                             self.expected_column_list_extra)

    def test_custom_columns_mixin_on_export(self):
        # Assert columns equal mandatory columns plus custom extra columns
        if self.model is None:
            return
        with override_settings(COLUMNS_LISTS={f'{self.model._meta.model_name}_export': self.extra_column_list}):
            self.assertEqual(import_string(f'geotrek.{self.model._meta.app_label}.views.{self.model.__name__}FormatList')().columns,
                             self.expected_column_formatlist_extra)


class GeotrekAPITestCase:
    api_prefix = '/api/en/'

    def get_expected_json_attrs(self):
        return {}

    def get_expected_geojson_attrs(self):
        return {}

    @freeze_time("2020-03-17")
    def test_api_list_for_model(self):
        if self.get_expected_json_attrs is None:
            return
        if self.model is None:
            return  # Abstract test should not run

        self.obj = self.modelfactory.create()
        list_url = '{api_prefix}{modelname}s.json'.format(api_prefix=self.api_prefix,
                                                          modelname=self.model._meta.model_name)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200, f"{list_url} not found")
        content_json = response.json()
        if hasattr(self, 'length'):
            length = content_json[0].pop('length')
            self.assertAlmostEqual(length, self.length)
        self.assertEqual(content_json, [{'id': self.obj.pk, **self.get_expected_json_attrs()}])

    @freeze_time("2020-03-17")
    def test_api_geojson_list_for_model(self):
        if self.get_expected_json_attrs is None:
            return
        if self.model is None:
            return  # Abstract test should not run

        self.obj = self.modelfactory.create()
        list_url = '{api_prefix}{modelname}s.geojson'.format(api_prefix=self.api_prefix,
                                                             modelname=self.model._meta.model_name)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200, f"{list_url} not found")
        content_json = response.json()
        if hasattr(self, 'length'):
            length = content_json['features'][0]['properties'].pop('length')
            self.assertAlmostEqual(length, self.length)
        self.assertEqual(content_json, {
            'type': 'FeatureCollection',
            'features': [{
                'id': self.obj.pk,
                'type': 'Feature',
                'geometry': self.expected_json_geom,
                'properties': self.get_expected_json_attrs(),
            }],
        })

    @freeze_time("2020-03-17")
    def test_api_detail_for_model(self):
        if self.get_expected_json_attrs is None:
            return
        if self.model is None:
            return  # Abstract test should not run

        self.obj = self.modelfactory.create()
        detail_url = '{api_prefix}{modelname}s/{id}'.format(api_prefix=self.api_prefix,
                                                            modelname=self.model._meta.model_name,
                                                            id=self.obj.pk)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200, f"{detail_url} not found")

        content_json = response.json()
        if hasattr(self, 'length'):
            length = content_json.pop('length')
            self.assertAlmostEqual(length, self.length)
        self.assertEqual(content_json, {'id': self.obj.pk, **self.get_expected_json_attrs()})

    @freeze_time("2020-03-17")
    def test_api_geojson_detail_for_model(self):
        if self.get_expected_json_attrs is None:
            return
        if self.model is None:
            return  # Abstract test should not run

        self.obj = self.modelfactory.create()
        detail_url = '{api_prefix}{modelname}s/{id}.geojson'.format(api_prefix=self.api_prefix,
                                                                    modelname=self.model._meta.model_name,
                                                                    id=self.obj.pk)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200, f"{detail_url} not found")
        content_json = response.json()
        if hasattr(self, 'length'):
            length = content_json['properties'].pop('length')
            self.assertAlmostEqual(length, self.length)
        self.assertEqual(content_json, {
            'id': self.obj.pk,
            'type': 'Feature',
            'geometry': self.expected_json_geom,
            'properties': self.get_expected_json_attrs(),
        })


class CommonLiveTest(MapEntityLiveTest):
    @mock.patch('mapentity.helpers.requests')
    def test_map_image_other_language(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run

        user = SuperUserFactory.create(username='Superuser', password='booh')
        self.client.force_login(user=user)

        obj = self.modelfactory.create(geom='POINT(0 0)')

        # Initially, map image does not exists
        image_path = obj.get_map_image_path()
        if os.path.exists(image_path):
            os.remove(image_path)
        self.assertFalse(os.path.exists(image_path))

        # Mock Screenshot response
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'*' * 100

        response = self.client.get(obj.map_image_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(image_path))

        mapimage_url = '%s%s?context&lang=fr' % (self.live_server_url, obj.get_detail_url())
        screenshot_url = 'http://0.0.0.0:8001/?url=%s' % mapimage_url
        url_called = mock_requests.get.call_args_list[0]
        self.assertTrue(url_called.startswith(screenshot_url))

    @mock.patch('mapentity.helpers.requests')
    def test_map_image_not_published_superuser(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run

        user = SuperUserFactory.create(username='Superuser', password='booh')
        self.client.force_login(user=user)

        obj = self.modelfactory.create(geom='POINT(0 0)', published=False)

        # Initially, map image does not exists
        image_path = obj.get_map_image_path()
        if os.path.exists(image_path):
            os.remove(image_path)
        self.assertFalse(os.path.exists(image_path))

        # Mock Screenshot response
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'*' * 100

        response = self.client.get(obj.map_image_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(image_path))

        mapimage_url = '%s%s?context' % (self.live_server_url, obj.get_detail_url())
        screenshot_url = 'http://0.0.0.0:8001/?url=%s' % mapimage_url
        url_called = mock_requests.get.call_args_list[0]
        self.assertTrue(url_called.startswith(screenshot_url))

    @mock.patch('mapentity.helpers.requests')
    def test_map_image_not_published_not_authenticated(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run

        obj = self.modelfactory.create(geom='POINT(0 0)', published=False)

        # Initially, map image does not exists
        image_path = obj.get_map_image_path()
        if os.path.exists(image_path):
            os.remove(image_path)
        self.assertFalse(os.path.exists(image_path))

        response = self.client.get(obj.map_image_url)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(os.path.exists(image_path))

    @mock.patch('mapentity.helpers.requests')
    def test_map_image_not_published_no_permission(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run

        user = UserFactory.create(username='user', password='booh')
        self.client.force_login(user=user)

        obj = self.modelfactory.create(geom='POINT(0 0)', published=False)

        # Initially, map image does not exists
        image_path = obj.get_map_image_path()
        if os.path.exists(image_path):
            os.remove(image_path)
        self.assertFalse(os.path.exists(image_path))

        # Mock Screenshot response
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'*' * 100

        response = self.client.get(obj.map_image_url)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(os.path.exists(image_path))

    @mock.patch('mapentity.helpers.requests')
    @override_settings(DEBUG=False)
    def test_map_image_not_serve(self, mock_requests):
        if self.model is None:
            return  # Abstract test should not run
        app_settings['SENDFILE_HTTP_HEADER'] = 'X-Accel-Redirect'
        user = SuperUserFactory.create(username='Superuser', password='booh')
        self.client.force_login(user=user)

        obj = self.modelfactory.create(geom='POINT(0 0)')

        # Initially, map image does not exists
        image_path = obj.get_map_image_path()
        if os.path.exists(image_path):
            os.remove(image_path)
        self.assertFalse(os.path.exists(image_path))

        # Mock Screenshot response
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = b'*' * 100

        response = self.client.get(obj.map_image_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(image_path))
