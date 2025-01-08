import os
from io import StringIO
from unittest import mock
from unittest.mock import patch, PropertyMock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from easy_thumbnails.models import Thumbnail

from geotrek import __version__
from geotrek.authent.tests.factories import StructureFactory
from geotrek.common.models import TargetPortal
from geotrek.common.tests.factories import AttachmentFactory, TargetPortalFactory
from geotrek.common.utils.testdata import get_dummy_uploaded_image
from geotrek.core.models import Usage, Path
from geotrek.core.tests.factories import UsageFactory, PathFactory
from geotrek.infrastructure.models import InfrastructureType, Infrastructure
from geotrek.infrastructure.tests.factories import InfrastructureFactory, InfrastructureTypeFactory
from geotrek.trekking.tests.factories import POIFactory


@mock.patch('sys.stdout', new_callable=StringIO)
class CommandUpdatePostMigrationTests(TestCase):
    def test_command_post_migration(self, mock_stdout):
        portal = TargetPortalFactory.create(name="Test", title=None)
        self.assertEqual(portal.title_fr, "")
        self.assertEqual(portal.description_fr, "")
        call_command('update_post_migration_languages')
        changed_portal = TargetPortal.objects.get(name="Test")
        self.assertEqual(changed_portal.title_fr, "Geotrek Rando")
        self.assertEqual(changed_portal.description_fr, "Geotrek est une web app permettant de préparer à "
                                                        "l'avance ses randonnées !")


class CommandUnsetStructureTests(TestCase):
    def test_command_unset_structure(self):
        structure1 = StructureFactory.create(name="coucou")
        structure2 = StructureFactory.create(name="coco")

        infratype1 = InfrastructureTypeFactory.create(label="annyeong", structure=structure1, pictogram=None)
        infratype2 = InfrastructureTypeFactory.create(label="annyeong", structure=structure2, pictogram=None)

        path = PathFactory.create(name="pass")
        usage1 = UsageFactory.create(usage="hello", structure=structure1)
        usage2 = UsageFactory.create(usage="hello", structure=structure2)
        path.usages.add(usage1)
        path.usages.add(usage2)

        infrastructure1 = InfrastructureFactory.create(name='pissenlit', type=infratype1)
        infrastructure2 = InfrastructureFactory.create(name='rhododendron', type=infratype2)

        self.assertEqual(InfrastructureType.objects.count(), 2)
        self.assertEqual(Usage.objects.count(), 2)

        self.assertEqual(infrastructure1.type.label, 'annyeong')
        self.assertEqual(infrastructure1.type.structure.name, 'coucou')
        self.assertEqual(infrastructure2.type.label, 'annyeong')
        self.assertEqual(infrastructure2.type.structure.name, 'coco')

        self.assertEqual(path.usages.count(), 2)
        self.assertEqual(usage1.structure.name, 'coucou')
        self.assertEqual(usage2.structure.name, 'coco')
        output = StringIO()
        call_command('unset_structure', '--all', verbosity=2, stdout=output)
        response = output.getvalue()
        self.assertIn("Create hello", response)
        self.assertEqual(InfrastructureType.objects.count(), 1)
        self.assertEqual(Usage.objects.count(), 1)

        infra = Infrastructure.objects.first()

        self.assertEqual(infra.type.label, 'annyeong')
        self.assertEqual(infra.type.structure, None)

        path_usages = Path.objects.first().usages.first()

        self.assertEqual(path_usages.usage, 'hello')
        self.assertEqual(path_usages.structure, None)

    def test_unset_structure_without_structure_keep_pk(self):
        structure = StructureFactory.create(name="Test")
        infratype_no_structure = InfrastructureTypeFactory.create(label="type1", structure=None, pictogram=None)
        InfrastructureFactory.create(name='infra1', type=infratype_no_structure)
        infratype_structure = InfrastructureTypeFactory.create(label="type2", structure=structure, pictogram=None)
        InfrastructureFactory.create(name='infra2', type=infratype_structure)

        self.assertEqual(InfrastructureType.objects.count(), 2)
        self.assertIsNone(infratype_no_structure.structure)
        self.assertIsNotNone(infratype_structure.structure)
        old_pk_no_structure = infratype_no_structure.pk
        old_pk_structure = infratype_structure.pk
        call_command('unset_structure', '--all', verbosity=0)
        type1 = InfrastructureType.objects.get(label="type1")
        type2 = InfrastructureType.objects.get(label="type1")
        new_pk_no_structure = type1.pk
        new_pk_structure = type2.pk

        self.assertEqual(old_pk_no_structure, new_pk_no_structure)
        self.assertNotEqual(old_pk_structure, new_pk_structure)

        self.assertIsNone(type1.structure)
        self.assertIsNone(type2.structure)

    def test_unset_structure_fail_no_model_not_all(self):
        InfrastructureTypeFactory.create(label="annyeong", structure=None, pictogram=None)
        with self.assertRaisesRegex(CommandError, "You should specify model"):
            call_command('unset_structure', verbosity=0)

    def test_unset_structure_list(self):
        output = StringIO()
        call_command('unset_structure', '--list', verbosity=0, stdout=output)
        stdout = output.getvalue()
        # Some of them listed.
        self.assertIn('Organism', stdout)
        self.assertIn('filetype', stdout)
        self.assertIn('Path source', stdout)


class CommandAttachmentsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.content = POIFactory(geom='SRID=%s;POINT(1 1)' % settings.SRID)

    def setUp(self):
        self.picture = AttachmentFactory(content_object=self.content,
                                         attachment_file=get_dummy_uploaded_image())

    def test_remove_thumbnails(self):
        output = StringIO()
        self.assertIsNotNone(self.content.thumbnail)
        self.assertTrue(os.path.exists(self.picture.attachment_file.path))
        self.assertTrue(os.path.exists("{path}.120x120_q85_crop.png".format(path=self.picture.attachment_file.path)))
        self.assertEqual(Thumbnail.objects.first().name, "{name}.120x120_q85_crop.png".format(
            name=self.picture.attachment_file.name
        ))
        call_command('remove_thumbnails', stdout=output)
        self.assertTrue(os.path.exists(self.picture.attachment_file.path))
        self.assertFalse(os.path.exists("{name}.120x120_q85_crop.png".format(name=self.picture.attachment_file.path)))
        self.assertEqual(Thumbnail.objects.count(), 0)

    def test_clean_attachments_deleted(self):
        output = StringIO()
        self.picture.delete()
        call_command('clean_attachments', stdout=output, verbosity=2)
        self.assertIn('%s... DELETED' % self.picture.attachment_file.name, output.getvalue())
        self.assertFalse(os.path.exists(self.picture.attachment_file.path))

    def test_clean_attachments_found(self):
        output = StringIO()
        call_command('clean_attachments', stdout=output, verbosity=2)
        self.assertIn('%s... Found' % self.picture.attachment_file.name, output.getvalue())
        self.assertTrue(os.path.exists(self.picture.attachment_file.path))

    def test_clean_attachments_thumbnails(self):
        output = StringIO()
        self.assertIsNotNone(self.content.thumbnail)
        call_command('clean_attachments', stdout=output, verbosity=2)
        self.assertIn('%s... Thumbnail' % self.content.thumbnail.name, output.getvalue())
        self.assertTrue(os.path.exists(self.content.thumbnail.path))


class CheckVersionsCommandTestCase(TestCase):
    def setUp(self):
        self.output = StringIO()

    def test_geotrek_version(self):
        call_command('check_versions', '--geotrek', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), __version__)

    @patch('geotrek.common.management.commands.check_versions.sys')
    def test_python_version(self, mock_sys):
        type(mock_sys).version_info = PropertyMock(return_value=(3, 9, 1, 'final', 0))
        call_command('check_versions', '--python', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), '3.9.1')

    @patch('django.get_version', return_value='3.2.7')
    def test_django_version(self, mock_get_version):
        call_command('check_versions', '--django', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), '3.2.7')

    @patch('django.db.connection.cursor')
    def test_postgresql_version(self, mock_cursor):
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ['13.3']
        call_command('check_versions', '--postgresql', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), '13.3')

    @patch('django.db.connection.cursor')
    def test_postgis_version(self, mock_cursor):
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ['3.1.0']
        call_command('check_versions', '--postgis', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), '3.1.0')

    @patch('django.db.connection.cursor')
    def test_pgrouting_version(self, mock_cursor):
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ['3.0.0']
        call_command('check_versions', '--pgrouting', '--no-color', stdout=self.output)
        self.assertEqual(self.output.getvalue().strip(), '3.0.0')

    @patch('geotrek.common.management.commands.check_versions.sys')
    @patch('django.get_version', return_value='3.2.2')
    @patch('django.db.connection.cursor')
    def test_full_version(self, mock_cursor, mock_get_version, mock_version_info):
        type(mock_version_info).version = PropertyMock(return_value="3.9.1")
        mock_cursor.return_value.__enter__.return_value.fetchone.side_effect = [('14',), ('3.0',), ('3.0.0',)]
        call_command('check_versions', '--full', '--no-color', stdout=self.output)
        expected_result = (
            f"Geotrek version    : {__version__}\n"
            "Python version     : 3.9.1\n"
            "Django version     : 3.2.2\n"
            "PostgreSQL version : 14\n"
            "PostGIS version    : 3.0\n"
            "pgRouting version  : 3.0.0"
        )
        self.assertEqual(self.output.getvalue().strip(), expected_result)
