from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.urls import NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from geotrek.common.mixins.actions import MergeActionMixin
from . import models as common_models

if 'modeltranslation' in settings.INSTALLED_APPS:
    from modeltranslation.admin import TabbedTranslationAdmin
else:
    from django.contrib.admin import ModelAdmin as TabbedTranslationAdmin


class OrganismAdmin(MergeActionMixin, admin.ModelAdmin):
    list_display = ('organism', 'structure')
    search_fields = ('organism', 'structure')
    list_filter = ('structure',)
    merge_field = 'organism'


class FileTypeAdmin(MergeActionMixin, admin.ModelAdmin):
    list_display = ('type', 'structure')
    search_fields = ('type', 'structure__name')
    list_filter = ('structure',)
    merge_field = 'type'


class LicenseAdmin(admin.ModelAdmin):
    list_display = ["label"]
    search_fields = ["label"]


class MapEntityContentTypeFilter(admin.SimpleListFilter):
    title = _('content type')
    parameter_name = 'content_type'

    def lookups(self, request, model_admin):
        from mapentity.registry import registry
        values = []
        for model, entity in registry.registry.items():
            content_type = model.get_content_type_id()
            values.append((content_type, entity.label))
        return tuple(values)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type=self.value())


class AttachmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_update'
    search_fields = ('title', 'legend', 'author', 'object_id')
    list_display = ('filename', 'legend', 'author', 'content_link', 'content_type')
    list_filter = ('filetype', MapEntityContentTypeFilter)
    exclude = ('object_id',)
    readonly_fields = ('content_type', 'content_link', 'creator', 'title')

    def has_add_permission(self, request):
        """ Do not add from Adminsite.
        """
        return False

    def content_link(self, obj):
        """Returns content object link"""
        try:
            assert hasattr(obj.content_object, '_entity'), f'Unregistered model {obj.content_type}'
            content_url = obj.content_object.get_detail_url()
        except (ObjectDoesNotExist, NoReverseMatch, AssertionError):
            return f'{obj.object_id}'
        else:
            return format_html('<a data-pk="{}" href="{}" >{}</a>',
                               obj.object_id, content_url, obj.object_id)

    content_link.short_description = _('Linked content')


class ThemeAdmin(MergeActionMixin, TabbedTranslationAdmin):
    list_display = ('label', 'cirkwi', 'pictogram_img')
    search_fields = ('label',)
    merge_field = 'label'


class RecordSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'pictogram_img')
    search_fields = ('name', )


class TargetPortalAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'title')
    search_fields = ('name', 'website')


class ReservationSystemAdmin(MergeActionMixin, admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    merge_field = 'name'


class LabelAdmin(TabbedTranslationAdmin):
    list_display = ('pictogram_img', 'name', 'filter')
    list_display_links = ('name',)
    search_fields = ('name', )


admin.site.register(common_models.Organism, OrganismAdmin)
admin.site.register(common_models.Attachment, AttachmentAdmin)
admin.site.register(common_models.FileType, FileTypeAdmin)
admin.site.register(common_models.Theme, ThemeAdmin)
admin.site.register(common_models.RecordSource, RecordSourceAdmin)
admin.site.register(common_models.TargetPortal, TargetPortalAdmin)
admin.site.register(common_models.ReservationSystem, ReservationSystemAdmin)
admin.site.register(common_models.Label, LabelAdmin)
admin.site.register(common_models.License, LicenseAdmin)
