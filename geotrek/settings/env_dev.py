#
# Django Development
# ..........................

import sys
import os

# Makemessages uses Locale_paths's settings to get the list of translations to do.
# We change 'var/extra_locale' to 'geotrek/locale'

if 'makemessages' in sys.argv:
    LOCALE_PATHS = (os.path.join(PROJECT_DIR, 'locale'),)

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#
# Developper additions
# ..........................

INSTALLED_APPS += (
    'django_extensions',
    # 'debug_toolbar',
    # 'geotrek.diving',
    # 'geotrek.sensitivity',
    # 'geotrek.outdoor',
    'drf_yasg',
)

INTERNAL_IPS = type(str('c'), (), {'__contains__': lambda *a: True})()

ALLOWED_HOSTS = ['*']

MIDDLEWARE += (
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

LOGGING['loggers']['']['level'] = 'DEBUG'

CACHES['default']['BACKEND'] = 'django.core.cache.backends.locmem.LocMemCache'
