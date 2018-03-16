"""
    Administration of authentication
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from geotrek.authent.models import Structure
from geotrek.authent.models import UserProfile


admin.site.unregister(get_user_model())


class UserProfileInline(admin.StackedInline):
    """ Custom form """
    model = UserProfile


class UserProfileAdmin(UserAdmin):
    """ Custom adminsite """
    inlines = [UserProfileInline]


if not settings.AUTHENT_TABLENAME:
    # If users are authenticated in a custom database, do not manage them here.
    User = get_user_model()
    admin.site.register(User, UserProfileAdmin)
    admin.site.register(Structure)
