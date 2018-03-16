from mapentity.registry import registry

from . import models


urlpatterns = registry.register(models.Infrastructure)
urlpatterns += registry.register(models.Signage)
