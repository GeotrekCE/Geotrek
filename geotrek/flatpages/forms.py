from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from geotrek.common.mixins.forms import CommonForm
from geotrek.common.models import Attachment, FileType
from geotrek.flatpages.models import FlatPage
if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.settings import AVAILABLE_LANGUAGES


class FlatPageForm(CommonForm):
    content = forms.CharField(widget=forms.Textarea, label=_("Content"))
    cover_image = forms.ImageField(label=_("Cover image"), required=False)
    cover_image_author = forms.CharField(label=_("Cover image author"), max_length=128, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs['user']
        super().__init__(*args, **kwargs)
        # Revert widget modifications done by MapentityForm.__init__()
        for fieldname in self.fields.keys():
            if fieldname.startswith('content_'):
                self.fields[fieldname].widget = forms.Textarea()
        self.fields['source'].help_text = None
        self.fields['portal'].help_text = None
        if self.instance.pk:
            page = Attachment.objects.filter(
                content_type=ContentType.objects.get_for_model(FlatPage),
                object_id=self.instance.pk
            ).first()
            if page:
                self.fields['cover_image'].initial = page.attachment_file
                self.fields['cover_image_author'].initial = page.author

    class Meta:
        model = FlatPage
        fields = (
            'title', 'order', 'published', 'source',
            'portal', 'external_url', 'target',
            'cover_image', 'cover_image_author',
            'content'
        )

    def clean(self):
        cleaned_data = super().clean()
        for lang in AVAILABLE_LANGUAGES:
            external_url = cleaned_data.get('external_url_' + lang, None)
            if external_url is not None and len(external_url) > 0:
                if 'content_' + lang in self.errors:
                    self.errors.pop('content_' + lang)

            # Test if HTML was filled
            # Use strip_tags() to catch empty tags (e.g. ``<p></p>``)
            html_content = cleaned_data.get('content_{}'.format(lang), None) or ''
            if external_url and external_url.strip() and strip_tags(html_content):
                raise ValidationError(_('Choose between external URL and HTML content'))

        return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=commit)
        if commit and self.cleaned_data['cover_image']:
            Attachment.objects.update_or_create(
                content_type=ContentType.objects.get_for_model(FlatPage),
                object_id=page.id,
                defaults={
                    'attachment_file': self.cleaned_data['cover_image'],
                    'filetype': FileType.objects.get_or_create(type="Photographie", structure=None)[0],
                    'creator': self.user,
                    'author': self.cleaned_data['cover_image_author'],
                    'starred': True,
                }
            )
        if commit and not self.cleaned_data['cover_image']:
            Attachment.objects.filter(
                content_type=ContentType.objects.get_for_model(FlatPage),
                object_id=page.id,
            ).delete()
        return page
