from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model

from geotrek.appconfig import GeotrekConfig
from geotrek.authent.utils.signals import create_user_profile


class AuthentConfig(GeotrekConfig):
    name = 'geotrek.authent'
    verbose_name = _("Authent")

    def ready(self):
        User = get_user_model()
        post_save.connect(create_user_profile, sender=User, dispatch_uid="create_user_profile")
