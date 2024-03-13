from django.apps import AppConfig
from django.core.checks import register, Tags
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    name = 'geotrek.core'
    verbose_name = _("Topology")

    def ready(self):
        from .forms import PathForm, TrailForm

        def check_hidden_fields_settings(app_configs, **kwargs):
            # Check all Forms hidden fields settings
            errors = PathForm.check_fields_to_hide()
            errors.extend(TrailForm.check_fields_to_hide())
            return errors

        register(check_hidden_fields_settings, Tags.security)
