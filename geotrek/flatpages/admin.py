import re

from django.contrib import admin
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from geotrek.flatpages import models as flatpages_models
from geotrek.flatpages.forms import FlatPageForm, MenuItemForm
from geotrek.flatpages.models import FlatPage
from geotrek.common.models import FileType, Attachment
from django.contrib.auth.models import User

if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.admin import TabbedTranslationAdmin

    class BaseAdmin(TabbedTranslationAdmin, TreeAdmin):
        pass

else:  # pragma: no cover

    # This is excluded from code coverage check, because it cannot be auto-tested.
    # Similar to `from django.contrib.admin import ModelAdmin as TabbedTranslationAdmin` found in other modules
    class BaseAdmin(TreeAdmin):
        pass


class FlatPageAdmin(BaseAdmin):
    change_form_template = 'flatpages/translations_js.html'
    list_display = ('title', 'published', 'publication_date', 'portals_for_display', )
    list_filter = (
        'published',
        ("portals", admin.filters.RelatedOnlyFieldListFilter),
    )
    search_fields = ('title', 'content')
    form = movenodeform_factory(flatpages_models.FlatPage, form=FlatPageForm)

    # Due to an issue with `modeltranslation` we have to specify fields explicitly even though
    # FlatPagesAdmin inherits ModelAdmin. This is required to show treebeard's fields, `_position`
    # and `_ref_node_id`.
    fields = (
        'title',
        'published',
        'portals',
        'source',
        'cover_image',
        'cover_image_author',
        'content',
        '_position',
        '_ref_node_id',
    )

    @admin.display(description=_('Portals'))
    def portals_for_display(self, obj):
        return ', '.join([portal.name for portal in obj.portals.all()])

    def get_form(self, request, *args, **kwargs):
        # Django's ModelAdmin generates a ModelForm class based on FlatPageForm in the add/edit views. We do not control
        # the form instance creation so we override `get_form` to inject the `user` attribute
        # needed by FlatPageForm on the newly created Form class.
        form_class = super().get_form(request, *args, **kwargs)
        form_class.user = request.user
        return form_class

    def save_related(self, request, form, formsets, change):

        # We override `ModelAdmin.save_related` to add/update/delete the attachment. Why not in
        # `ModelAdmin.save_form` which may have looked like a better place? This is because Django's ModelAdmin
        # does not commit the object in `save_form`, it waits for formsets' validations. We override
        # `save_related` because we need the committed object (with an ID).
        # See `django.contrib.admin.options.py:L1578`
        super().save_related(request, form, formsets, change)
        form.save_cover_image()
        all_attachments = form.instance.attachments.all()
        attachments_url = []
        for field in form.instance._meta.get_fields():
            if field.get_internal_type() == "TextField":
                field_value = getattr(form.instance, field.name)
                if field_value is not None:
                    matches = re.finditer(r'(src=\".+?/media/)(?P<url>.+?)\" ', field_value)
                    for match in matches:
                        if match["url"] not in all_attachments:
                            page = FlatPage.add_root(title="tinymceAttachment")
                            filetype = FileType.objects.get(type="Photographie")
                            attachment = Attachment.objects.create(
                                content_object=page,
                                attachment_file=match["url"],
                                author='',
                                filetype=filetype,
                                creator=request.user,
                            )
                            form.instance.attachments.add(attachment)
                            attachments_url.append(match["url"])

        # print("Attachements_URL => ", attachments_url)
        # print("Attachements => ", form.instance.attachments.all())


class MenuItemAdmin(BaseAdmin):
    list_display = ('title', 'published', 'portals_for_display', )
    list_filter = (
        ("portals", admin.filters.RelatedOnlyFieldListFilter),
    )
    form = movenodeform_factory(flatpages_models.MenuItem, form=MenuItemForm)
    fieldsets = [
        (None, {
            'fields': [
                'title',
                'pictogram',
                'thumbnail',
                'portals',
                'platform',
                'published',
                'target_type',
            ],
        }),
        (_('Page'), {
            'fields': [
                'page',
            ],
            'classes': ('hidden', 'page_fieldset', )
        }),
        (_('Link'), {
            'fields': [
                'link_url',
                'open_in_new_tab',
            ],
            'classes': ('hidden', 'link_fieldset', )
        }),
        (None, {
            'fields': [
                '_position',
                '_ref_node_id',
            ],
        }),
    ]

    @admin.display(description=_('Portals'))
    def portals_for_display(self, obj):
        return ", ".join(p.name for p in obj.portals.all())

    def get_form(self, request, *args, **kwargs):
        # Django's ModelAdmin generates a ModelForm class based on FlatPageForm in the add/edit views. We do not control
        # the form instance creation so we override `get_form` to inject the `user` attribute
        # needed by FlatPageForm on the newly created Form class.
        form_class = super().get_form(request, *args, **kwargs)
        form_class.user = request.user
        return form_class

    def save_related(self, request, form, formsets, change):
        # We override `ModelAdmin.save_related` to add/update/delete the attachment. Why not in
        # `ModelAdmin.save_form` which may have looked like a better place? This is because Django's ModelAdmin
        # does not commit the object in `save_form`, it waits for formsets' validations. We override
        # `save_related` because we need the committed object (with an ID).
        # See `django.contrib.admin.options.py:L1578`
        super().save_related(request, form, formsets, change)
        form.save_thumbnail()


if settings.FLATPAGES_ENABLED:
    admin.site.register(flatpages_models.FlatPage, FlatPageAdmin)
    admin.site.register(flatpages_models.MenuItem, MenuItemAdmin)
