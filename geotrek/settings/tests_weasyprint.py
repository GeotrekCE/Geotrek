from .default import *  # NOQA

#
#  Django Tests
# ..........................

TEST = True

TEST_EXCLUDE = ('django',)

LOGGING['handlers']['console']['level'] = 'CRITICAL'

LANGUAGE_CODE = 'en'

SOUTH_TESTS_MIGRATE = False

MAPENTITY_CONFIG['MAPENTITY_WEASYPRINT'] = True
