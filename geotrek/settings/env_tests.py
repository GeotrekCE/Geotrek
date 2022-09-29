#
#  Django Tests
# ..........................

TEST = True

ALLOWED_HOSTS = ['localhost']

CELERY_ALWAYS_EAGER = True

# TEST_EXCLUDE = ('django',)

ALLOWED_HOSTS = ['localhost']

INSTALLED_APPS += (
    'geotrek.diving',
    'geotrek.sensitivity',
    'geotrek.outdoor',
    'drf_yasg',
)

LOGGING['loggers']['']['handlers'] = ('log_file', )
LOGGING['handlers']['log_file']['level'] = 'INFO'

LANGUAGE_CODE = 'en'
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('en', 'es', 'fr', 'it')

LAND_BBOX_AREAS_ENABLED = True

TIME_ZONE = "UTC"

class DisableMigrations():
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

ADMINS = (
    ('test', 'test@test.com'),
)

MANAGERS = ADMINS

CRISPY_FAIL_SILENTLY = False

# TEST_RUNNER = 'geotrek.test_runner.TestRunner'
