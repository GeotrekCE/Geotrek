"""

Extends geotrek.settings.base using values coming
from a .INI file (default: etc/settings.ini).

It prevents users from editing a python file to configure Geotrek,
and provides a way to restrict the set of configurable options.

In addition, the same .INI file is used by buildout in order to
create config files of nginx, etc.

"""
import os

from django.core.exceptions import ImproperlyConfigured
from django.conf.global_settings import LANGUAGES as LANGUAGES_LIST

from . import EnvIniReader
from .base import *


DEPLOY_ROOT = os.getenv('DEPLOY_ROOT', os.path.dirname(PROJECT_ROOT_PATH))

settingsfile = os.getenv('GEOTREK_SETTINGS',
                         os.path.join(DEPLOY_ROOT, 'etc', 'settings.ini'))


envini = EnvIniReader(settingsfile)

#
#  Main settings
#..........................

SECRET_KEY = envini.get('secret_key', SECRET_KEY)

ROOT_URL = envini.get('rooturl', ROOT_URL)
FORCE_SCRIPT_NAME = ROOT_URL if ROOT_URL != '' else None
ADMIN_MEDIA_PREFIX = '%s/static/admin/' % ROOT_URL
# Keep default values equal to buildout default values
DEPLOY_ROOT = envini.get('deployroot', section="django", default=DEPLOY_ROOT)
MEDIA_URL = envini.get('mediaurl', section="django", default=MEDIA_URL)
MEDIA_URL_SECURE = envini.get('mediaurl_secure', section="django", default=MEDIA_URL_SECURE)
STATIC_URL = '%s%s' % (ROOT_URL, envini.get('staticurl', section="django", default=STATIC_URL))
MEDIA_ROOT =  envini.get('mediaroot', section="django", default=os.path.join(DEPLOY_ROOT, 'var', 'media'))
STATIC_ROOT =  envini.get('staticroot', section="django", default=os.path.join(DEPLOY_ROOT, 'var', 'static'))
CACHE_ROOT =  envini.get('cacheroot', section="django", default=os.path.join(DEPLOY_ROOT, 'var', 'cache'))
UPLOAD_DIR = envini.get('uploaddir', section="django", default=UPLOAD_DIR)
MAPENTITY_CONFIG['TEMP_DIR'] =  envini.get('tmproot', section="django", default=os.path.join(DEPLOY_ROOT, 'var', 'tmp'))


DATABASES['default']['NAME'] = envini.get('dbname')
DATABASES['default']['USER'] = envini.get('dbuser')
DATABASES['default']['PASSWORD'] = envini.get('dbpassword')
DATABASES['default']['HOST'] = envini.get('dbhost', 'localhost')
DATABASES['default']['PORT'] = envini.getint('dbport', 5432)


CACHES['default']['TIMEOUT'] = envini.getint('cachetimeout', 3600 * 24)
CACHES['fat']['BACKEND'] = 'django.core.cache.backends.filebased.FileBasedCache'
CACHES['fat']['LOCATION'] = CACHE_ROOT
CACHES['fat']['TIMEOUT'] = envini.getint('cachetimeout', 3600 * 24)


LANGUAGE_CODE = envini.get('language', LANGUAGE_CODE, env=False)
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE
LANGUAGES = tuple([l for l in LANGUAGES_LIST if l[0] in envini.getstrings('languages')])

TITLE = envini.get('title', MAPENTITY_CONFIG['TITLE'])
MAPENTITY_CONFIG['TITLE'] = TITLE
MAPENTITY_CONFIG['ROOT_URL'] = ROOT_URL
MAPENTITY_CONFIG['LANGUAGE_CODE'] = LANGUAGE_CODE
MAPENTITY_CONFIG['LANGUAGES'] = LANGUAGES


#
#  Deployment settings
#..........................

MAPENTITY_CONFIG['CONVERSION_SERVER'] = '%s://%s:%s' % (envini.get('protocol', section='convertit', default='http'),
                                                        envini.get('host', section='convertit', default='0.0.0.0'),
                                                        envini.get('port', section='convertit', default='6543'))

MAPENTITY_CONFIG['CAPTURE_SERVER'] = '%s://%s:%s' % (envini.get('protocol', section='screamshotter', default='http'),
                                                     envini.get('host', section='screamshotter', default='0.0.0.0'),
                                                     envini.get('port', section='screamshotter', default='8001'))


#
#  Geotrek settings
#..........................

DEFAULT_STRUCTURE_NAME = envini.get('defaultstructure')

#
#  GIS settings
#..........................

SRID = int(envini.get('srid', SRID))
SPATIAL_EXTENT = tuple(envini.getfloats('spatial_extent'))

LEAFLET_CONFIG['TILES'] = [
    (gettext_noop('Scan'), '%s/tiles/scan/{z}/{x}/{y}.png' % ROOT_URL),
    (gettext_noop('Ortho'), '%s/tiles/ortho/{z}/{x}/{y}.jpg' % ROOT_URL),
]
LEAFLET_CONFIG['SRID'] = SRID
LEAFLET_CONFIG['TILES_EXTENT'] = SPATIAL_EXTENT

MAP_STYLES['path']['color'] = envini.get('layercolor_paths', MAP_STYLES['path']['color'])
MAP_STYLES['city']['color'] = envini.get('layercolor_land', MAP_STYLES['city']['color'])
MAP_STYLES['district']['color'] = envini.get('layercolor_land', MAP_STYLES['district']['color'])
MAP_STYLES['restrictedarea']['color'] = envini.get('layercolor_land', MAP_STYLES['restrictedarea']['color'])

_others_color = envini.get('layercolor_others', None)
if _others_color:
    MAP_STYLES.setdefault('detail', {})['color'] = _others_color
    MAP_STYLES.setdefault('others', {})['color'] = _others_color
