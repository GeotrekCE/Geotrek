from io import BytesIO
import importlib
import json
import os
from pathlib import PurePath
import re
import requests
import logging
import magic
import mimetypes
from requests.auth import HTTPBasicAuth
import textwrap
import xlrd
import xml.etree.ElementTree as ET
from functools import reduce
from collections.abc import Iterable
from time import sleep
from PIL import Image, UnidentifiedImageError

from ftplib import FTP
from os.path import dirname
from urllib.parse import urlparse

from django.contrib.gis.geos import GEOSGeometry, WKBWriter
from django.db import models, connection
from django.db.models.fields import NOT_PROVIDED
from django.db.utils import DatabaseError, InternalError
from django.contrib.auth import get_user_model
from django.contrib.gis.gdal import DataSource, GDALException, CoordTransform
from django.contrib.gis.geos import Point, Polygon
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext as _
from django.utils.encoding import force_str
from django.conf import settings
from paperclip.models import attachment_upload, random_suffix_regexp
from modeltranslation.utils import build_localized_fieldname

from geotrek.authent.models import default_structure
from geotrek.common.models import FileType, Attachment, License
from geotrek.common.utils.parsers import add_http_prefix
from geotrek.common.utils.translation import get_translated_fields


if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.fields import TranslationField

logger = logging.getLogger(__name__)


class ImportError(Exception):
    pass


class GlobalImportError(ImportError):
    pass


class RowImportError(ImportError):
    pass


class ValueImportError(ImportError):
    pass


class DownloadImportError(ImportError):
    pass


class Parser:
    """
    provider: Allow to differentiate multiple Parser for the same model
    default_language: Allow to define which language this parser will populate by default
    headers: Allow to configure headers on parser requests
    """
    label = None
    model = None
    filename = None
    url = None
    simplify_tolerance = 0  # meters
    update_only = False
    delete = False
    duplicate_eid_allowed = False
    fill_empty_translated_fields = False
    warn_on_missing_fields = False
    warn_on_missing_objects = False
    separator = '+'
    eid = None
    provider = None
    fields = None
    m2m_fields = {}
    constant_fields = {}
    m2m_constant_fields = {}
    m2m_aggregate_fields = []
    non_fields = {}
    natural_keys = {}
    field_options = {}
    default_language = None
    headers = {"User-Agent": "Geotrek-Admin"}

    def __init__(self, progress_cb=None, user=None, encoding='utf8'):
        self.warnings = {}
        self.line = 0
        self.nb_success = 0
        self.nb_created = 0
        self.nb_updated = 0
        self.nb_unmodified = 0
        self.progress_cb = progress_cb
        self.user = user
        self.structure = user and user.profile.structure or default_structure()
        self.encoding = encoding
        self.translated_fields = get_translated_fields(self.model)

        if self.fields is None:
            self.fields = {
                f.name: force_str(f.verbose_name)
                for f in self.model._meta.fields
                if not isinstance(f, TranslationField)
            }
            self.m2m_fields = {
                f.name: force_str(f.verbose_name)
                for f in self.model._meta.many_to_many
            }

        if self.default_language and self.default_language in settings.MODELTRANSLATION_LANGUAGES:
            translation.activate(self.default_language)
        else:
            translation.activate(settings.MODELTRANSLATION_DEFAULT_LANGUAGE)

    def normalize_field_name(self, name):
        return name.upper()

    def normalize_src(self, src):
        if isinstance(src, Iterable) and not isinstance(src, str):
            return [self.normalize_field_name(subsrc) for subsrc in src]
        else:
            return self.normalize_field_name(src)

    def add_warning(self, msg):
        key = _("Line {line}".format(line=self.line))
        warnings = self.warnings.setdefault(key, [])
        warnings.append(msg)

    def get_part(self, dst, src, val):
        if not src:
            return val
        if val is None:
            return None
        if '.' in src:
            part, left = src.split('.', 1)
        else:
            part, left = src, ''
        try:
            value = int(part)
            return self.get_part(dst, left, val[value])
        except ValueError:
            if part == '*':
                return [self.get_part(dst, left, subval) for subval in val]
            else:
                return self.get_part(dst, left, val[part])

    def get_val(self, row, dst, src):
        if isinstance(src, Iterable) and not isinstance(src, str):
            val = []
            for subsrc in src:
                try:
                    val.append(self.get_val(row, dst, subsrc))
                except ValueImportError as warning:
                    if self.warn_on_missing_fields:
                        self.add_warning(str(warning))
                    val.append(None)
            return val
        else:
            try:
                return self.get_part(dst, src, row)
            except (KeyError, IndexError):
                required = "required " if self.field_options.get(dst, {}).get('required', False) else ""
                raise ValueImportError(_("Missing {required}field '{src}'").format(required=required, src=src))

    def apply_filter(self, dst, src, val):
        field = self.model._meta.get_field(dst)
        if (isinstance(field, models.ForeignKey) or isinstance(field, models.ManyToManyField)):
            if dst not in self.natural_keys:
                raise ValueImportError(_("Destination field '{dst}' not in natural keys configuration").format(dst=dst))
            to = field.remote_field.model
            natural_key = self.natural_keys[dst]
            kwargs = self.field_options.get(dst, {})
            if isinstance(field, models.ForeignKey):
                val = self.filter_fk(src, val, to, natural_key, **kwargs)
            else:
                val = self.filter_m2m(src, val, to, natural_key, **kwargs)
        return val

    def parse_non_field(self, dst, src, val):
        """Returns True if modified"""
        if hasattr(self, 'save_{0}'.format(dst)):
            return getattr(self, 'save_{0}'.format(dst))(src, val)

    def set_value(self, dst, src, val):
        field = self.model._meta.get_field(dst)
        if val is None and not field.null:
            if field.blank and (isinstance(field, models.CharField) or isinstance(field, models.TextField)):
                val = ""
            else:
                raise RowImportError(_("Null value not allowed for field '{src}'".format(src=src)))
        if val == "" and not field.blank:
            raise RowImportError(_("Blank value not allowed for field '{src}'".format(src=src)))
        if isinstance(field, models.CharField):
            val = str(val)[:256]
        if isinstance(field, models.ManyToManyField):
            fk = getattr(self.obj, dst)
            fk.set(val)
        else:
            setattr(self.obj, dst, val)

    def parse_real_field(self, dst, src, val):
        """Returns True if modified"""
        if hasattr(self.obj, dst):
            if dst in self.m2m_fields or dst in self.m2m_constant_fields:
                old = set(getattr(self.obj, dst).all())
            else:
                old = getattr(self.obj, dst)

        if hasattr(self, 'filter_{0}'.format(dst)):
            val = getattr(self, 'filter_{0}'.format(dst))(src, val)
        else:
            val = self.apply_filter(dst, src, val)
        if hasattr(self.obj, dst):
            if dst in self.m2m_fields or dst in self.m2m_constant_fields:
                val = set(val)
                if dst in self.m2m_aggregate_fields:
                    val = val | old
            if isinstance(old, float) and isinstance(val, float):
                old = round(old, 10)
                val = round(val, 10)
            if isinstance(old, str):
                val = val or ""
            if old != val:
                self.set_value(dst, src, val)
                return True
            else:
                return False
        else:
            self.set_value(dst, src, val)
            return True

    def parse_translation_field(self, dst, src, val):
        """Specific treatment for translated fields
        TODO: check self.default_language to get default values
        TODO: compare each translated fields with source fields :
        this only compares old 'name' with new 'name' but it should compare
            - old 'name_en' with new 'name_en',
            - old 'name_fr' with new 'name_fr'...
        and return "True" if any of them have changed
        """
        val = val or ""
        modified = False
        old_values = {}
        # We keep every old values for each langs to get tracability during filter or apply filter
        for lang in settings.MODELTRANSLATION_LANGUAGES:
            dst_field_lang = build_localized_fieldname(dst, lang)
            old_values[lang] = getattr(self.obj, dst_field_lang)
        # If during filter, the traduction of the field has been changed
        # we can still check if this value has been changed
        if hasattr(self, 'filter_{0}'.format(dst)):
            val_default_language = getattr(self, 'filter_{0}'.format(dst))(src, val)
        else:
            val_default_language = self.apply_filter(dst, src, val)

        for lang in settings.MODELTRANSLATION_LANGUAGES:
            dst_field_lang = build_localized_fieldname(dst, lang)
            new_value = getattr(self.obj, dst_field_lang)
            old_value = old_values[lang]
            # Field not translated, use same val for all translated
            if self.obj._meta.get_field(dst).default == NOT_PROVIDED:
                val_default_language = val_default_language
            else:
                val_default_language = self.obj._meta.get_field(dst).default
            # Set val_default_language only if new empty
            if not new_value:
                # If there is no new value check if old value is different form the default value
                # If this is the same, it means old value was empty and was fill with default value in previous import
                if old_value != val_default_language:
                    self.set_value(dst_field_lang, src, val_default_language)
                    modified = True
            if new_value != old_value:
                modified = True

        return modified

    def parse_field(self, row, dst, src, updated, non_field):
        if dst in self.constant_fields:
            val = self.constant_fields[dst]
        elif dst in self.m2m_constant_fields:
            val = self.m2m_constant_fields[dst]
        else:
            src = self.normalize_src(src)
            val = self.get_val(row, dst, src)
        if non_field:
            modified = self.parse_non_field(dst, src, val)
        elif self.fill_empty_translated_fields and dst in self.translated_fields:
            modified = self.parse_translation_field(dst, src, val)
        else:
            modified = self.parse_real_field(dst, src, val)
        if modified:
            updated.append(dst)
            if dst in self.translated_fields:
                for lang in settings.MODELTRANSLATION_LANGUAGES:
                    updated.append(build_localized_fieldname(dst, lang))

    def parse_fields(self, row, fields, non_field=False):
        updated = []
        for dst, src in fields.items():
            try:
                self.parse_field(row, dst, src, updated, non_field)
            except ValueImportError as warning:
                if self.field_options.get(dst, {}).get('required', False):
                    raise RowImportError(warning)
                if self.warn_on_missing_fields:
                    self.add_warning(str(warning))
                continue
        return updated

    def parse_obj(self, row, operation):
        try:
            update_fields = self.parse_fields(row, self.fields)
            update_fields += self.parse_fields(row, self.constant_fields)
            if 'id' in update_fields:
                update_fields.remove('id')  # Can't update primary key
        except RowImportError as warnings:
            self.add_warning(str(warnings))
            return
        if operation == "created":
            if hasattr(self.model, 'provider') and self.provider is not None and not self.obj.provider:
                self.obj.provider = self.provider
            self.obj.save()
        else:
            self.obj.save(update_fields=update_fields)
        update_fields += self.parse_fields(row, self.m2m_fields)
        update_fields += self.parse_fields(row, self.m2m_constant_fields)
        update_fields += self.parse_fields(row, self.non_fields, non_field=True)
        if operation == "created":
            self.nb_created += 1
        elif update_fields:
            self.nb_updated += 1
        else:
            self.nb_unmodified += 1

    def get_eid_kwargs(self, row):
        try:
            eid_src = self.fields[self.eid]
        except KeyError:
            raise GlobalImportError(_("Eid field '{eid_dst}' missing in parser configuration").format(eid_dst=self.eid))
        eid_src = self.normalize_field_name(eid_src)
        try:
            eid_val = self.get_val(row, self.eid, eid_src)
        except KeyError:
            raise GlobalImportError(_("Missing id field '{eid_src}'").format(eid_src=eid_src))
        if hasattr(self, 'filter_{0}'.format(self.eid)):
            eid_val = getattr(self, 'filter_{0}'.format(self.eid))(eid_src, eid_val)
        self.eid_src = eid_src
        self.eid_val = eid_val
        return {self.eid: eid_val}

    def parse_row(self, row):
        self.eid_val = None
        self.line += 1
        if self.eid is None:
            eid_kwargs = {}
            objects = self.model.objects.none()
        else:
            try:
                eid_kwargs = self.get_eid_kwargs(row)
            except RowImportError as warnings:
                self.add_warning(str(warnings))
                return
            objects = self.model.objects.filter(**eid_kwargs)
            if hasattr(self.model, 'provider') and self.provider is not None:
                objects = objects.filter(provider__exact=self.provider)
        if len(objects) == 0 and self.update_only:
            if self.warn_on_missing_objects:
                self.add_warning(_("Bad value '{eid_val}' for field '{eid_src}'. No object with this identifier").format(eid_val=self.eid_val, eid_src=self.eid_src))
            return
        elif len(objects) == 0:
            obj = self.model(**eid_kwargs)
            if hasattr(obj, 'structure'):
                obj.structure = self.structure
            objects = [obj]
            operation = "created"
        elif len(objects) >= 2 and not self.duplicate_eid_allowed:
            self.add_warning(_("Bad value '{eid_val}' for field '{eid_src}'. Multiple objects with this identifier").format(eid_val=self.eid_val, eid_src=self.eid_src))
            return
        else:
            _objects = []
            for obj in objects:
                if not hasattr(obj, 'structure') or obj.structure == self.structure or self.user is None or self.user.has_perm('authent.can_bypass_structure'):
                    _objects.append(obj)
                else:
                    self.to_delete.discard(obj.pk)
                    self.add_warning(_("Bad ownership '{structure}' for object '{eid_val}'.").format(structure=obj.structure.name, eid_val=self.eid_val))
            objects = _objects
            operation = "updated"
        for self.obj in objects:
            self.parse_obj(row, operation)
            self.to_delete.discard(self.obj.pk)
        self.nb_success += 1  # FIXME
        if self.progress_cb:
            self.progress_cb(float(self.line) / self.nb, self.line, self.eid_val)

    def report(self, output_format='txt'):
        context = {
            'nb_success': self.nb_success,
            'nb_lines': self.line,
            'nb_created': self.nb_created,
            'nb_updated': self.nb_updated,
            'nb_deleted': len(self.to_delete) if self.delete else None,
            'nb_unmodified': self.nb_unmodified,
            'warnings': self.warnings,
        }
        return render_to_string('common/parser_report.{output_format}'.format(output_format=output_format), context)

    def get_mapping(self, src, val, mapping, partial):
        if partial:
            found = False
            for i, j in mapping.items():
                if i in val:
                    val = j
                    found = True
                    break
            if not found:
                values = [str(key) for key in mapping.keys()]
                self.add_warning(_("Bad value '{val}' for field {src}. Should contain {values}").format(val=str(val), src=src, separator=self.separator, values=values))
                return None
        else:
            if mapping is not None:
                if val and val not in mapping.keys():
                    values = [str(key) for key in mapping.keys()]
                    self.add_warning(_("Bad value '{val}' for field {src}. Should be in {values}").format(val=str(val), src=src, separator=self.separator, values=values))
                    return None
                if not val:
                    return None
                val = mapping[val]
        return val

    def filter_fk(self, src, val, model, field, mapping=None, partial=False, create=False, fk=None, **kwargs):
        val = self.get_mapping(src, val, mapping, partial)
        if val is None:
            return None
        fields = {field: val}
        if fk:
            fields[fk] = getattr(self.obj, fk)
        if create:
            val, created = model.objects.get_or_create(**fields)
            if created:
                self.add_warning(_("{model} '{val}' did not exist in Geotrek-Admin and was automatically created").format(model=model._meta.verbose_name.title(), val=val))
            return val
        try:
            return model.objects.get(**fields)
        except model.DoesNotExist:
            self.add_warning(_("{model} '{val}' does not exists in Geotrek-Admin. Please add it").format(model=model._meta.verbose_name.title(), val=val))
            return None

    def filter_m2m(self, src, val, model, field, mapping=None, partial=False, create=False, fk=None, **kwargs):
        if not val:
            return []
        if self.separator and not isinstance(val, list):
            val = val.split(self.separator)
        dst = []
        for subval in val:
            if isinstance(subval, str):
                subval = subval.strip()
            subval = self.get_mapping(src, subval, mapping, partial)
            if subval is None:
                continue
            fields = {field: subval}
            if fk:
                fields[fk] = getattr(self.obj, fk)
            if create:
                subval, created = model.objects.get_or_create(**fields)
                if created:
                    self.add_warning(_("{model} '{val}' did not exist in Geotrek-Admin and was automatically created").format(model=model._meta.verbose_name.title(), val=subval))
                dst.append(subval)
                continue
            try:
                dst.append(model.objects.get(**fields))
            except model.DoesNotExist:
                self.add_warning(_("{model} '{val}' does not exists in Geotrek-Admin. Please add it").format(model=model._meta.verbose_name.title(), val=subval))
                continue
        return dst

    def get_to_delete_kwargs(self):
        # FIXME: use mapping if it exists
        kwargs = {}
        for dst, val in self.constant_fields.items():
            field = self.model._meta.get_field(dst)
            if isinstance(field, models.ForeignKey):
                natural_key = self.natural_keys[dst]
                try:
                    kwargs[dst] = field.remote_field.model.objects.get(**{natural_key: val})
                except field.remote_field.model.DoesNotExist:
                    return None
            else:
                kwargs[dst] = val
        for dst, val in self.m2m_constant_fields.items():
            assert not self.separator or self.separator not in val
            field = self.model._meta.get_field(dst)
            natural_key = self.natural_keys[dst]
            filters = {natural_key: subval for subval in val}
            if not filters:
                continue
            try:
                kwargs[dst] = field.remote_field.model.objects.get(**filters)
            except field.remote_field.model.DoesNotExist:
                return None
        if hasattr(self.model, 'provider') and self.provider is not None:
            kwargs['provider__exact'] = self.provider
        return kwargs

    def start(self):
        kwargs = self.get_to_delete_kwargs()
        if kwargs is None:
            self.to_delete = set()
        else:
            self.to_delete = set(self.model.objects.filter(**kwargs).values_list('pk', flat=True))

    def end(self):
        if self.delete:
            self.model.objects.filter(pk__in=self.to_delete).delete()

    def parse(self, filename=None, limit=None):
        if filename:
            self.filename = filename
        if not self.url and not self.filename:
            raise GlobalImportError(_("Filename or url is required"))
        if self.filename and not os.path.exists(self.filename):
            raise GlobalImportError(_("File does not exists at: {filename}").format(filename=self.filename))
        self.start()
        for i, row in enumerate(self.next_row()):
            if limit and i >= limit:
                break
            try:
                self.parse_row(row)
            except DatabaseError as e:
                if settings.DEBUG:
                    raise
                self.add_warning(str(e))
            except (ValueImportError, RowImportError) as e:
                self.add_warning(str(e))
            except Exception as e:
                raise
                if settings.DEBUG:
                    raise
                self.add_warning(str(e))
        self.end()

    def request_or_retry(self, url, verb='get', **kwargs):
        try_get = settings.PARSER_NUMBER_OF_TRIES
        assert try_get > 0
        while try_get:
            action = getattr(requests, verb)
            response = action(url, headers=self.headers, allow_redirects=True, **kwargs)
            if response.status_code in settings.PARSER_RETRY_HTTP_STATUS:
                logger.info("Failed to fetch url {}. Retrying ...".format(url))
                sleep(settings.PARSER_RETRY_SLEEP_TIME)
                try_get -= 1
            elif response.status_code == 200:
                return response
            else:
                break
        logger.warning("Failed to fetch {} after {} times. Status code : {}.".format(url, settings.PARSER_NUMBER_OF_TRIES, response.status_code))
        raise DownloadImportError(_("Failed to download {url}. HTTP status code {status_code}").format(url=response.url, status_code=response.status_code))


class XmlParser(Parser):
    """XML Parser"""
    ns = {}
    results_path = ''

    def next_row(self):
        if self.filename:
            with open(self.filename) as f:
                self.root = ET.fromstring(f.read())
        else:
            response = requests.get(self.url, params={})
            if response.status_code != 200:
                raise GlobalImportError(_(u"Failed to download {url}. HTTP status code {status_code}").format(
                    url=self.url, status_code=response.status_code))
            self.root = ET.fromstring(response.content)
        entries = self.root.findall(self.results_path, self.ns)
        self.nb = len(entries)
        for row in entries:
            yield row

    def get_part(self, dst, src, val):
        return val.findtext(src, None, self.ns)

    def normalize_field_name(self, name):
        return name


class ShapeParser(Parser):
    def next_row(self):
        datasource = DataSource(self.filename, encoding=self.encoding)
        layer = datasource[0]
        SpatialRefSys = connection.ops.spatial_ref_sys()
        target_srs = SpatialRefSys.objects.get(srid=settings.SRID).srs
        coord_transform = CoordTransform(layer.srs, target_srs)
        self.nb = len(layer)
        for i, feature in enumerate(layer):
            row = {self.normalize_field_name(field.name): field.value for field in feature}
            try:
                ogrgeom = feature.geom
            except GDALException:
                print(_("Invalid geometry pointer"), i)
                geom = None
            else:
                ogrgeom.coord_dim = 2  # Flatten to 2D
                ogrgeom.transform(coord_transform)
                geom = ogrgeom.geos
            if self.simplify_tolerance and geom is not None:
                geom = geom.simplify(self.simplify_tolerance)
            row[self.normalize_field_name('geom')] = geom
            yield row

    def normalize_field_name(self, name):
        """Shapefile field names length is 10 char max"""
        name = super().normalize_field_name(name)
        return name[:10]


class ExcelParser(Parser):
    def next_row(self):
        workbook = xlrd.open_workbook(self.filename)
        sheet = workbook.sheet_by_index(0)
        header = [self.normalize_field_name(cell.value) for cell in sheet.row(0)]
        self.nb = sheet.nrows - 1
        for i in range(1, sheet.nrows):
            values = [cell.value for cell in sheet.row(i)]
            row = dict(zip(header, values))
            yield row


class AtomParser(Parser):
    ns = {
        'Atom': 'http://www.w3.org/2005/Atom',
        'georss': 'http://www.georss.org/georss',
    }

    def flatten_fields(self, fields):
        return reduce(lambda x, y: x + (list(y) if hasattr(y, '__iter__') else [y]), fields.values(), [])

    def next_row(self):
        srcs = self.flatten_fields(self.fields)
        srcs += self.flatten_fields(self.m2m_fields)
        srcs += self.flatten_fields(self.non_fields)
        tree = ET.parse(self.filename)
        entries = tree.getroot().findall('Atom:entry', self.ns)
        self.nb = len(entries)
        for entry in entries:
            row = {self.normalize_field_name(src): entry.find(src, self.ns).text for src in srcs}
            yield row


class AttachmentParserMixin:
    download_attachments = True
    base_url = ''
    delete_attachments = True
    filetype_name = "Photographie"
    non_fields = {
        'attachments': _("Attachments"),
    }

    def start(self):
        super().start()
        if settings.PAPERCLIP_ENABLE_LINK is False and self.download_attachments is False:
            raise Exception('You need to enable PAPERCLIP_ENABLE_LINK to use this function')
        try:
            self.filetype = FileType.objects.get(type=self.filetype_name, structure=None)
        except FileType.DoesNotExist:
            try:
                self.filetype = FileType.objects.get(type=self.filetype_name, structure=self.structure)
            except FileType.DoesNotExist:
                raise GlobalImportError(_("FileType '{name}' does not exists in "
                                          "Geotrek-Admin. Please add it").format(name=self.filetype_name))
        self.creator, created = get_user_model().objects.get_or_create(username='import', defaults={'is_active': False})

    def filter_attachments(self, src, val):
        if not val:
            return []
        return [(subval.strip(), '', '') for subval in val.split(self.separator) if subval.strip()]

    def has_size_changed(self, url, attachment):
        parsed_url = urlparse(url)
        if parsed_url.scheme == 'ftp':
            directory = dirname(parsed_url.path)

            ftp = FTP(parsed_url.hostname)
            ftp.login(user=parsed_url.username, passwd=parsed_url.password)
            ftp.cwd(directory)
            size = ftp.size(parsed_url.path.split('/')[-1:][0])
            return size != attachment.attachment_file.size

        if parsed_url.scheme == 'http' or parsed_url.scheme == 'https':
            try:
                response = self.request_or_retry(url, verb='head')
            except (requests.exceptions.ConnectionError, DownloadImportError) as e:
                raise ValueImportError('Failed to load attachment: {exc}'.format(exc=e))
            size = response.headers.get('content-length')
            try:
                return size is not None and int(size) != attachment.attachment_file.size
            except FileNotFoundError:
                pass

        return True

    def download_attachment(self, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == 'ftp':
            try:
                response = self.request_or_retry(url)
            except (DownloadImportError, requests.exceptions.ConnectionError) as e:
                raise ValueImportError('Failed to load attachment: {exc}'.format(exc=e))
            return response.read()
        else:
            if self.download_attachments:
                try:
                    response = self.request_or_retry(url)
                except (DownloadImportError, requests.exceptions.ConnectionError) as e:
                    raise ValueImportError('Failed to load attachment: {exc}'.format(exc=e))
                if response.status_code != requests.codes.ok:
                    self.add_warning(_("Failed to download '{url}'").format(url=url))
                    return None
                return response.content
            return None

    def check_attachment_updated(self, attachments_to_delete, updated, **kwargs):
        found = False
        for attachment in attachments_to_delete:
            upload_name, ext = os.path.splitext(attachment_upload(attachment, kwargs.get('name')))
            existing_name = attachment.attachment_file.name
            regexp = f"{upload_name}({random_suffix_regexp()})?(_[a-zA-Z0-9]{{7}})?{ext}"
            if re.search(r"^{regexp}$".format(regexp=regexp), existing_name) and not self.has_size_changed(kwargs.get('url'), attachment):
                found = True
                attachments_to_delete.remove(attachment)
                if (
                        kwargs.get('author') != attachment.author
                        or kwargs.get('legend') != attachment.legend
                        or kwargs.get('title') != attachment.title
                ):
                    attachment.author = kwargs.get('author')
                    attachment.legend = textwrap.shorten(kwargs.get('legend'), width=127)
                    attachment.title = textwrap.shorten(kwargs.get('title', ''), width=127)
                    attachment.save(**{'skip_file_save': True})
                    updated = True
                break
        return found, updated

    def generate_content_attachment(self, attachment, parsed_url, url, updated, name):
        if (parsed_url.scheme in ('http', 'https') and self.download_attachments) or parsed_url.scheme == 'ftp':
            content = self.download_attachment(url)
            if content is None:
                return False, updated
            f = ContentFile(content)
            if settings.PAPERCLIP_MAX_BYTES_SIZE_IMAGE and settings.PAPERCLIP_MAX_BYTES_SIZE_IMAGE < f.size:
                self.add_warning(
                    _(f'{self.obj.__class__.__name__} #{self.obj.pk} - {url} : downloaded file is too large'))
                return False, updated
            try:
                image = Image.open(BytesIO(content))
                if settings.PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH and settings.PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH > image.width:
                    self.add_warning(
                        _(f"{self.obj.__class__.__name__} #{self.obj.pk} - {url} : downloaded file is not wide enough"))
                    return False, updated
                if settings.PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT and settings.PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT > image.height:
                    self.add_warning(
                        _(f"{self.obj.__class__.__name__} #{self.obj.pk} - {url} : downloaded file is not tall enough"))
                    return False, updated
                if settings.PAPERCLIP_ALLOWED_EXTENSIONS is not None:
                    extension = PurePath(url).suffix.lower().strip('.')
                    if extension not in settings.PAPERCLIP_ALLOWED_EXTENSIONS:
                        self.add_warning(
                            _(
                                f"Invalid attachment file {url} for {self.obj.__class__.__name__} #{self.obj.pk}: "
                                f"File type '{extension}' is not allowed. "
                            )
                        )
                        return False, updated
                    f.seek(0)
                    file_mimetype = magic.from_buffer(f.read(), mime=True)
                    file_mimetype_allowed = f".{extension}" in mimetypes.guess_all_extensions(file_mimetype)
                    file_mimetype_allowed = file_mimetype_allowed or settings.PAPERCLIP_EXTRA_ALLOWED_MIMETYPES.get(extension, False) and file_mimetype in settings.PAPERCLIP_EXTRA_ALLOWED_MIMETYPES.get(extension)
                    if not file_mimetype_allowed:
                        self.add_warning(
                            _(
                                f"Invalid attachment file {url} for {self.obj.__class__.__name__} #{self.obj.pk}: "
                                f"File mime type '{file_mimetype}' is not allowed for {extension}."
                            )
                        )
                        return False, updated
            except UnidentifiedImageError:
                pass
            attachment.attachment_file.save(name, f, save=False)
            attachment.is_image = attachment.is_an_image()
        else:
            attachment.attachment_link = url
        return True, updated

    def remove_attachments(self, attachments_to_delete):
        if self.delete_attachments:
            for att in attachments_to_delete:
                att.delete()

    def generate_attachment(self, **kwargs):
        attachment = Attachment()
        attachment.content_object = self.obj
        attachment.filetype = self.filetype
        attachment.creator = self.creator
        attachment.author = kwargs.get('author')
        attachment.legend = textwrap.shorten(kwargs.get('legend'), width=127)
        attachment.title = textwrap.shorten(kwargs.get('title'), width=127)
        return attachment

    def generate_attachments(self, src, val, attachments_to_delete, updated):
        attachments = []
        for attachment_data in self.filter_attachments(src, val):
            url = self.base_url + attachment_data[0]
            legend = attachment_data[1] or ""
            author = attachment_data[2] or ""
            title = attachment_data[3] if len(attachment_data) > 3 else ""
            basename, ext = os.path.splitext(os.path.basename(url))
            name = '%s%s' % (basename[:128], ext)
            found, updated = self.check_attachment_updated(attachments_to_delete, updated, name=name, url=url,
                                                           legend=legend, author=author, title=title)
            if found:
                continue

            parsed_url = urlparse(url)
            attachment = self.generate_attachment(author=author, legend=legend, title=title)
            save, updated = self.generate_content_attachment(attachment, parsed_url, url, updated, name)
            if not save:
                continue
            attachments.append(attachment)
            updated = True
        return updated, attachments

    def save_attachments(self, src, val):
        updated = False
        attachments_to_delete = list(Attachment.objects.attachments_for_object(self.obj))
        updated, attachments = self.generate_attachments(src, val, attachments_to_delete, updated)
        Attachment.objects.bulk_create(attachments)
        # TODO : attachments from parsers should be resized
        #  See https://github.com/makinacorpus/django-paperclip/blob/master/paperclip/models.py#L124
        # `bulk_create` does not call this `save` method
        self.remove_attachments(attachments_to_delete)
        return updated


class TourInSoftParser(AttachmentParserMixin, Parser):
    version_tourinsoft = 2
    separator = '#'
    separator2 = '|'

    @property
    def items(self):
        if self.version_tourinsoft == 3:
            return self.root['value']
        return self.root['d']['results']

    def get_nb(self):
        if self.version_tourinsoft == 3:
            return int(self.root['odata.count'])
        return int(self.root['d']['__count'])

    def next_row(self):
        skip = 0
        while True:
            params = {
                '$format': 'json',
                '$inlinecount': 'allpages',
                '$top': 1000,
                '$skip': skip,
            }
            response = self.request_or_retry(self.url, params=params)
            self.root = response.json()
            self.nb = self.get_nb()
            for row in self.items:
                yield {self.normalize_field_name(src): val for src, val in row.items()}
            skip += 1000
            if skip >= self.nb:
                return

    def filter_attachments(self, src, val):
        if not val:
            return []
        return [
            subval.split(self.separator2)
            for subval in val.split(self.separator)
            if subval.split(self.separator2)[0]
        ]

    def filter_geom(self, src, val):
        lng, lat = val
        if not lng or not lat:
            raise ValueImportError("Empty geometry")
        geom = Point(float(lng), float(lat), srid=4326)  # WGS84
        geom.transform(settings.SRID)
        return geom

    def filter_email(self, src, val):
        val = val or ""

        for subval in val.split(self.separator):
            if not subval:
                continue
            try:
                key, value = subval.split(self.separator2)
            except ValueError as e:
                raise ValueImportError("Fail to split <MoyenDeCom>: {}".format(e))
            if key in ("Mél", "Mail"):
                return value

        return ""

    def filter_website(self, src, val):
        val = val or ""

        for subval in val.split(self.separator):
            if not subval:
                continue
            try:
                key, value = subval.split(self.separator2)
            except ValueError as e:
                raise ValueImportError("Fail to split <MoyenDeCom>: {}".format(e))
            if key in ("Site web", "Site web (URL)"):
                return value

        return ""

    def filter_contact(self, src, val):
        com, adresse = val
        infos = []

        if adresse:
            # Some address have 6 items, some others 7 items :(
            lines = adresse.split(self.separator2)
            # Remove last field (code INSEE)
            lines = lines[:-1]
            # Put city and postal code together
            if lines[-2] and lines[-1]:
                lines[-2:] = [" ".join(lines[-2:])]
            # Remove empty lines
            lines = [line for line in lines if line]
            infos.append(
                "<strong>Adresse :</strong><br>"
                + "<br>".join(lines)
            )

        if com:
            for subval in com.split(self.separator):
                if not subval:
                    continue
                try:
                    key, value = subval.split(self.separator2)
                except ValueError as e:
                    raise ValueImportError("Fail to split <MoyenDeCom>: {}".format(e))
                if key in ("Mél", "Mail", "Site web", "Site web (URL)"):
                    continue
                infos.append("<strong>{} :</strong><br>{}".format(key, value))

        return "<br><br>".join(infos)


class TourismSystemParser(AttachmentParserMixin, Parser):
    @property
    def items(self):
        return self.root['data']

    def next_row(self):
        size = 1000
        skip = 0
        while True:
            params = {
                'size': size,
                'start': skip,
            }
            response = self.request_or_retry(self.url, params=params, authent=HTTPBasicAuth(self.login, self.password))
            self.root = response.json()
            self.nb = int(self.root['metadata']['total'])
            for row in self.items:
                yield {self.normalize_field_name(src): val for src, val in row.items()}
            skip += size
            if skip >= self.nb:
                return

    def filter_attachments(self, src, val):
        result = []
        for subval in val or []:
            try:
                name = subval['name']['fr']
            except KeyError:
                name = None
            result.append((subval['URL'], name, None))
        return result

    def normalize_field_name(self, name):
        return name


class OpenSystemParser(Parser):
    url = 'http://proxy-xml.open-system.fr/rest.aspx'

    def next_row(self):
        params = {
            'Login': self.login,
            'Pass': self.password,
            'Action': 'concentrateur_liaisons',
        }
        response = self.request_or_retry(self.url, params=params)
        self.root = ET.fromstring(response.content).find('Resultat').find('Objets')
        self.nb = len(self.root)
        for row in self.root:
            id_apidae = row.find('ObjetCle').find('Cle').text
            for liaison in row.find('Liaisons'):
                yield {
                    'id_apidae': id_apidae,
                    'id_opensystem': liaison.find('ObjetOS').find('CodeUI').text,
                }

    def normalize_field_name(self, name):
        return name


class LEIParser(AttachmentParserMixin, XmlParser):
    """
    Parser for LEI tourism SIT

    You can define :

    fields = {
        'eid': 'PRODUIT',
        'name': 'NOM',
        'description': 'COMMENTAIRE',
        'contact': (
            'ADRPROD_NUM_VOIE', 'ADRPROD_LIB_VOIE', 'ADRPROD_CP', 'ADRPROD_LIBELLE_COMMUNE',
            'ADRPROD_TEL', 'ADRPROD_TEL2', 'ADRPREST_TEL', 'ADRPREST_TEL2'
        ),
        'email': ('ADRPROD_EMAIL'),
        'website': ('ADRPROD_URL', 'ADRPREST_URL'),
        'geom': ('LATITUDE', 'LONGITUDE'),
    }

    non_fields = {     # URL                                         # Legend
        'attachments': [('CRITERES/Crit[@CLEF_CRITERE="30000279"]', 'CRITERES/Crit[@CLEF_CRITERE="900003"]'),
                        ('CRITERES/Crit[@CLEF_CRITERE="30000280"]', 'CRITERES/Crit[@CLEF_CRITERE="900004"]')],
    }
    """
    results_path = 'Resultat/sit_liste'
    eid = 'eid'

    def get_part(self, dst, src, val):
        """For generic CRITERES return XML Crit element"""
        if 'CRITERES/Crit' in src:
            # Return list of Crit elements
            return val.findall(src)
        return val.findtext(src, None, self.ns)

    def get_crit_kv(self, crit):
        """Get Crit key / value according to Nomenclature"""
        crit_name = self.root.findtext(
            f'NOMENCLATURE/CRIT[@CLEF="{crit.attrib["CLEF_CRITERE"]}"]/NOMCRIT'
        )
        crit_value = self.get_crit_value(crit)
        # If value is available for crit, add it to result
        if crit.text is not None and crit_value != 'Photos':
            crit_value = "{0} : {1}".format(crit_value, crit.text)
        return crit_name, crit_value

    def get_crit_value(self, crit):
        """Get Crit value only, according to Nomenclature"""
        return self.root.findtext(
            f'NOMENCLATURE/CRIT[@CLEF="{crit.attrib["CLEF_CRITERE"]}"]/MODAL[@CLEF="{crit.attrib["CLEF_MODA"]}"]'
        )

    def start(self):
        super().start()
        lei = set(self.model.objects.filter(eid__startswith='LEI').values_list('pk', flat=True))
        self.to_delete = self.to_delete & lei

    def filter_eid(self, src, val):
        return 'LEI' + val

    def filter_attachments(self, src, val):
        """Get Photos url and legend from Crit element list

        Keyword arguments:
        src --
        val -- Crit element list

        returns photos list of tuples (url, legend, '')
        """
        photos = []
        for crits in val:
            url_crits = crits[0]
            legend_crits = crits[1]
            if legend_crits:
                legend_crit = legend_crits[0]
                legend = legend_crit.text
                if legend:
                    legend = legend[:128]
            else:
                legend = ""
            for crit in url_crits:
                url = crit.text
                if not url:
                    continue
                url = url.replace('https://', 'http://')
                if url[:7] != 'http://':
                    url = 'http://' + url
                photos.append((url, legend, ''))
        return photos

    def filter_description(self, src, val):
        if val is None:
            return ""
        val = val.replace('\n', '<br>')
        return val

    def filter_geom(self, src, val):
        lat, lng = val
        if lat is None or lng is None:
            raise ValueImportError("Empty geometry")
        lat = lat.replace(',', '.')
        lng = lng.replace(',', '.')
        try:
            geom = Point(float(lng), float(lat), srid=4326)  # WGS84
        except ValueError:
            raise ValueImportError("Empty geometry")

        try:
            geom.transform(settings.SRID)
        except (GDALException, InternalError) as e:
            raise ValueImportError(e)
        return geom

    def filter_website(self, src, val):
        (val1, val2) = val

        if val1:
            return add_http_prefix(val1)
        if val2:
            return add_http_prefix(val2)


class GeotrekAggregatorParser:
    filename = None
    url = None

    mapping_model_parser = {
        "Trek": ("geotrek.trekking.parsers", "GeotrekTrekParser"),
        "POI": ("geotrek.trekking.parsers", "GeotrekPOIParser"),
        "Service": ("geotrek.trekking.parsers", "GeotrekServiceParser"),
        "InformationDesk": ("geotrek.tourism.parsers", "GeotrekInformationDeskParser"),
        "TouristicContent": ("geotrek.tourism.parsers", "GeotrekTouristicContentParser"),
        "TouristicEvent": ("geotrek.tourism.parsers", "GeotrekTouristicEventParser"),
        "Signage": ("geotrek.signage.parsers", "GeotrekSignageParser"),
        "Infrastructure": ("geotrek.infrastructure.parsers", "GeotrekInfrastructureParser"),
    }

    invalid_model_topology = ['Trek', 'POI', 'Service', 'Signage', 'Infrastructure']

    def __init__(self, progress_cb=None, user=None, encoding='utf8'):
        self.progress_cb = progress_cb
        self.user = user
        self.encoding = encoding
        self.line = 0
        self.nb_success = 0
        self.nb_created = 0
        self.nb_updated = 0
        self.nb_unmodified = 0
        self.progress_cb = progress_cb
        self.warnings = {}
        self.report_by_api_v2_by_type = {}

    def add_warning(self, key, msg):
        warnings = self.warnings.setdefault(key, [])
        warnings.append(msg)

    def run_method_parser(self, key_name, parsers, method_name):
        for parser in parsers:
            self.progress_cb(0, 0, f'{str(parser.model._meta.model_name).capitalize()} ({key_name})')
            getattr(parser, method_name)()
            self.progress_cb(1, 0, f'{str(parser.model._meta.model_name).capitalize()} ({key_name})')
            self.report_by_api_v2_by_type[key_name][str(parser.model._meta.model_name).capitalize()] = {
                'nb_lines': parser.line,
                'nb_success': parser.nb_success,
                'nb_created': parser.nb_created,
                'nb_updated': parser.nb_updated,
                'nb_deleted': len(parser.to_delete),
                'nb_unmodified': parser.nb_unmodified,
                'warnings': parser.warnings
            }

    def parse(self, filename=None, limit=None):
        filename = filename if filename else self.filename
        if not os.path.exists(filename):
            raise GlobalImportError(_(f"File does not exists at: {filename}"))
        with open(filename, mode='r') as f:
            json_aggregator = json.load(f)

        for key, datas in json_aggregator.items():
            self.report_by_api_v2_by_type[key] = {}
            models_to_import = datas.get('data_to_import')
            if not models_to_import:
                models_to_import = self.mapping_model_parser.keys()
            parsers_to_parse = []
            for model in models_to_import:
                if settings.TREKKING_TOPOLOGY_ENABLED:
                    if model in self.invalid_model_topology:
                        warning = f"{model}s can't be imported with dynamic segmentation"
                        logger.warning(warning)
                        key_warning = _(f"Model {model}")
                        self.add_warning(key_warning, warning)
                        self.report_by_api_v2_by_type[key][model] = {
                            'nb_lines': 0,
                            'nb_success': 0,
                            'nb_created': 0,
                            'nb_updated': 0,
                            'nb_deleted': None,
                            'nb_unmodified': 0,
                            'warnings': self.warnings
                        }
                        continue
                module_name, class_name = self.mapping_model_parser[model]
                module = importlib.import_module(module_name)
                parser = getattr(module, class_name)
                if 'url' not in datas:
                    warning = f"{key} has no url"
                    key_warning = _("Geotrek-admin")
                    self.add_warning(key_warning, warning)
                    self.report_by_api_v2_by_type[key][str(parser.model._meta.model_name).capitalize()] = {
                        'nb_lines': 0,
                        'nb_success': 0,
                        'nb_created': 0,
                        'nb_updated': 0,
                        'nb_deleted': None,
                        'nb_unmodified': 0,
                        'warnings': self.warnings
                    }
                else:
                    Parser = parser(progress_cb=self.progress_cb, provider=key, url=datas['url'],
                                    portals_filter=datas.get('portals'), mapping=datas.get('mapping'),
                                    create_categories=datas.get('create'), all_datas=datas.get('all_datas'))
                    parsers_to_parse.append(Parser)

            self.run_method_parser(key, parsers_to_parse, 'start_meta')
            self.run_method_parser(key, parsers_to_parse, 'parse')
            self.run_method_parser(key, parsers_to_parse, 'end_meta')

    def report(self, output_format='txt'):
        context = {'report': self.report_by_api_v2_by_type}
        return render_to_string('common/parser_report_aggregator.{output_format}'.format(output_format=output_format), context)


class GeotrekParser(AttachmentParserMixin, Parser):
    """
    url_categories: url of the categories in api v2 (example: 'category': '/api/v2/touristiccontent_category/')
    replace_fields: Replace fields which have not the same name in the api v2 compare to models (geom => geometry in api v2)
    m2m_replace_fields: Replace m2m fields which have not the same name in the api v2 compare to models (geom => geometry in api v2)
    categories_keys_api_v2: Key in the route of the category (example: /api/v2/touristiccontent_category/) corresponding to the model field
    provider: Allow to differentiate multiple GeotrekParser for the same model
    portals_filter: Portals which will be use for filter in api v2 (default: No portal filter)
    mapping: Mapping between values in categories (example: /api/v2/touristiccontent_category/) and final values
        Can be use when you want to change a value from the api/v2
    create_categories: Create all categories during importation
    all_datas: Import all datas and do not use updated_after filter
    """
    model = None
    next_url = ''
    url = None
    separator = None
    delete = True
    eid = 'eid'
    constant_fields = {}
    url_categories = {}
    replace_fields = {}
    m2m_replace_fields = {}
    categories_keys_api_v2 = {}
    params_used = {}
    non_fields = {
        'attachments': "attachments",
    }
    field_options = {
        'geom': {'required': True},
    }
    bbox = None
    portals_filter = None
    mapping = {}
    create_categories = False
    all_datas = False
    provider = None

    def __init__(self, all_datas=None, create_categories=None, provider=None, mapping=None, portals_filter=None, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bbox = Polygon.from_bbox(settings.SPATIAL_EXTENT)
        self.bbox.srid = settings.SRID
        self.bbox.transform(4326)  # WGS84
        self.portals_filter = portals_filter
        self.url = url if url else self.url
        self.mapping = mapping if mapping else self.mapping
        self.provider = provider if provider else self.provider
        self.all_datas = all_datas if all_datas else self.all_datas
        self.create_categories = create_categories if create_categories else self.create_categories
        self.fields = dict((f.name, f.name) for f in self.model._meta.fields if not isinstance(f, TranslationField) and f.name not in ['id', 'provider'])
        self.m2m_fields = {
            f.name: f.name
            for f in self.model._meta.many_to_many
        }
        # Replace automatics fields and m2m_fields generated above
        for key, value in self.replace_fields.items():
            self.fields[key] = value

        for key, value in self.m2m_replace_fields.items():
            self.m2m_fields[key] = value
        self.translated_fields = [field for field in get_translated_fields(self.model)]
        # Generate a mapping dictionnary between id and the related label
        for category, route in self.url_categories.items():
            if self.categories_keys_api_v2.get(category):
                response = self.request_or_retry(f"{self.url}/api/v2/{route}")
                self.field_options.setdefault(category, {})
                self.field_options[category]["mapping"] = {}
                if self.create_categories:
                    self.field_options[category]["create"] = True
                results = response.json().get('results', [])
                # for element in category url map the id with its label
                for result in results:
                    id_result = result['id']
                    label = result[self.categories_keys_api_v2[category]]
                    if isinstance(result[self.categories_keys_api_v2[category]], dict):
                        if label[settings.MODELTRANSLATION_DEFAULT_LANGUAGE]:
                            self.field_options[category]["mapping"][id_result] = self.replace_mapping(label[settings.MODELTRANSLATION_DEFAULT_LANGUAGE], route)
                    else:
                        if label:
                            self.field_options[category]["mapping"][id_result] = self.replace_mapping(label, category)
            else:
                raise ImproperlyConfigured(f"{category} is not configured in categories_keys_api_v2")
        self.creator, created = get_user_model().objects.get_or_create(username='import', defaults={'is_active': False})

    def replace_mapping(self, label, route):
        for key, list_map in self.mapping.get(route, {}).items():
            if label in list_map:
                return key
        return label

    def generate_attachments(self, src, val, attachments_to_delete, updated):
        attachments = []
        for url, legend, author, license in self.filter_attachments(src, val):
            url = self.base_url + url
            legend = legend or ""
            author = author or ""
            license = License.objects.get_or_create(label=license)[0] if license else None
            basename, ext = os.path.splitext(os.path.basename(url))
            name = '%s%s' % (basename[:128], ext)
            found, updated = self.check_attachment_updated(attachments_to_delete, updated, name=name, url=url,
                                                           legend=legend, author=author)
            if found:
                continue

            parsed_url = urlparse(url)
            attachment = self.generate_attachment(author=author, legend=legend, license=license)
            save, updated = self.generate_content_attachment(attachment, parsed_url, url, updated, name)
            if not save:
                continue
            attachments.append(attachment)
            updated = True
        return updated, attachments

    def generate_attachment(self, **kwargs):
        attachment = Attachment()
        attachment.content_object = self.obj
        attachment.filetype = self.filetype
        attachment.creator = self.creator
        attachment.author = kwargs.get('author')
        attachment.legend = textwrap.shorten(kwargs.get('legend'), width=127)
        attachment.license = kwargs.get('license')
        return attachment

    def start(self):
        super().start()
        kwargs = self.get_to_delete_kwargs()
        json_id_key = self.replace_fields.get('eid', 'id')
        params = {
            'fields': json_id_key,
            'page_size': 10000
        }
        response = self.request_or_retry(self.next_url, params=params)
        ids = [f"{element[json_id_key]}" for element in response.json().get('results', [])]
        self.to_delete = set(self.model.objects.filter(**kwargs).exclude(eid__in=ids).values_list('pk', flat=True))

    def filter_attachments(self, src, val):
        return [(subval.get('url'), subval.get('legend'), subval.get('author'), subval.get('license')) for subval in val]

    def start_meta(self):
        self.to_delete = set()

    def end_meta(self):
        pass

    def apply_filter(self, dst, src, val):
        val = super().apply_filter(dst, src, val)
        val_default_lang = val
        if dst in self.translated_fields:
            if isinstance(val, dict):
                val_default_lang = val.get(translation.get_language())
                for language in settings.MODELTRANSLATION_LANGUAGES:
                    if language not in val.keys():
                        key = language
                        if not self.obj._meta.get_field(dst).default == NOT_PROVIDED:
                            self.set_value(f'{dst}_{key}', src, self.obj._meta.get_field(dst).default)
                        else:
                            self.set_value(f'{dst}_{key}', src, val_default_lang)
                for key, final_value in val.items():
                    if key in settings.MODELTRANSLATION_LANGUAGES:
                        self.set_value(f'{dst}_{key}', src, final_value)
        return val_default_lang

    def normalize_field_name(self, name):
        return name

    @property
    def items(self):
        return self.root['results']

    def filter_geom(self, src, val):
        geom = GEOSGeometry(json.dumps(val))
        geom.transform(settings.SRID)
        geom = WKBWriter().write(geom)
        geom = GEOSGeometry(geom)
        return geom

    def next_row(self):
        """Returns next row.
        Geotrek API is paginated, run until "next" is empty
        :returns row
        """
        portals = self.portals_filter
        updated_after = None

        available_fields = [field.name for field in self.model._meta.get_fields()]
        if not self.all_datas and self.model.objects.filter(provider__exact=self.provider).exists() and 'date_update' in available_fields:
            updated_after = self.model.objects.filter(provider__exact=self.provider).latest('date_update').date_update.strftime('%Y-%m-%d')
        params = {
            'in_bbox': ','.join([str(coord) for coord in self.bbox.extent]),
            'portals': ','.join(portals) if portals else '',
            'updated_after': updated_after
        }
        self.params_used = params
        response = self.request_or_retry(self.next_url, params=params)
        self.root = response.json()
        self.nb = int(self.root['count'])

        for row in self.items:
            yield row
        self.next_url = self.root['next']

        while self.next_url:
            response = self.request_or_retry(self.next_url)
            self.root = response.json()
            self.nb = int(self.root['count'])

            for row in self.items:
                yield row

            self.next_url = self.root['next']


class ApidaeBaseParser(Parser):
    """Parser to import "anything" from APIDAE"""
    separator = None
    api_key = None
    project_id = None
    selection_id = None
    url = 'http://api.apidae-tourisme.com/api/v002/recherche/list-objets-touristiques/'
    size = 100
    skip = 0

    # A list of locales to be fetched (i.e. ['fr', 'en']). Leave empty to fetch default locales.
    locales = None

    @property
    def items(self):
        if self.nb == 0:
            return []
        return self.root['objetsTouristiques']

    def next_row(self):
        while True:
            params = {
                'apiKey': self.api_key,
                'projetId': self.project_id,
                'selectionIds': [self.selection_id],
                'count': self.size,
                'first': self.skip,
                'responseFields': self.responseFields
            }
            if self.locales:
                params['locales'] = self.locales
            response = self.request_or_retry(self.url, params={'query': json.dumps(params)})
            self.root = response.json()
            self.nb = int(self.root['numFound'])
            for row in self.items:
                yield row
            self.skip += self.size
            if self.skip >= self.nb:
                return

    def normalize_field_name(self, name):
        return name
