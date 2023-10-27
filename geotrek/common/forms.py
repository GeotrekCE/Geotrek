import logging

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Layout, Submit
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.images import get_image_dimensions
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mapentity.forms import MapEntityForm, SubmitButton

from geotrek.common.models import AccessibilityAttachment, HDViewPoint

logger = logging.getLogger(__name__)


class ImportDatasetForm(forms.Form):
    parser = forms.TypedChoiceField(
        label=_('Data to import from network'),
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parser'].choices = choices

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    'parser',
                ),
                FormActions(
                    Submit('import-web', _("Import"), css_class='button white')
                ),
                css_class='file-attachment-form',
            )
        )


class ImportSuricateForm(forms.Form):
    parser = forms.TypedChoiceField(
        label=_('Data to import from Suricate'),
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parser'].choices = choices

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    'parser',
                ),
                FormActions(
                    Submit('import-suricate', _("Import"), css_class='button white')
                ),
                css_class='file-attachment-form',
            )
        )


class ImportDatasetFormWithFile(ImportDatasetForm):
    file = forms.FileField(
        label=_('File'),
        required=True,
        widget=forms.FileInput
    )
    encoding = forms.ChoiceField(
        label=_('Encoding'),
        choices=(('Windows-1252', 'Windows-1252'), ('UTF-8', 'UTF-8'))
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['parser'].label = _('Data to import from local file')
        self.helper.layout = Layout(
            Div(
                Div(
                    'parser',
                    'file',
                    'encoding',
                ),
                FormActions(
                    Submit('upload-file', _("Import"), css_class='button white')
                ),
                css_class='file-attachment-form',
            )
        )


class SyncRandoForm(forms.Form):
    """
    Sync Rando View Form
    """

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_id = 'form-sync'
        helper.form_action = reverse('common:sync_randos')
        helper.form_class = 'search'
        # submit button with boostrap attributes, disabled by default
        helper.add_input(Button('sync-web', _("Launch Sync"),
                                css_class="btn-primary",
                                **{'data-toggle': "modal",
                                   'data-target': "#confirm-submit",
                                   'disabled': 'disabled'}))

        return helper


class AttachmentAccessibilityForm(forms.ModelForm):
    next = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        self._object = kwargs.pop('object', None)

        super().__init__(*args, **kwargs)
        self.fields['legend'].widget.attrs['placeholder'] = _('Overview of the tricky passage')

        self.redirect_on_error = True
        # Detect fields errors without uploading (using HTML5)
        self.fields['author'].widget.attrs['pattern'] = r'^\S.*'
        self.fields['legend'].widget.attrs['pattern'] = r'^\S.*'
        self.fields['attachment_accessibility_file'].required = True
        self.fields['attachment_accessibility_file'].widget = forms.FileInput()

        self.helper = FormHelper(form=self)
        self.helper.form_tag = True
        self.helper.form_class = 'attachments-accessibility form-horizontal'
        self.helper.help_text_inline = True
        self.helper.form_style = "default"
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.fields['next'].initial = f"{self._object.get_detail_url()}?tab=attachments-accessibility"

        if not self.instance.pk:
            form_actions = [
                Submit('submit_attachment',
                       _('Submit attachment'),
                       css_class="btn-primary")
            ]
            self.form_url = reverse('common:add_attachment_accessibility', kwargs={
                'app_label': self._object._meta.app_label,
                'model_name': self._object._meta.model_name,
                'pk': self._object.pk
            })
        else:
            form_actions = [
                Button('cancel', _('Cancel'), css_class=""),
                Submit('submit_attachment',
                       _('Update attachment'),
                       css_class="btn-primary")
            ]
            self.fields['title'].widget.attrs['readonly'] = True
            self.form_url = reverse('common:update_attachment_accessibility', kwargs={
                'attachment_pk': self.instance.pk
            })

        self.helper.form_action = self.form_url
        self.helper.layout.fields.append(
            FormActions(*form_actions, css_class="form-actions"))

    class Meta:
        model = AccessibilityAttachment
        fields = ('attachment_accessibility_file', 'info_accessibility', 'author', 'title', 'legend')

    def success_url(self):
        obj = self._object
        return f"{obj.get_detail_url()}?tab=attachments-accessibility"

    def clean_attachment_accessibility_file(self):
        uploaded_image = self.cleaned_data.get("attachment_accessibility_file", False)
        if self.instance.pk:
            try:
                uploaded_image.file.readline()
            except FileNotFoundError:
                return uploaded_image
        if settings.PAPERCLIP_MAX_BYTES_SIZE_IMAGE and settings.PAPERCLIP_MAX_BYTES_SIZE_IMAGE < uploaded_image.size:
            raise forms.ValidationError(_('The uploaded file is too large'))
        width, height = get_image_dimensions(uploaded_image)
        if settings.PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH and settings.PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH > width:
            raise forms.ValidationError(_('The uploaded file is not wide enough'))
        if settings.PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT and settings.PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT > height:
            raise forms.ValidationError(_('The uploaded file is not tall enough'))
        return uploaded_image

    def save(self, request, *args, **kwargs):
        obj = self._object
        self.instance.creator = request.user
        self.instance.content_object = obj
        if "attachment_accessibility_file" in self.changed_data:
            # New file : regenerate new random name for this attachment
            instance = super().save(commit=False)
            instance.save(**{'force_refresh_suffix': True})
            return instance
        return super().save(*args, **kwargs)


class HDViewPointForm(MapEntityForm):
    geomfields = ['geom']

    def __init__(self, *args, content_type=None, object_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if content_type and object_id:
            ct = ContentType.objects.get_for_id(content_type)
            self.instance.content_type = ct
            self.instance.content_object = ct.get_object_for_this_type(id=object_id)
            self.instance.object_id = object_id
            self.helper.form_action += f"?object_id={object_id}&content_type={content_type}"

    class Meta:
        model = HDViewPoint
        fields = ('picture', 'geom', 'author', 'title', 'license', 'legend')


class HDViewPointAnnotationForm(forms.ModelForm):
    annotations = forms.JSONField(label=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields['annotations'].required = False
        self.fields['annotations'].widget = forms.Textarea(
            attrs={
                'name': 'annotations',
                'rows': '15',
                'type': 'textarea',
                'autocomplete': 'off',
                'autocorrect': 'off',
                'autocapitalize': 'off',
                'spellcheck': 'false',
                # Do not show GEOJson textarea to users
                'style': 'display: none;'
            }
        )
        self._init_layout()

    def _init_layout(self):
        """ Setup form buttons, submit URL, layout """

        actions = [
            Button('cancel', _('Cancel'), css_class="btn btn-light ml-auto mr-2"),
            SubmitButton('save_changes', _('Save changes')),
        ]

        leftpanel = Div(
            'annotations',
            css_id="modelfields",
        )
        formactions = FormActions(
            *actions,
            css_class="form-actions",
            template='mapentity/crispy_forms/bootstrap4/layout/formactions.html'
        )

        # # Main form layout
        self.helper.help_text_inline = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_style = "default"
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'controls col-md-9'
        self.helper.layout = Layout(
            Div(
                Div(
                    leftpanel,
                    # *rightpanel,
                    css_class="row"
                ),
                css_class="container-fluid"
            ),
            formactions,
        )

    class Meta:
        model = HDViewPoint
        fields = ('annotations', )
