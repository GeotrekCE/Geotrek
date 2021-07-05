from django.apps import AppConfig
from django.core.checks import register, Tags
from django.utils.translation import gettext_lazy as _


class SignageConfig(AppConfig):
    name = 'geotrek.signage'
    verbose_name = _("Signage")

    def ready(self):
        from .forms import SignageForm

        def check_hidden_fields_settings(app_configs, **kwargs):
            # Check all Forms hidden fields settings
            errors = SignageForm.check_fields_to_hide()
            return errors

        register(check_hidden_fields_settings, Tags.security)
