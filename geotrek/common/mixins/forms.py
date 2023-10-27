import logging
from copy import deepcopy

from django import forms
from django.conf import settings
from django.core.checks import Error
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.db.models import ForeignKey, ManyToManyField, Q, QuerySet
from django.forms import HiddenInput
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from mapentity.forms import MapEntityForm

from geotrek.authent.models import StructureRelated, StructureOrNoneRelated, default_structure
from geotrek.common.mixins.models import NoDeleteMixin, PublishableMixin
from geotrek.common.utils.translation import get_translated_fields

logger = logging.getLogger(__name__)


class FormsetMixin:
    context_name = None
    formset_class = None

    def form_valid(self, form):
        context = self.get_context_data()
        formset_form = context[self.context_name]

        if formset_form.is_valid():
            response = super().form_valid(form)
            formset_form.instance = self.object
            formset_form.save()
        else:
            response = self.form_invalid(form)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            try:
                context[self.context_name] = self.formset_class(
                    self.request.POST, instance=self.object)
            except ValidationError:
                pass
        else:
            context[self.context_name] = self.formset_class(
                instance=self.object)
        return context


class CommonForm(MapEntityForm):
    not_hideable_fields = []

    class Meta:
        fields = []

    MAP_SETTINGS = {
        'PathForm': 'path',
        'TrekForm': 'trek',
        'TrailForm': 'trail',
        'LandEdgeForm': 'landedge',
        'PhysicalEdgeForm': 'physicaledge',
        'CompetenceEdgeForm': 'competenceedge',
        'WorkManagementEdgeForm': 'workmanagement',
        'SignageManagementEdgeForm': 'signagemanagementedge',
        'InfrastructureForm': 'infrastructure',
        'InterventionForm': 'intervention',
        'SignageForm': 'signage',
        'ProjectForm': 'project',
        'SiteForm': 'site',
        'CourseForm': 'course',
        'TouristicContentForm': 'touristic_content',
        'TouristicEventForm': 'touristic_event',
        'POIForm': 'poi',
        'ServiceForm': 'service',
        'DiveForm': 'dive',
        'SensitiveAreaForm': 'sensitivity_species',
        'RegulatorySensitiveAreaForm': 'sensitivity_regulatory',
        'BladeForm': 'blade',
        'ReportForm': 'report',
    }

    def deep_remove(self, fieldslayout, name):
        if isinstance(fieldslayout, list):
            for field in fieldslayout:
                self.deep_remove(field, name)
        elif hasattr(fieldslayout, 'fields'):
            if name in fieldslayout.fields:
                fieldslayout.fields.remove(name)
                self.fields.pop(name)
            for field in fieldslayout.fields:
                self.deep_remove(field, name)

    def replace_orig_fields(self):
        model = self._meta.model
        codeperm = '%s.publish_%s' % (
            model._meta.app_label, model._meta.model_name)
        if 'published' in self.fields and self.user and not self.user.has_perm(codeperm):
            self.deep_remove(self.fieldslayout, 'published')
        if 'review' in self.fields and self.instance and self.instance.any_published:
            self.deep_remove(self.fieldslayout, 'review')
        super().replace_orig_fields()

    def filter_related_field(self, name, field):
        if not isinstance(field, forms.models.ModelChoiceField):
            return
        try:
            modelfield = self.instance._meta.get_field(name)
        except FieldDoesNotExist:
            # be careful but custom form fields, not in model
            modelfield = None
        if not isinstance(modelfield, (ForeignKey, ManyToManyField)):
            return
        model = modelfield.remote_field.model
        # Filter structured choice fields according to user's structure
        if issubclass(model, StructureRelated) and model.check_structure_in_forms:
            field.queryset = field.queryset.filter(structure=self.user.profile.structure)
        if issubclass(model, StructureOrNoneRelated) and model.check_structure_in_forms:
            field.queryset = field.queryset.filter(Q(structure=self.user.profile.structure) | Q(structure=None))
        if issubclass(model, NoDeleteMixin):
            field.queryset = field.queryset.filter(deleted=False)

    def __init__(self, *args, **kwargs):

        # Get settings key for this Form
        settings_key = self.MAP_SETTINGS.get(self.__class__.__name__, None)
        if settings_key is None:
            logger.warning("No value set in MAP_SETTINGS dictonary for form class " + self.__class__.__name__)
        self.hidden_fields = settings.HIDDEN_FORM_FIELDS.get(settings_key, [])

        self.fieldslayout = deepcopy(self.fieldslayout)
        super().__init__(*args, **kwargs)
        self.fields = self.fields.copy()
        self.update = kwargs.get("instance") is not None
        if 'structure' in self.fields:
            if self.user.has_perm('authent.can_bypass_structure'):
                if not self.instance.pk:
                    self.fields['structure'].initial = self.user.profile.structure
            else:
                for name, field in self.fields.items():
                    self.filter_related_field(name, field)
                del self.fields['structure']

        # For each field listed in 'to hide' list for this Form
        for field_to_hide in self.hidden_fields:
            # Ignore if field was translated (handled in TranslatedModelForm)
            if field_to_hide not in self._translated:
                # Hide only if optional
                if self.fields[field_to_hide].required:
                    logger.warning(
                        f"Ignoring entry in HIDDEN_FORM_FIELDS: field '{field_to_hide}' is required on form {self.__class__.__name__}."
                    )
                elif field_to_hide in self.not_hideable_fields:
                    logger.warning(
                        f"Ignoring entry in HIDDEN_FORM_FIELDS: field '{field_to_hide}' cannot be hidden on form {self.__class__.__name__}."
                    )
                else:
                    self.fields[field_to_hide].widget = HiddenInput()

    def clean(self):
        """Check field data with structure and completeness fields if relevant"""
        structure = self.cleaned_data.get('structure')

        # if structure in form, check each field same structure
        if structure:
            # Copy cleaned_data because self.add_error may remove an item
            for name, field in self.cleaned_data.copy().items():
                try:
                    modelfield = self.instance._meta.get_field(name)
                except FieldDoesNotExist:
                    continue
                if not isinstance(modelfield, (ForeignKey, ManyToManyField)):
                    continue
                model = modelfield.remote_field.model
                if not issubclass(model, (StructureRelated, StructureOrNoneRelated)):
                    continue
                if not model.check_structure_in_forms:
                    continue
                if isinstance(field, QuerySet):
                    for value in field:
                        self.check_structure(value, structure, name)
                else:
                    self.check_structure(field, structure, name)

        # If model is publishable or reviewable,
        # check if completeness fields are required, and raise error if some fields are missing
        if self.completeness_fields_are_required():
            missing_fields = []
            completeness_fields = settings.COMPLETENESS_FIELDS.get(self._meta.model._meta.model_name, [])
            if settings.COMPLETENESS_LEVEL == 'error_on_publication':
                missing_fields = self._get_missing_completeness_fields(completeness_fields,
                                                                       _('This field is required to publish object.'))
            elif settings.COMPLETENESS_LEVEL == 'error_on_review':
                missing_fields = self._get_missing_completeness_fields(completeness_fields,
                                                                       _('This field is required to review object.'))

            if missing_fields:
                raise ValidationError(
                    _('Fields are missing to publish or review object: %(fields)s'),
                    params={
                        'fields': ', '.join(missing_fields)
                    },
                )

        return self.cleaned_data

    def check_structure(self, obj, structure, name):
        if hasattr(obj, 'structure'):
            if obj.structure and structure != obj.structure:
                self.add_error(name, format_lazy(_("Please select a choice related to all structures (without brackets) "
                                                   "or related to the structure {struc} (in brackets)"), struc=structure))

    @property
    def any_published(self):
        """Check if form has published in at least one of the language"""
        return any([self.cleaned_data.get(f'published_{language[0]}', False)
                    for language in settings.MAPENTITY_CONFIG['TRANSLATED_LANGUAGES']])

    @property
    def published_languages(self):
        """Returns languages in which the form has published data.
        """
        languages = [language[0] for language in settings.MAPENTITY_CONFIG['TRANSLATED_LANGUAGES']]
        if settings.PUBLISHED_BY_LANG:
            return [language for language in languages if self.cleaned_data.get(f'published_{language}', None)]
        else:
            if self.any_published:
                return languages

    def completeness_fields_are_required(self):
        """Return True if the completeness fields are required"""
        if not issubclass(self._meta.model, PublishableMixin):
            return False

        if not self.instance.is_complete():
            if settings.COMPLETENESS_LEVEL == 'error_on_publication':
                if self.any_published:
                    return True
            elif settings.COMPLETENESS_LEVEL == 'error_on_review':
                # Error on review implies error on publication
                if self.cleaned_data['review'] or self.any_published:
                    return True

        return False

    def _get_missing_completeness_fields(self, completeness_fields, msg):
        """Check fields completeness and add error message if field is empty"""

        missing_fields = []
        translated_fields = get_translated_fields(self._meta.model)

        # Add error on each field if it is empty
        for field_required in completeness_fields:
            if field_required in translated_fields:
                if self.cleaned_data.get('review') and settings.COMPLETENESS_LEVEL == 'error_on_review':
                    # get field for first language only
                    field_required_lang = f"{field_required}_{settings.MAPENTITY_CONFIG['TRANSLATED_LANGUAGES'][0][0]}"
                    missing_fields.append(field_required_lang)
                    self.add_error(field_required_lang, msg)
                else:
                    for language in self.published_languages:
                        field_required_lang = f'{field_required}_{language}'
                        if not self.cleaned_data.get(field_required_lang):
                            missing_fields.append(field_required_lang)
                            self.add_error(field_required_lang, msg)
            else:
                if not self.cleaned_data.get(field_required):
                    missing_fields.append(field_required)
                    self.add_error(field_required, msg)
        return missing_fields

    def save(self, commit=True):
        """Set structure field before saving if need be"""
        if self.update:  # Structure is already set on object.
            pass
        elif not hasattr(self.instance, 'structure'):
            pass
        elif 'structure' in self.fields:
            pass  # The form contains the structure field. Let django use its value.
        elif self.user:
            self.instance.structure = self.user.profile.structure
        else:
            self.instance.structure = default_structure()
        return super().save(commit)

    @classmethod
    def check_fields_to_hide(cls):
        errors = []
        for field_to_hide in settings.HIDDEN_FORM_FIELDS.get(cls.MAP_SETTINGS[cls.__name__], []):
            if field_to_hide not in cls._meta.fields:
                errors.append(
                    Error(
                        f"Cannot hide field '{field_to_hide}'",
                        hint="Field not included in form",
                        # Diplay dotted path only
                        obj=str(cls).split(" ")[1].strip(">").strip("'"),
                    )
                )
        return errors
