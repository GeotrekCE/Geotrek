import json
import os
from io import StringIO
from unittest import mock, skipIf
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import DatabaseError
from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase
from django.test.utils import override_settings
from requests import Response

from geotrek.authent.tests.factories import StructureFactory
from geotrek.common.models import Attachment, FileType, Organism, RecordSource, Theme
from geotrek.common.parsers import (AttachmentParserMixin, DownloadImportError,
                                    ExcelParser, GeotrekAggregatorParser,
                                    GeotrekParser, OpenSystemParser,
                                    TourInSoftParser, TourismSystemParser,
                                    ValueImportError, XmlParser)
from geotrek.common.tests.factories import ThemeFactory
from geotrek.common.tests.mixins import GeotrekParserTestMixin
from geotrek.common.utils.testdata import SVG_FILE, get_dummy_img
from geotrek.trekking.models import POI, Trek
from geotrek.trekking.parsers import GeotrekTrekParser
from geotrek.trekking.tests.factories import TrekFactory


class OrganismParser(ExcelParser):
    model = Organism
    fields = {'organism': 'nOm'}


class OrganismEidParser(ExcelParser):
    model = Organism
    fields = {'organism': 'nOm'}
    eid = 'organism'


class StructureExcelParser(ExcelParser):
    model = Organism
    fields = {
        'organism': 'nOm',
        'structure': 'structure'
    }
    eid = 'organism'


class OrganismNoMappingNoPartialParser(StructureExcelParser):
    field_options = {
        "structure": {"mapping": {"foo": "bar", "": "boo"}}
    }
    natural_keys = {
        "structure": "name"
    }


class OrganismNoMappingPartialParser(StructureExcelParser):
    field_options = {
        "structure": {"mapping": {"foo": "bar"}, "partial": True}
    }
    natural_keys = {
        "structure": "name"
    }


class OrganismNoNaturalKeysParser(StructureExcelParser):
    warn_on_missing_fields = True


class AttachmentParser(AttachmentParserMixin, OrganismEidParser):
    non_fields = {'attachments': 'photo'}


class WarnAttachmentParser(AttachmentParser):
    warn_on_missing_fields = True


class AttachmentLegendParser(AttachmentParser):

    def filter_attachments(self, src, val):
        (url, legend, author) = val.split(', ')
        return [(url, legend, author)]


class ParserTests(TestCase):
    def test_bad_parser_class(self):
        with self.assertRaisesRegex(Exception, "Failed to import parser class 'geotrek.common.tests.test_parsers.DoesNotExist'"):
            call_command('import', 'geotrek.common.tests.test_parsers.DoesNotExist', '', verbosity=0)

    def test_bad_parser_file(self):
        with self.assertRaisesRegex(Exception, "module 'parsers' has no attribute 'DoesNotExist'"):
            call_command('import', 'DoesNotExist', '', verbosity=0)

    def test_no_filename_no_url(self):
        with self.assertRaisesRegex(CommandError, "File path missing"):
            call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', '', verbosity=0)

    def test_bad_filename(self):
        with self.assertRaisesRegex(CommandError, "File does not exists at: find_me/I_am_not_there.shp"):
            call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', 'find_me/I_am_not_there.shp', verbosity=0)

    @override_settings(VAR_DIR=os.path.join(os.path.dirname(__file__), 'data'))
    def test_custom_parser(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'CustomParser', filename, verbosity=0)

    def test_progress(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', filename, verbosity=2, stdout=output)
        self.assertIn('(100%)', output.getvalue())

    def test_create(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', filename, verbosity=0)
        self.assertEqual(Organism.objects.count(), 1)
        organism = Organism.objects.get()
        self.assertEqual(organism.organism, "2.0")

    def test_duplicate_without_eid(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', filename, verbosity=0)
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismParser', filename, verbosity=0)
        self.assertEqual(Organism.objects.count(), 2)

    def test_unmodified_with_eid(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismEidParser', filename, verbosity=0)
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismEidParser', filename, verbosity=0)
        self.assertEqual(Organism.objects.count(), 1)

    def test_updated_with_eid(self):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        filename2 = os.path.join(os.path.dirname(__file__), 'data', 'organism2.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismEidParser', filename, verbosity=0)
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismEidParser', filename2, verbosity=0)
        self.assertEqual(Organism.objects.count(), 2)
        organisms = Organism.objects.order_by('pk')
        self.assertEqual(organisms[0].organism, "2.0")
        self.assertEqual(organisms[1].organism, "Comité Hippolyte")

    def test_report_format_text(self):
        parser = OrganismParser()
        self.assertRegex(parser.report(), '0/0 lines imported.')
        self.assertNotRegex(parser.report(), r'<div id=\"collapse-\$celery_id\" class=\"collapse\">')

    def test_report_format_html(self):
        parser = OrganismParser()
        self.assertRegex(parser.report(output_format='html'),
                         r'<div id=\"collapse-\$celery_id\" class=\"collapse\">')

    def test_report_format_bad(self):
        parser = OrganismParser()
        with self.assertRaises(TemplateDoesNotExist):
            parser.report(output_format='toto')

    @mock.patch('geotrek.common.parsers.Parser.parse_row')
    def test_databaseerror_except(self, mock_parse_row):
        output = StringIO()
        mock_parse_row.side_effect = DatabaseError('foo bar')
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismEidParser', filename, verbosity=2, stdout=output)
        self.assertIn('foo bar', output.getvalue())

    def test_fk_not_in_natural_keys(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism5.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismNoNaturalKeysParser', filename, verbosity=2, stdout=output)
        self.assertIn("Destination field 'structure' not in natural keys configuration", output.getvalue())

    def test_no_mapping_not_partial(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism5.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismNoMappingNoPartialParser', filename, verbosity=2, stdout=output)
        self.assertIn("Bad value 'Structure' for field STRUCTURE. Should be in ['foo', '']", output.getvalue())

    def test_no_mapping_partial(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism5.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.OrganismNoMappingPartialParser', filename, verbosity=2, stdout=output)
        self.assertIn("Bad value 'Structure' for field STRUCTURE. Should contain ['foo']", output.getvalue())


class ThemeParser(ExcelParser):
    """Parser used in MultilangParserTests, using Theme because it has a translated field"""
    model = Theme
    eid = 'label'  # Ensure that already created themes with same name will be updated
    fields = {'label': 'Nom'}


class MultilangThemeParser(ThemeParser):
    """Parser used in MultilangParserTests, using Theme because it has a translated field"""
    fill_empty_translated_fields = True


class MultilangFilterThemeParser(MultilangThemeParser):
    """Parser used in MultilangParserTests, using Theme because it has a translated field"""

    def filter_label(self, src, val):
        return 'filtered {}'.format(val)


@override_settings(MODELTRANSLATION_DEFAULT_LANGUAGE="fr", LANGUAGE_CODE='fr')
class MultilangParserTests(TestCase):
    """Test for translated fields
- case 1 : flow has only one data
    - choose to fill all empty fields `label_fr`, `label_en`…
    - choose to fill only default language field `label`
- TODO: case 2 : flow has a data per language
    - fill fields / language, if no data fill with default language
    - only fill fields / language when data is present
"""

    def test_parser_fill_translated_fields_off(self):
        """Parser should not fill empty fields for all languages, only main language"""
        filename = os.path.join(os.path.dirname(__file__), 'data', 'themes.xls')
        label_default_language = "label_{}".format(settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
        other_languages = [lang for lang in settings.MODELTRANSLATION_LANGUAGES if lang != settings.MODELTRANSLATION_DEFAULT_LANGUAGE]
        call_command('import', 'geotrek.common.tests.test_parsers.ThemeParser', filename, verbosity=0)

        theme_imported = Theme.objects.get(label="Paysages")
        self.assertEqual(getattr(theme_imported, label_default_language), "Paysages")
        for language in other_languages:
            label_language = "label_{}".format(language)
            self.assertIsNone(getattr(theme_imported, label_language))

    def test_parser_fill_translated_fields_on(self):
        """Parser should fill empty fields for all languages"""
        filename = os.path.join(os.path.dirname(__file__), 'data', 'themes.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.MultilangThemeParser', filename, verbosity=0)
        theme_imported = Theme.objects.get(label="Paysages")
        self.assertEqual(theme_imported.label_fr, theme_imported.label_en)

    def test_parser_fill_translated_fields_on_only_empty(self):
        """Parser should fill empty fields for all languages"""
        theme_landscape = ThemeFactory(label="Paysages", label_en="Landscape")
        filename = os.path.join(os.path.dirname(__file__), 'data', 'themes.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.MultilangThemeParser', filename, verbosity=0)
        theme_imported = Theme.objects.get(label="Paysages")
        self.assertEqual(theme_imported, theme_landscape)
        self.assertEqual(theme_imported.label_en, "Landscape")

    def test_parser_fill_translated_fields_with_apply_method(self):
        """Parser should first apply filter method before"""
        filename = os.path.join(os.path.dirname(__file__), 'data', 'themes.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.MultilangFilterThemeParser', filename, verbosity=0)
        theme_imported = Theme.objects.get(label="filtered Paysages")
        self.assertEqual(theme_imported.label_fr, theme_imported.label_en)
        self.assertEqual(theme_imported.label_fr, 'filtered Paysages')


class AttachmentParserTests(TestCase):
    def setUp(self):
        self.filetype = FileType.objects.create(type="Photographie")

    @mock.patch('requests.get')
    def test_attachment(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = get_dummy_img()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        organism = Organism.objects.get()
        attachment = Attachment.objects.get()
        self.assertEqual(attachment.content_object, organism)
        self.assertEqual(attachment.attachment_file.name, 'paperclip/common_organism/{pk}/titi.png'.format(pk=organism.pk))
        self.assertEqual(attachment.filetype, self.filetype)
        self.assertTrue(attachment.is_image)
        self.assertTrue(os.path.exists(attachment.attachment_file.path), True)

    @mock.patch('requests.get')
    def test_attachment_connection_error(self, mocked):
        mocked.return_value.status_code = 200
        mocked.side_effect = requests.exceptions.ConnectionError("Error connection")
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        output = StringIO()
        output_3 = StringIO()
        call_command('import', 'geotrek.common.tests.test_parsers.WarnAttachmentParser', filename, verbosity=2,
                     stdout=output, stderr=output_3)
        self.assertFalse(Attachment.objects.exists())
        self.assertIn("Failed to load attachment: Error connection", output.getvalue())

    @mock.patch('requests.get')
    @override_settings(PAPERCLIP_MAX_BYTES_SIZE_IMAGE=20)
    def test_attachment_bigger_size(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = get_dummy_img()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)

        self.assertEqual(Attachment.objects.count(), 0)
        with override_settings(PAPERCLIP_MAX_BYTES_SIZE_IMAGE=86):
            # Dummy Image is of size 85
            call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
            self.assertEqual(Attachment.objects.count(), 1)

    @mock.patch('requests.get')
    @override_settings(PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH=6)
    def test_attachment_min_width(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = get_dummy_img()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)

        self.assertEqual(Attachment.objects.count(), 0)
        with override_settings(PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH=4):
            # Dummy Image is of size 85
            call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
            self.assertEqual(Attachment.objects.count(), 1)

    @mock.patch('requests.get')
    @override_settings(PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT=6)
    def test_attachment_min_height(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = get_dummy_img()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)

        self.assertEqual(Attachment.objects.count(), 0)
        with override_settings(PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT=4):
            # Dummy Image is of size 85
            call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
            self.assertEqual(Attachment.objects.count(), 1)

    @mock.patch('requests.get')
    def test_attachment_long_name(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = b''
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism3.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        organism = Organism.objects.get()
        attachment = Attachment.objects.get()
        self.assertEqual(attachment.content_object, organism)
        self.assertEqual(attachment.attachment_file.name,
                         'paperclip/common_organism/{pk}/{ti}.png'.format(pk=organism.pk, ti='ti' * 64))
        self.assertEqual(attachment.filetype, self.filetype)
        self.assertTrue(os.path.exists(attachment.attachment_file.path), True)

    @mock.patch('requests.get')
    def test_attachment_long_legend(self, mocked):
        mocked.return_value.status_code = 200
        mocked.return_value.content = b''
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism4.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentLegendParser', filename, verbosity=0)
        organism = Organism.objects.get()
        attachment = Attachment.objects.get()
        self.assertEqual(attachment.content_object, organism)
        self.assertEqual(attachment.legend,
                         '{0}'.format(('Legend ' * 18).rstrip()))
        self.assertEqual(attachment.filetype, self.filetype)
        self.assertTrue(os.path.exists(attachment.attachment_file.path), True)

    @mock.patch('requests.get')
    @mock.patch('PIL.Image.open')
    def test_catch_decompression_error(self, mocked_open, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_open.side_effect = ValueError("Decompressed Data Too Large")
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism4.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentLegendParser', filename, verbosity=0)
        self.assertEqual(Attachment.objects.count(), 0)

    @mock.patch('requests.get')
    def test_attachment_with_other_filetype_with_structure(self, mocked):
        """
        It will always take the one without structure first
        """
        structure = StructureFactory.create(name="Structure")
        FileType.objects.create(type="Photographie", structure=structure)
        mocked.return_value.status_code = 200
        mocked.return_value.content = b''
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        organism = Organism.objects.get()
        attachment = Attachment.objects.get()
        self.assertEqual(attachment.content_object, organism)
        self.assertEqual(attachment.attachment_file.name, 'paperclip/common_organism/{pk}/titi.png'.format(pk=organism.pk))
        self.assertEqual(attachment.filetype, self.filetype)
        self.assertEqual(attachment.filetype.structure, None)
        self.assertTrue(os.path.exists(attachment.attachment_file.path), True)

    @mock.patch('requests.get')
    def test_attachment_with_no_filetype_photographie(self, mocked):
        self.filetype.delete()
        mocked.return_value.status_code = 200
        mocked.return_value.content = b''
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        with self.assertRaisesRegex(CommandError, "FileType 'Photographie' does not exists in Geotrek-Admin. Please add it"):
            call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_attachment_not_updated(self, mocked_head, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200
        mocked_head.return_value.headers = {'content-length': 0}
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        attachment = Attachment.objects.first()
        old_name = attachment.attachment_file.name
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(Attachment.objects.first().attachment_file.name, old_name)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_attachment_not_updated_partially_changed(self, mocked_head, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200
        mocked_head.return_value.headers = {'content-length': 0}
        filename_no_legend = os.path.join(os.path.dirname(__file__), 'data', 'attachment_no_legend.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename_no_legend, verbosity=0)
        attachment = Attachment.objects.get()
        old_name = attachment.attachment_file.name
        self.assertEqual(attachment.legend, '')
        self.assertEqual(attachment.author, '')
        filename = os.path.join(os.path.dirname(__file__), 'data', 'attachment.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentLegendParser', filename, verbosity=0)
        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(Attachment.objects.count(), 1)
        attachment.refresh_from_db()
        self.assertEqual(attachment.attachment_file.name, old_name)
        self.assertEqual(attachment.legend, 'legend')
        self.assertEqual(attachment.author, 'name')

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_attachment_updated_file_not_found(self, mocked_head, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200
        mocked_head.return_value.headers = {'content-length': 0}
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        attachment = Attachment.objects.get()
        old_name = attachment.attachment_file.name
        os.remove(attachment.attachment_file.path)
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        self.assertEqual(mocked_get.call_count, 2)
        self.assertEqual(Attachment.objects.count(), 1)
        attachment = Attachment.objects.first()
        # New file has same name as deleted one
        self.assertEqual(attachment.attachment_file.name, old_name)

    @override_settings(PARSER_RETRY_SLEEP_TIME=0)
    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_attachment_request_fail(self, mocked_head, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 503
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(mocked_head.call_count, 3)
        self.assertEqual(Attachment.objects.count(), 1)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_attachment_request_except(self, mocked_head, mocked_get):
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_head.side_effect = DownloadImportError()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(mocked_head.call_count, 1)
        self.assertEqual(Attachment.objects.count(), 1)

    @mock.patch('requests.get')
    @mock.patch('geotrek.common.parsers.urlparse')
    def test_attachment_download_fail(self, mocked_urlparse, mocked_get):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        mocked_get.side_effect = DownloadImportError("DownloadImportError")
        mocked_urlparse.return_value = urlparse('ftp://test.url.com/organism.xls')
        output = StringIO()
        call_command('import', 'geotrek.common.tests.test_parsers.WarnAttachmentParser', filename, verbosity=2,
                     stdout=output)
        self.assertIn("Failed to load attachment: DownloadImportError", output.getvalue())
        self.assertEqual(mocked_get.call_count, 1)

    @mock.patch('requests.get')
    def test_attachment_no_content(self, mocked):
        """
        It will always take the one without structure first
        """
        def mocked_requests_get(*args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            response._content = None
            return response

        # Mock GET
        mocked.side_effect = mocked_requests_get
        structure = StructureFactory.create(name="Structure")
        FileType.objects.create(type="Photographie", structure=structure)
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=0)
        self.assertEqual(Attachment.objects.count(), 0)

    @mock.patch('requests.get')
    def test_attachment_bad_mimetype(self, mocked_get):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism6.xls')
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = get_dummy_img()
        output = StringIO()
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=2,
                     stdout=output)
        self.assertEqual(Organism.objects.count(), 1)
        self.assertEqual(Attachment.objects.count(), 0)
        org = Organism.objects.first()
        self.assertIn(f"Invalid attachment file http://toto.tata/titi.jpeg for Organism #{org.pk}: File mime type 'image/png' is not allowed for jpeg.", output.getvalue())
        self.assertEqual(mocked_get.call_count, 1)

    @mock.patch('requests.get')
    def test_attachment_bad_extension(self, mocked_get):
        filename = os.path.join(os.path.dirname(__file__), 'data', 'organism7.xls')
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = get_dummy_img()
        output = StringIO()
        call_command('import', 'geotrek.common.tests.test_parsers.AttachmentParser', filename, verbosity=2,
                     stdout=output)
        self.assertEqual(Organism.objects.count(), 1)
        self.assertEqual(Attachment.objects.count(), 0)
        org = Organism.objects.first()
        self.assertIn(f"Invalid attachment file http://toto.tata/titi.unknown for Organism #{org.pk}: File type 'unknown' is not allowed.", output.getvalue())
        self.assertEqual(mocked_get.call_count, 1)


class TestXmlParser(XmlParser):
    results_path = 'Result/el'
    model = Organism

    fields = {'organism': 'ORGANISM'}

    def __init__(self):
        self.filename = os.path.join(os.path.dirname(__file__), 'data', 'test.xml')
        self.filetype = FileType.objects.create(type="Photographie")
        super().__init__()


class XMLParserTests(TestCase):
    def test_xml_parser(self):
        parser = TestXmlParser()
        parser.parse()
        self.assertEqual(Organism.objects.count(), 1)
        self.assertEqual(Organism.objects.get().organism, 'Organism a')

    def test_parser_limit(self):
        parser = TestXmlParser()
        parser.parse(limit=-1)
        self.assertEqual(Organism.objects.count(), 0)


class TourInSoftParserTests(TestCase):

    def test_attachment(self):
        class TestTourParser(TourInSoftParser):
            separator = '##'
            separator2 = '||'

            def __init__(self):
                self.model = Trek
                super().__init__()

        parser = TestTourParser()
        result = parser.filter_attachments('', 'a||b||c##||||##d||e||f')
        self.assertListEqual(result, [['a', 'b', 'c'], ['d', 'e', 'f']])

    def test_moyen_de_com_split_failure(self):
        class TestTourParser(TourInSoftParser):
            def __init__(self):
                self.model = Trek
                super().__init__()

        parser = TestTourParser()
        with self.assertRaises(ValueImportError):
            parser.filter_email('', 'Téléphone filaire|02 37 37 80 11#Instagram|#chateaudesenonches')
        with self.assertRaises(ValueImportError):
            parser.filter_website('', 'Mél|chateau.senonches@gmail.Com#Instagram|#chateaudesenonches')
        with self.assertRaises(ValueImportError):
            parser.filter_contact('', ('Mél|chateau.senonches@gmail.Com#Instagram|#chateaudesenonches', ''))


class TourismSystemParserTest(TestCase):
    @mock.patch('geotrek.common.parsers.HTTPBasicAuth')
    @mock.patch('requests.get')
    def test_attachment(self, mocked_get, mocked_auth):
        class TestTourismSystemParser(TourismSystemParser):
            def __init__(self):
                self.model = Trek
                self.filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
                self.filetype = FileType.objects.create(type="Photographie")
                self.login = "test"
                self.password = "test"
                super().__init__()

        def side_effect():
            response = Response()
            response.status_code = 200
            response._content = bytes('{\"metadata\": {\"total\": 1}, \"data\": [] }', 'utf-8')
            response.encoding = 'utf-8'
            return response

        mocked_auth.return_value = None
        mocked_get.return_value = side_effect()
        parser = TestTourismSystemParser()
        parser.parse()
        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(mocked_auth.call_count, 1)


class OpenSystemParserTest(TestCase):
    @mock.patch('requests.get')
    def test_attachment(self, mocked_get):
        class TestOpenSystemParser(OpenSystemParser):
            def __init__(self):
                self.model = Trek
                self.filename = os.path.join(os.path.dirname(__file__), 'data', 'organism.xls')
                self.filetype = FileType.objects.create(type="Photographie")
                self.login = "test"
                self.password = "test"
                super().__init__()

        def side_effect():
            response = Response()
            response.status_code = 200
            response._content = bytes(
                "<?xml version=\"1.0\"?><Data><Resultat><Objets>[]</Objets></Resultat></Data>",
                'utf-8'
            )
            return response

        mocked_get.return_value = side_effect()
        parser = TestOpenSystemParser()
        parser.parse()
        self.assertEqual(mocked_get.call_count, 1)


class GeotrekTrekTestParser(GeotrekParser):
    url = "https://test.fr"
    model = Trek
    url_categories = {
        'foo_field': 'test'
    }


class GeotrekTrekTestProviderParser(GeotrekTrekParser):
    url = "https://test.fr"
    provider = "Provider1"
    default_language = "fr"
    delete = True
    url_categories = {}
    constant_fields = {'structure': settings.DEFAULT_STRUCTURE_NAME}


class GeotrekTrekTestNoProviderParser(GeotrekTrekParser):
    url = "https://test.fr"
    delete = True
    url_categories = {}
    constant_fields = {'structure': settings.DEFAULT_STRUCTURE_NAME}


class GeotrekAggregatorTestParser(GeotrekAggregatorParser):
    pass


class GeotrekParserTest(GeotrekParserTestMixin, TestCase):
    def setUp(self, *args, **kwargs):
        self.filetype = FileType.objects.create(type="Photographie")

    def test_improperly_configurated_categories(self):
        with self.assertRaisesRegex(ImproperlyConfigured, 'foo_field is not configured in categories_keys_api_v2'):
            call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestParser', verbosity=2)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_delete_according_to_provider(self, mocked_head, mocked_get):
        self.mock_time = 0
        self.mock_json_order = [
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json'),
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json'),
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json')]

        # Mock GET
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json = self.mock_json
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200

        call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestProviderParser', verbosity=0)
        self.assertEqual(Trek.objects.count(), 1)
        t = Trek.objects.first()
        self.assertEqual(t.eid, "58ed4fc1-645d-4bf6-b956-71f0a01a5eec")
        self.assertEqual(str(t.uuid), "58ed4fc1-645d-4bf6-b956-71f0a01a5eec")
        self.assertEqual(t.provider, "Provider1")
        self.assertEqual(t.description_teaser, "Header")
        self.assertEqual(t.description_teaser_fr, "Chapeau")
        self.assertEqual(t.description_teaser_en, "Header")
        TrekFactory(provider="Provider1", name="I should be deleted", eid="1234")
        t2 = TrekFactory(provider="Provider2", name="I should not be deleted", eid="1236")
        t3 = TrekFactory(provider="", name="I should not be deleted", eid="12374")
        call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestProviderParser', verbosity=0)
        self.assertEqual({t.pk, t2.pk, t3.pk}, set(Trek.objects.values_list('pk', flat=True)))
        call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestProviderParser', verbosity=0)
        self.assertEqual({t.pk, t2.pk, t3.pk}, set(Trek.objects.values_list('pk', flat=True)))

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_delete_according_to_no_provider(self, mocked_head, mocked_get):
        self.mock_time = 0
        self.mock_json_order = [
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json'),
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json'),
            ('common', 'treks.json'),
            ('common', 'treks.json'),
            ('trekking', 'trek_no_children.json')]

        # Mock GET
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json = self.mock_json
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200

        self.assertEqual(Trek.objects.count(), 0)
        call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestNoProviderParser', verbosity=0)
        self.assertEqual(Trek.objects.count(), 1)
        t = Trek.objects.first()
        self.assertEqual(t.provider, "")
        self.assertEqual(t.eid, "58ed4fc1-645d-4bf6-b956-71f0a01a5eec")
        self.assertEqual(str(t.uuid), "58ed4fc1-645d-4bf6-b956-71f0a01a5eec")
        TrekFactory(provider="", name="I should be deleted", eid="12374")
        call_command('import', 'geotrek.common.tests.test_parsers.GeotrekTrekTestNoProviderParser', verbosity=0)
        self.assertEqual([t.pk], list(Trek.objects.values_list('pk', flat=True)))


class GeotrekAggregatorParserTest(GeotrekParserTestMixin, TestCase):
    def setUp(self, *args, **kwargs):
        self.filetype = FileType.objects.create(type="Photographie")

    def test_geotrek_aggregator_no_file(self):
        with self.assertRaisesRegex(CommandError, "File does not exists at: config_aggregator_does_not_exist.json"):
            call_command('import', 'geotrek.common.tests.test_parsers.GeotrekAggregatorTestParser',
                         'config_aggregator_does_not_exist.json', verbosity=0)

    @skipIf(settings.TREKKING_TOPOLOGY_ENABLED, 'Test without dynamic segmentation only')
    @mock.patch('geotrek.common.parsers.importlib.import_module', return_value=mock.MagicMock())
    @mock.patch('django.template.loader.render_to_string')
    @mock.patch('requests.get')
    def test_geotrek_aggregator_no_data_to_import(self, mocked_get, mocked_render, mocked_import_module):
        def mocked_json():
            return {}

        def side_effect_render(file, context):
            return 'Render'

        mocked_get.json = mocked_json
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_render.side_effect = side_effect_render
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'geotrek_parser_v2',
                                'config_aggregator_no_data_to_import.json')
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        stdout_parser = output.getvalue()
        self.assertIn('Render\n', stdout_parser)
        self.assertIn('(URL_1) (00%)', stdout_parser)
        self.assertIn('(URL_1) (100%)', stdout_parser)
        # Trek, POI, Service, InformationDesk, TouristicContent, TouristicEvent, Signage, Infrastructure
        self.assertEqual(10, mocked_import_module.call_count)

    @skipIf(not settings.TREKKING_TOPOLOGY_ENABLED, 'Test with dynamic segmentation only')
    def test_geotrek_aggregator_parser_model_dynamic_segmentation(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'geotrek_parser_v2', 'config_aggregator_ds.json')
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        string_parser = output.getvalue()
        self.assertIn("Services can't be imported with dynamic segmentation", string_parser)
        self.assertIn("POIs can't be imported with dynamic segmentation", string_parser)
        self.assertIn("Treks can't be imported with dynamic segmentation", string_parser)

    @skipIf(settings.TREKKING_TOPOLOGY_ENABLED, 'Test without dynamic segmentation only')
    @mock.patch('geotrek.common.parsers.importlib.import_module', return_value=mock.MagicMock())
    @mock.patch('django.template.loader.render_to_string')
    @mock.patch('requests.get')
    def test_geotrek_aggregator_parser_multiple_admin(self, mocked_get, mocked_render, mocked_import_module):
        def mocked_json():
            return {}

        def side_effect_render(file, context):
            return 'Render'

        mocked_get.json = mocked_json
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = b''
        mocked_render.side_effect = side_effect_render
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'geotrek_parser_v2',
                                'config_aggregator_multiple_admin.json')
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        stdout_parser = output.getvalue()
        self.assertIn('Render\n', stdout_parser)

        self.assertIn('(URL_1) (00%)', stdout_parser)
        self.assertIn('(URL_1) (100%)', stdout_parser)
        # "VTT", "Vélo"
        # "Trek", "Service", "POI"
        # "POI", "InformationDesk", "TouristicContent"
        self.assertEqual(8, mocked_import_module.call_count)

    @skipIf(settings.TREKKING_TOPOLOGY_ENABLED, 'Test without dynamic segmentation only')
    def test_geotrek_aggregator_parser_no_url(self):
        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'geotrek_parser_v2', 'config_aggregator_no_url.json')
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        string_parser = output.getvalue()

        self.assertIn('URL_1 has no url', string_parser)

    @skipIf(settings.TREKKING_TOPOLOGY_ENABLED, 'Test without dynamic segmentation only')
    @mock.patch('requests.get')
    @mock.patch('requests.head')
    @override_settings(MODELTRANSLATION_DEFAULT_LANGUAGE="fr", LANGUAGE_CODE='fr')
    def test_geotrek_aggregator_parser(self, mocked_head, mocked_get):
        self.mock_time = 0
        # First every categories (inside __init__)
        # Then inside start_meta()
        # start()
        # parse()
        # end()
        # start()
        # parse()
        # end()
        # end_meta()
        self.mock_json_order = [
            # First time
            ('trekking', 'structure.json'),
            ('trekking', 'trek_difficulty.json'),
            ('trekking', 'trek_route.json'),
            ('trekking', 'trek_theme.json'),
            ('trekking', 'trek_practice.json'),
            ('trekking', 'trek_accessibility.json'),
            ('trekking', 'trek_network.json'),
            ('trekking', 'trek_label.json'),
            ('trekking', 'sources.json'),
            ('trekking', 'sources.json'),
            ('trekking', 'structure.json'),
            ('trekking', 'poi_type.json'),
            ('trekking', 'trek_ids.json'),
            ('trekking', 'trek.json'),
            ('trekking', 'trek_children.json'),
            ('trekking', 'trek_published_step.json'),
            ('trekking', 'trek_unpublished_step.json'),
            ('trekking', 'trek_unpublished_structure.json'),
            ('trekking', 'trek_unpublished_practice.json'),
            ('trekking', 'poi_ids.json'),
            ('trekking', 'poi.json'),
            ('tourism', 'informationdesk_ids.json'),
            ('tourism', 'informationdesk.json'),

            #  End meta first time
            ('tourism', 'informationdesk.json'),
            ('trekking', 'trek_informationdesk.json'),

            # Second time
            ('trekking', 'structure.json'),
            ('trekking', 'trek_difficulty.json'),
            ('trekking', 'trek_route.json'),
            ('trekking', 'trek_theme.json'),
            ('trekking', 'trek_practice.json'),
            ('trekking', 'trek_accessibility.json'),
            ('trekking', 'trek_network.json'),
            ('trekking', 'trek_label.json'),
            ('trekking', 'sources.json'),
            ('trekking', 'sources.json'),
            ('trekking', 'structure.json'),
            ('trekking', 'poi_type.json'),
            ('trekking', 'trek_ids.json'),
            ('trekking', 'trek.json'),
            ('trekking', 'trek_children.json'),
            ('trekking', 'trek_published_step.json'),
            ('trekking', 'trek_unpublished_step.json'),
            ('trekking', 'trek_unpublished_structure.json'),
            ('trekking', 'trek_unpublished_practice.json'),
            ('trekking', 'poi_ids.json'),
            ('trekking', 'poi.json'),
            ('tourism', 'informationdesk_ids.json'),
            ('tourism', 'informationdesk.json'),
            # End meta second time
            ('tourism', 'informationdesk_treks.json'),
            ('trekking', 'trek_informationdesk_2.json')
        ]

        # Mock GET
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json = self.mock_json
        mocked_get.return_value.content = b''
        mocked_head.return_value.status_code = 200

        output = StringIO()
        filename = os.path.join(os.path.dirname(__file__), 'data', 'geotrek_parser_v2', 'config_aggregator.json')
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        string_parser = output.getvalue()
        self.assertIn('0000: Trek (URL_1) (00%)', string_parser)
        self.assertIn('0000: Poi (URL_1) (00%)', string_parser)
        # Published Tour steps are imported twice, but created once
        self.assertIn('7/7 lignes importées.', string_parser)
        self.assertIn('6 enregistrements créés.', string_parser)
        self.assertIn('2/2 lignes importées.', string_parser)
        self.assertEqual(Trek.objects.count(), 6)
        self.assertEqual(POI.objects.count(), 2)
        self.assertEqual(1, Trek.objects.get(name="Foo").information_desks.count())
        self.assertEqual("Office de Tourisme de Seix",
                         Trek.objects.get(name="Foo").information_desks.first().name)
        self.assertEqual(3, Trek.objects.get(name="Boucle du Pic des Trois Seigneurs").information_desks.count())
        call_command('import', 'geotrek.common.parsers.GeotrekAggregatorParser', filename=filename, verbosity=2,
                     stdout=output)
        self.assertEqual(1, Trek.objects.get(name="Boucle du Pic des Trois Seigneurs").information_desks.count())


class GeotrekTrekTestSourcesParser(GeotrekTrekParser):
    url = "https://test.fr"
    model = Trek
    url_categories = {
        'source': 'source'
    }
    field_options = {
        'source': {'create': True}
    }
    constant_fields = {'structure': settings.DEFAULT_STRUCTURE_NAME}


class GeotrekAggregatorSourcesTests(TestCase):

    def mocked_responses(self, url):
        class MockResponse:
            def __init__(self, mock_time, status_code):
                self.content = SVG_FILE
                self.mock_time = mock_time
                self.mock_json_order = [
                    # First time
                    ('trekking', 'sources.json'),
                    ('trekking', 'sources.json'),
                    # # Second time
                    ('trekking', 'sources.json'),
                    ('trekking', 'sources_updated.json'),
                    # Third time
                    ('trekking', 'sources.json'),
                    ('trekking', 'sources_error_1.json'),
                    ('trekking', 'iwillthrowerror.json"'),
                    # Fourth time
                    ('trekking', 'sources.json'),
                    ('trekking', 'sources_error_2.json'),
                ]
                self.status_code = status_code

            def json(self):
                filename = os.path.join('geotrek', self.mock_json_order[self.mock_time][0], 'tests', 'data', 'geotrek_parser_v2',
                                        self.mock_json_order[self.mock_time][1])
                with open(filename, 'r') as f:
                    return json.load(f)

        if self.mock_time == 6:
            self.mock_time += 1
            raise requests.exceptions.ConnectionError
        status_code = 200
        if self.mock_time == 9:
            status_code = 404
            self.mock_time += 1
        mocked_response = MockResponse(self.mock_time, status_code)
        if ".png" not in url:
            self.mock_time += 1
        return mocked_response

    @mock.patch('requests.get')
    @mock.patch('geotrek.common.parsers.GeotrekParser.request_or_retry')
    @mock.patch('geotrek.common.parsers.GeotrekParser.add_warning')
    def test_sources_extra_fields_parsing(self, mocked_add_warning, mocked_request_or_retry, mocked_get):
        self.mock_time = 0
        mocked_request_or_retry.side_effect = self.mocked_responses

        # Test created
        GeotrekTrekTestSourcesParser()
        s = RecordSource.objects.get(name="Parc national des Ecrins")
        self.assertEqual(s.website, "https://www.ecrins-parcnational.fr")
        self.assertEqual(s.pictogram.file.name.split('/')[-1], "pnecrins.png")

        # Test updated
        GeotrekTrekTestSourcesParser()
        s.refresh_from_db()
        self.assertEqual(s.website, "")
        self.assertEqual(s.pictogram, "")

        # Test Connection Error
        GeotrekTrekTestSourcesParser()
        mocked_add_warning.assert_called_with("Failed to download 'https://geotrek-admin.ecrins-parcnational.fr/media/upload/iwillthrowerror.png'")

        # Test bad response status
        GeotrekTrekTestSourcesParser()
        mocked_add_warning.assert_called_with("Failed to download 'https://geotrek-admin.ecrins-parcnational.fr/media/upload/iwillthrowerroragain.png'")
