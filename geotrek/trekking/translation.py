from django.conf import settings

from modeltranslation.translator import translator, TranslationOptions

from geotrek.trekking import models as trekking_models


# Trek app

class TrekTO(TranslationOptions):
    fields = ('name', 'departure', 'arrival', 'description_teaser',
              'description', 'ambiance', 'access', 'disabled_infrastructure', 'advice',
              'advised_parking', 'public_transport') + (
        ('published',) if settings.PUBLISHED_BY_LANG else tuple())
    fallback_undefined = {
        'published': None
    }


class POITO(TranslationOptions):
    fields = ('name', 'description') + (
        ('published',) if settings.PUBLISHED_BY_LANG else tuple()
    )


class POITypeTO(TranslationOptions):
    fields = ('label', )


class ThemeTO(TranslationOptions):
    fields = ('label', )


class TrekNetworkTO(TranslationOptions):
    fields = ('network', )


class UsageTO(TranslationOptions):
    fields = ('usage', )


class RouteTO(TranslationOptions):
    fields = ('route', )


class DifficultyLevelTO(TranslationOptions):
    fields = ('difficulty', )


class WebLinkTO(TranslationOptions):
    fields = ('name', )


class WebLinkCategoryTO(TranslationOptions):
    fields = ('label', )

# Register previously defined translation options
trek_translation_to_register = [
    (trekking_models.Trek, TrekTO),
    (trekking_models.POI, POITO),
    (trekking_models.POIType, POITypeTO),
    (trekking_models.Theme, ThemeTO),
    (trekking_models.TrekNetwork, TrekNetworkTO),
    (trekking_models.Usage, UsageTO),
    (trekking_models.Route, RouteTO),
    (trekking_models.DifficultyLevel, DifficultyLevelTO),
    (trekking_models.WebLink, WebLinkTO),
    (trekking_models.WebLinkCategory, WebLinkCategoryTO),
]

for model, model_to in trek_translation_to_register:
    translator.register(model, model_to)
