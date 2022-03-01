from geotrek.infrastructure import models
from geotrek.signage.views import SignageViewSet


class SyncRando:
    def __init__(self, sync):
        self.global_sync = sync

    def sync(self, lang):
        self.global_sync.sync_geojson(lang, SignageViewSet, 'signages.geojson', type_view={"get": "rando-v2-geojson"})
        self.global_sync.sync_static_file(lang, 'signage/picto-signage.png')
        models_picto = [models.InfrastructureType]
        self.global_sync.sync_pictograms(lang, models_picto, zipfile=self.global_sync.zipfile)
