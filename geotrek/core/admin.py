from django.contrib import admin

from geotrek.core.models import (Datasource, Stake, Usage, Network, Trail,
                                 Comfort,)


class DatasourceAdmin(admin.ModelAdmin):
    list_display = ('source', 'structure')
    search_fields = ('source', 'structure')
    list_filter = ('structure',)


class StakeAdmin(admin.ModelAdmin):
    list_display = ('stake', 'structure')
    search_fields = ('stake', 'structure')
    list_filter = ('structure',)


class UsageAdmin(admin.ModelAdmin):
    list_display = ('usage', 'structure')
    search_fields = ('usage', 'structure')
    list_filter = ('structure',)


class NetworkAdmin(admin.ModelAdmin):
    list_display = ('network', 'structure')
    search_fields = ('network', 'structure')
    list_filter = ('structure',)


class ComfortAdmin(admin.ModelAdmin):
    list_display = ('comfort', 'structure')
    search_fields = ('comfort', 'structure')
    list_filter = ('structure',)


admin.site.register(Datasource, DatasourceAdmin)
admin.site.register(Stake, StakeAdmin)
admin.site.register(Usage, UsageAdmin)
admin.site.register(Network, NetworkAdmin)
admin.site.register(Comfort, ComfortAdmin)
