from django.db import models
from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin
from tinymce.widgets import TinyMCE
from modeltranslation.admin import TranslationAdmin

from geotrek.tourism import models as tourism_models


class DataSourceAdmin(TranslationAdmin):
    list_display = ('title', 'pictogram_img')
    search_fields = ('title',)

admin.site.register(tourism_models.DataSource, DataSourceAdmin)


class InformationDeskTypeAdmin(TranslationAdmin):
    list_display = ('label', 'pictogram_img')
    search_fields = ('label', )

admin.site.register(tourism_models.InformationDeskType, InformationDeskTypeAdmin)


class InformationDeskAdmin(LeafletGeoAdmin, TranslationAdmin):
    list_display = ('name', 'website', 'municipality')
    search_fields = ('name',)

    formfield_overrides = {
        models.TextField: {'widget': TinyMCE},
    }

admin.site.register(tourism_models.InformationDesk, InformationDeskAdmin)
