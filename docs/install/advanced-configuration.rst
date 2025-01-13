.. _advanced-configuration-section:

======================
Advanced configuration
======================

.. contents::
   :local:
   :depth: 2


Application settings
--------------------

Spatial extents
~~~~~~~~~~~~~~~

In order to check your configuration of spatial extents, a small tool
is available at http://server/tools/extents/.

.. note::

  Administrator privileges are required.


Email settings
~~~~~~~~~~~~~~

Geotrek-admin will send emails:

* to administrators when internal errors occur
* to managers when a feedback report is created

Email configuration takes place in ``/opt/geotrek-admin/var/conf/custom.py``, where you control
recipients emails (``ADMINS``, ``MANAGERS``) and email server configuration.

Set configuration settings in ``geotrek/settings/custom.py.dist`` template file.

You can test your configuration with the following command. A fake email will
be sent to the managers:

.. code-block:: bash

    sudo geotrek sendtestemail --managers
    
.. _API:

API
~~~

.. envvar:: API_IS_PUBLIC

    Set to ``True`` if you want the API V2 to be available for everyone without authentication. 

    Example::

        API_IS_PUBLIC = True

    Default::

        False

.. note::
  - This API provides access to promotion content (Treks, POIs, Touristic Contents ...). 
  - Set to ``False`` if Geotrek is intended to be used only for managing content and not promoting them.
  - This setting does not impact the Path endpoints, which means that the Paths informations will always need authentication to be display in the API, regardless of this setting.


Swagger API documentation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: INSTALLED_APPS for API V2

In order to enable swagger module to auto-document API, in the custom settings file, add the following code : 

    Enable API V2 documentation:

.. code-block:: python

        INSTALLED_APPS += ('drf_yasg', )


Then run ``sudo dpkg-reconfigure -u geotrek-admin``.
The API swagger documentation is now available here : ``<GEOTREK_ADMIN_URL>/api/v2``

Share services between several Geotrek instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As explained :ref:`in the design section <design-section>`, *Geotrek-admin* relies
on several services. They are generic and reusable, and can thus be shared
between several instances, in order to save system resources for example.

A simple way to achieve this is to install one instance with everything
as usual (*standalone*), and plug the other instances on its underlying services.


Capture and conversion
''''''''''''''''''''''

If you want to use external services, in ``.env``, add following variables:

.. code-block:: python

    CAPTURE_HOST=x.x.x.x
    CAPTURE_PORT=XX
    CONVERSION_HOST=x.x.x.x
    CONVERSION_PORT=XX

Then, you can delete all screamshotter and convertit references in ``docker-compose.yml``.


Shutdown useless services
'''''''''''''''''''''''''

Now that your instances point the shared server. You can shutdown the useless
services on each instance.

Start by stopping everything:

.. code-block:: bash

    sudo systemctl stop geotrek


Control number of workers and request timeouts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the application runs on 4 processes, and timeouts after 30 seconds.

To control those values, edit and fix your ``docker-compose.yml`` file in web and api section.

To know how many workers you should set, please refer to `gunicorn documentation <http://gunicorn-docs.readthedocs.org/en/latest/design.html#how-many-workers>`_.


External authentication
~~~~~~~~~~~~~~~~~~~~~~~

You can authenticate user against a remote database table or view.

To enable this feature, fill these fields in ``/opt/geotrek-admin/var/conf/custom.py``:

.. code-block:: python

    AUTHENT_DATABASE = 'authent'
    DATABASES['authent'] = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '<database name>',
        'USER': '<user name>',
        'PASSWORD': '<password>',
        'HOST': '<host>',
        'PORT': '<port>',
    }
    AUTHENT_TABLENAME = '<table name>'
    AUTHENTICATION_BACKENDS = ['geotrek.authent.backend.DatabaseBackend']

Expected columns in table/view are :

* ``username`` : string (*unique*)
* ``first_name`` : string
* ``last_name``: string
* ``password`` : string (simple md5 encoded, or full hashed and salted password)
* ``email`` : string
* ``level`` : integer (1: readonly, 2: redactor, 3: path manager, 4: trekking manager, 5: management and trekking editor, 6: administrator)
* ``structure`` : string
* ``lang`` : string (language code)

.. note::

  - The schema used in ``AUTHENT_TABLENAME`` must be in the user search_path (``ALTER USER $geotrek_db_user SET search_path=public,userschema;``)
  - User management will be disabled from Administration backoffice.
  - In order to disable remote login, just comment *AUTHENTICATION_BACKENDS* line in settings file, and restart instance (see paragraph above).
  - Geotrek-admin can support many types of users authentication (LDAP, oauth, ...), contact us for more details.

Custom SQL
~~~~~~~~~~

Put your custom SQL in a file name ``/opt/geotrek-admin/var/conf/extra_sql/<app name>/<pre or post>_<script name>.sql``

* app name is the name of the Django application, eg. trekking or tourism
* ``pre_``… scripts are executed before Django migrations and ``post_``… scripts after
* script are executed in INSTALLED_APPS order, then by alphabetical order of script names

.. _map-settings:

Map settings
------------

Change or add WMTS tiles layers (IGN, OSM, Mapbox…)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, you have two basemaps layers in your Geotrek-admin (OSM and OpenTopoMap)

You can change or add more basemaps layers like this:

.. envvar:: LEAFLET_CONFIG['TILES'] 

  Specify the tiles URLs this way in your custom Django setting file:

    Syntax::

        LEAFLET_CONFIG['TILES'] = [('NAME_OF_TILE', 'URL', 'COPYRIGHT'), ...]

    Basic example::

        LEAFLET_CONFIG['TILES'] = [
        ('OSM', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', '© OpenStreetMap Contributors'),
        ('OpenTopoMap', 'http://a.tile.opentopomap.org/{z}/{x}/{y}.png', 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)'),
        ]

    Example with IGN and OSM basemaps::

        LEAFLET_CONFIG['TILES'] = [
        (
            'IGN Plan V2',
            '//data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            {
                'attribution': 'Plan IGNV2 - Carte © IGN/Geoportail',
                'maxNativeZoom': 16,
                'maxZoom': 22
            }
        ),
        (
            'IGN Orthophotos',
            '//data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            {
                'attribution': 'Orthophotos - Carte © IGN/Geoportail',
                'maxNativeZoom': 19,
                'maxZoom': 22
            }
        ),
        (
            'OpenStreetMap',
            '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">Contributeurs d\'OpenStreetMap</a>',
                'maxNativeZoom': 19,
                'maxZoom': 22
            }
        ),
        (
            'OpenTopoMap',
            '//{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            {
                'attribution': 'map data: © <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | map style: © <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                'maxNativeZoom': 17,
                'maxZoom': 22
            }
        ),
        (
            'IGN Scan 25',
            '//data.geopf.fr/private/wmts?apikey=ign_scan_ws&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&EXCEPTIONS=text/xml&FORMAT=image/jpeg&SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            {
                'attribution': 'Plan Scan 25 Touristique - Carte © IGN/Geoportail',
                'maxNativeZoom': 17,
                'maxZoom': 22
            }
        ),
        ]

    You can also configure overlays layers like this::

        LEAFLET_CONFIG['OVERLAYS'] = [
        (
            'IGN Cadastre',
            '//data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            {
                'attribution': 'Cadastre - Carte © IGN/Geoportail',
                'maxNativeZoom': 19,
                'maxZoom': 22
            }
        ),
        ]

.. note:: 
  To use some IGN Geoportail WMTS tiles (Scan25, Scan100, etc.), you may need an API key. You can find more information about this on https://geoservices.ign.fr/services-geoplateforme-diffusion.

Map layers zoom
~~~~~~~~~~~~~~~

.. envvar:: LEAFLET_CONFIG

    You can define the max_zoom the user can zoom for all tiles.

    Example::

        LEAFLET_CONFIG= 19


.. note::

  It can be interesting when your tiles can't go to a zoom. For example OpenTopoMap is 17.


Map layers colors and style
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: MAPENTITY_CONFIG for layers color and style

    All layers colors can be customized from the settings. See `Leaflet reference <http://leafletjs.com/reference.html#path>`_ for vectorial layer style.

    Example::

        MAPENTITY_CONFIG['MAP_STYLES']['path'] = {'color': 'red', 'weight': 5}

    Example with one parameter::

        MAPENTITY_CONFIG['MAP_STYLES']['city']['opacity'] = 0.8

.. note::

  It can be interesting when your tiles can't go to a zoom. For example OpenTopoMap is 17.


.. envvar:: COLORS_POOL

    Regarding colors that depend from database content, such as land layers (physical types, work management...) or restricted areas. We use a specific setting that receives a list of colors:

    Example::

        COLORS_POOL['restrictedarea'] = ['#ff00ff', 'red', '#ddddd'...]

See the default values in ``geotrek/settings/base.py`` for the complete list
of available styles.

.. code-block:: python

    MAPENTITY_CONFIG['MAP_STYLES'] = {
        'path': {'weight': 2, 'opacity': 1.0, 'color': '#FF4800'},
        'draftpath': {'weight': 5, 'opacity': 1, 'color': 'yellow', 'dashArray': '8, 8'},
        'city': {'weight': 4, 'color': 'orange', 'opacity': 0.3, 'fillOpacity': 0.0},
        'district': {'weight': 6, 'color': 'orange', 'opacity': 0.3, 'fillOpacity': 0.0, 'dashArray': '12, 12'},
        'restrictedarea': {'weight': 2, 'color': 'red', 'opacity': 0.5, 'fillOpacity': 0.5},
        'land': {'weight': 4, 'color': 'red', 'opacity': 1.0},
        'physical': {'weight': 6, 'color': 'red', 'opacity': 1.0},
        'competence': {'weight': 4, 'color': 'red', 'opacity': 1.0},
        'workmanagement': {'weight': 4, 'color': 'red', 'opacity': 1.0},
        'signagemanagement': {'weight': 5, 'color': 'red', 'opacity': 1.0},
        'print': {'path': {'weight': 1},
                  'trek': {'color': '#FF3300', 'weight': 7, 'opacity': 0.5,
                           'arrowColor': 'black', 'arrowSize': 10},}
    }

Color of the different layers on the map :

.. code-block:: python

    COLORS_POOL = {'land': ['#f37e79', '#7998f3', '#bbf379', '#f379df', '#f3bf79', '#9c79f3', '#7af379'],
                   'physical': ['#f3799d', '#79c1f3', '#e4f379', '#de79f3', '#79f3ba', '#f39779', '#797ff3'],
                   'circulation': ['#f3799d', '#79c1f3', '#e4f379', '#de79f3', '#79f3ba', '#f39779', '#797ff3'],
                   'competence': ['#a2f379', '#f379c6', '#79e9f3', '#f3d979', '#b579f3', '#79f392', '#f37984'],
                   'signagemanagement': ['#79a8f3', '#cbf379', '#f379ee', '#79f3e3', '#79f3d3'],
                   'workmanagement': ['#79a8f3', '#cbf379', '#f379ee', '#79f3e3', '#79f3d3'],
                   'restrictedarea': ['plum', 'violet', 'deeppink', 'orchid',
                                      'darkviolet', 'lightcoral', 'palevioletred',
                                      'MediumVioletRed', 'MediumOrchid', 'Magenta',
                                      'LightSalmon', 'HotPink', 'Fuchsia']}

Color of the different layers on the top right for landing.

.. note::

  - For land, physical, competence, signagemanagement, workmanagement should have 5 values.
  - For restricted Area: add as many color as your number of restricted area type
  - **Restart** the application for changes to take effect.


External raster layers
~~~~~~~~~~~~~~~~~~~~~~

.. tip::
  It is possible to add overlay tiles layer on maps. For example, it can be useful to:
    - Get the cadastral parcels on top of satellite images
    - Home made layers (*with Tilemill or QGisMapserver for example*).
    - Like the park center borders, traffic maps, IGN BDTopo® or even the Geotrek paths that are marked as invisible in the database!

.. envvar:: LEAFLET_CONFIG['OVERLAYS']

    In ``custom.py``, just add the following lines:

    Example::

        LEAFLET_CONFIG['OVERLAYS'] = [
        ('Cadastre', '//data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}', '&copy; Cadastre - Carte © IGN/Geoportail')
        ('Coeur de parc', 'http://serveur/coeur-parc/{z}/{x}/{y}.png', '&copy; PNF'),
        ]


**Expected properties:**

For ``GeoJSON`` files, you can provide the following properties :

* ``title``: string
* ``description``: string
* ``website``: string
* ``phone``: string
* ``pictures``: list of objects with ``url`` and ``copyright`` attributes
* ``category``: object with ``id`` and ``label`` attributes


Geographical CRUD
~~~~~~~~~~~~~~~~~

.. envvar:: PATH_SNAPPING_DISTANCE

    Minimum distance to merge two paths in unit of SRID

    Example::

        PATH_SNAPPING_DISTANCE = 2.0

.. note::

  - Change the distance. Better to keep it like this. 
  - Not used when ``TREKKING_TOPOLOGY_ENABLED = True``

.. envvar:: SNAP_DISTANCE

    Distance of snapping for the cursor in pixels on Leaflet map.

    Example::

        SNAP_DISTANCE = 30

.. envvar:: PATH_MERGE_SNAPPING_DISTANCE

    Minimum distance to merge two paths.

    Example::

        PATH_MERGE_SNAPPING_DISTANCE = 2

.. note::

  - Change the distance. Should be higher or the same as ``PATH_SNAPPING_DISTANCE``. 
  - Used when ``TREKKING_TOPOLOGY_ENABLED = True``.

.. envvar:: TREK_POINTS_OF_REFERENCE_ENABLED

    Points of reference are enabled on form of treks.

    Example::

        TREK_POINTS_OF_REFERENCE_ENABLED = True

    Default::

        False

.. envvar:: OUTDOOR_COURSE_POINTS_OF_REFERENCE_ENABLED

    Points of reference are enabled on form of outdoor courses.

    Example::

        OUTDOOR_COURSE_POINTS_OF_REFERENCE_ENABLED = True

    Default::
    
        False

.. envvar:: TOPOLOGY_STATIC_OFFSETS

    Land objects are added on other objects (path for example) with offset, avoiding overlay.

    Example::

        TOPOLOGY_STATIC_OFFSETS = {'land': -5, 'physical': 0, 'competence': 5, 'signagemanagement': -10, 'workmanagement': 10}

    Example with more overlays::

        TOPOLOGY_STATIC_OFFSETS = {'land': -7, 'physical': 0, 'competence': 7, 'signagemanagement': -14, 'workmanagement': 14}

.. note::

  You should not change it to avoid overlay except if you want to have more overlays.

**All settings used to generate altimetric profile :**

.. code-block:: python

    ALTIMETRIC_PROFILE_PRECISION = 25  # Sampling precision in meters
    ALTIMETRIC_PROFILE_AVERAGE = 2  # nb of points for altimetry moving average
    ALTIMETRIC_PROFILE_STEP = 1  # Step min precision for positive / negative altimetry gain
    ALTIMETRIC_PROFILE_BACKGROUND = 'white'
    ALTIMETRIC_PROFILE_COLOR = '#F77E00'
    ALTIMETRIC_PROFILE_HEIGHT = 400
    ALTIMETRIC_PROFILE_WIDTH = 800
    ALTIMETRIC_PROFILE_FONTSIZE = 25
    ALTIMETRIC_PROFILE_FONT = 'ubuntu'
    ALTIMETRIC_PROFILE_MIN_YSCALE = 1200  # Minimum y scale (in meters)
    ALTIMETRIC_AREA_MAX_RESOLUTION = 150  # Maximum number of points (by width/height)
    ALTIMETRIC_AREA_MARGIN = 0.15

.. note::

  - All these settings can be modified but you need to check the result every time
  - The only one modified most of the time is ``ALTIMETRIC_PROFILE_COLOR``


Disable darker map backgrounds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: MAPENTITY_CONFIG for map background

    Since IGN map backgrounds are very dense and colourful, a dark opacity is applied. In order to disable, change this MapEntity setting:

    Example::

        MAPENTITY_CONFIG['MAP_BACKGROUND_FOGGED'] = False

    Default::

        True

Map screenshots
~~~~~~~~~~~~~~~

.. code-block:: python

    SHOW_SENSITIVE_AREAS_ON_MAP_SCREENSHOT = True
    SHOW_POIS_ON_MAP_SCREENSHOT = True
    SHOW_SERVICES_ON_MAP_SCREENSHOT = True
    SHOW_SIGNAGES_ON_MAP_SCREENSHOT = True
    SHOW_INFRASTRUCTURES_ON_MAP_SCREENSHOT = True

.. envvar:: MAP_CAPTURE_SIZE

    Show objects on maps of PDF

    Example::

        MAP_CAPTURE_SIZE = 800

.. note::

  - Size in pixels of the capture.
  - Be careful with your pdfs.
  - If you change this value, pdfs will be rendered differently


Modules and components
----------------------

Enable Apps
~~~~~~~~~~~

In order to disable a full set of modules, in the custom settings file, add the following code:

.. code-block:: python

    # Disable infrastructure and maintenance
    _INSTALLED_APPS = list(INSTALLED_APPS)
    _INSTALLED_APPS.remove('geotrek.infrastructure')
    _INSTALLED_APPS.remove('geotrek.maintenance')
    INSTALLED_APPS = _INSTALLED_APPS


.. envvar:: TRAIL_MODEL_ENABLED

    In order to remove notion of trails.

    Example::

        TRAIL_MODEL_ENABLED = False

    Default::

        True


.. envvar:: LANDEDGE_MODEL_ENABLED

    In order to remove landedge model.

    Example::

        LANDEDGE_MODEL_ENABLED = False

    Default::

        True


In order to remove zoning combo-boxes on list map:

.. code-block:: python

    LAND_BBOX_CITIES_ENABLED = False
    LAND_BBOX_DISTRICTS_ENABLED = False
    LAND_BBOX_AREAS_ENABLED = False


.. envvar:: TOURISM_ENABLED

    In order to hide TouristicContents and TouristicEvents on menu.

    Example::

        TOURISM_ENABLED = False

    Default::

        True

.. envvar:: FLATPAGES_ENABLED

    In order to hide Flatpages on menu. Flatpages are used in Geotrek-rando.

    Example::

        FLATPAGES_ENABLED = False

    Default::

        True

.. envvar:: ACCESSIBILITY_ATTACHMENTS_ENABLED

    In order to hide the accessibility menu for attachments.

    Example::

        ACCESSIBILITY_ATTACHMENTS_ENABLED = False

    Default::

        True

.. note::

  - By doing so, some software upgrades may not be as smooth as usual.
  - Never forget to mention this customization if you ask for community support.


Paths
~~~~~

.. envvar:: ALLOW_PATH_DELETION_TOPOLOGY

    If ``False``, it forbids to delete a path when at least one topology is linked to this path.

    Example::

        ALLOW_PATH_DELETION_TOPOLOGY = True

    Default::

        False


.. envvar:: ALERT_DRAFT

    If ``True``, it sends a message to managers (MANAGERS) whenever a path has been changed to draft.


    Example::

        ALERT_DRAFT = False

    Default::

        True

.. envvar:: ALERT_REVIEW

    If ``True``, it sends a message to managers (MANAGERS) whenever an object which can be published has been changed to review mode.


    Example::

        ALERT_REVIEW = False

    Default::

        True

.. note::

  Email configuration takes place in ``/opt/geotrek-admin/var/conf/custom.py``, where you control recipients emails (``ADMINS``, ``MANAGERS``) and email server configuration.


Signage and Blade
~~~~~~~~~~~~~~~~~

``BLADE_ENABLED`` and ``LINE_ENABLED`` settings (default to ``True``) allow to enable or disable blades and lines submodules.

``DIRECTION_ON_LINES_ENABLED`` setting (default to ``False``) allow to have the `direction` field on lines instead of blades.

.. envvar:: BLADE_CODE_TYPE

    Type of the blade code (string or integer)


    Example::

        BLADE_CODE_TYPE = INT

.. note::

  - It can be string or integer
  - If you have an integer code : ``int``
  - If you have an string code : ``str``

.. envvar:: BLADE_CODE_FORMAT

    Correspond to the format of blades. Show N3-1 for the blade 1 of the signage N3.


    Example::

        BLADE_CODE_FORMAT = "{signagecode}-{bladenumber}"

.. note::

  - If you want to change : move information under bracket
  - You can also remove one element between bracket
  - You can do for exemple : ``"CD99.{signagecode}.{bladenumber}"``
  - It will display : ``CD99.XIDNZEIU.01 (first blade of XIDNZEIU)``
  - ``signagecode`` is the code of the signage
  - ``bladenumber`` is the number of the blade

.. envvar:: LINE_CODE_FORMAT

    Corresponds to the format used in export of lines. Used in csv of signage


    Example::

        LINE_CODE_FORMAT = "{signagecode}-{bladenumber}-{linenumber}"

.. note::

  - Similar with above
  - You can do for example : ``"CD99.{signagecode}-{bladenumber}.{linenumber}"``
  - It will display : ``CD99.XIDNZEIU-01.02`` (second line of the first blade of XIDNZEIU)
  - ``signagecode`` is the code of the signage
  - ``bladenumber`` is the number of the blade
  - ``linenumber`` is the number of the line

.. _trek-poi-intersection:

POI
~~~~

.. envvar:: TREK_POI_INTERSECTION_MARGIN

    Buffer around treks to intersects POIs (works only without dynamic segmentation)

    Example::

        TREK_POI_INTERSECTION_MARGIN = 500  # meters

    Default::

        500

Diving
~~~~~~

.. envvar:: INSTALLED_APPS for Diving

    In order to enable diving module, in the custom settings file, add the following code:

    Example::

        INSTALLED_APPS += ('geotrek.diving', )


Then run ``sudo dpkg-reconfigure -pcritical geotrek-admin``.

You can also insert diving minimal data (default practices, difficulties, levels and group permissions values):

.. code-block:: bash

    sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/basic.json
    cp /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/upload/* /opt/geotrek-admin/var/media/upload/

You can insert licenses of attachments with this command :

.. code-block:: bash

    sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/common/fixtures/licenses.json


Land
~~~~~~~

You can insert circulation and authorization types with this command :

::

    sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/land/fixtures/circulations.json

.. _outdoor:

Outdoor
~~~~~~~

.. envvar:: INSTALLED_APPS for Outdoor

    In order to enable Outdoor module, in the custom settings file, add the following code:

    Example::

        INSTALLED_APPS += ('geotrek.outdoor', )


Then run ``sudo dpkg-reconfigure -pcritical geotrek-admin``.

You can also insert Outdoor minimal data:

.. code-block:: bash

    sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/outdoor/fixtures/basic.json

After installing Outdoor module, you have to add permissions to your user groups on outdoor sites and courses.

.. note::

  - Outdoor module is not compatible with PostGIS <= 2.4 that is included in Ubuntu 18.04.
  - You should either upgrade to Ubuntu 20.04 or upgrade postGIS to 2.5 with https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa

.. _sensitive-areas:

Sensitive areas
~~~~~~~~~~~~~~~

.. note::

    The sensitivity module was developed as part of the Biodiv'Sports project to provide a central platform for sensitive areas.

    The official address of the Geotrek instance of the Biodiv'Sports project is: https://biodiv-sports.fr, and is the base URL for the following API URLs.


.. envvar:: INSTALLED_APPS for Sensitive areas

    In order to enable sensitivity module, in the custom settings file, add the following code:

    Example::

        INSTALLED_APPS += ('geotrek.sensitivity', )


    You can insert rules of sensitive area with these commands:

    .. code-block:: bash

        sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/rules.json
        cp -r /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/upload/rules/ /opt/geotrek-admin/var/media/upload/


The following settings are related to sensitive areas:

.. envvar:: SENSITIVITY_DEFAULT_RADIUS

    Default radius of sensitivity bubbles when not specified for species

    Example::

        SENSITIVITY_DEFAULT_RADIUS = 100  # meters

    Default::

        100


.. envvar:: SENSITIVE_AREA_INTERSECTION_MARGIN

    Buffer around treks to intersects sensitive areas

    Example::

        SENSITIVE_AREA_INTERSECTION_MARGIN = 500  # meters

    Default::

        500

.. notes

    # Take care if you change this value after adding data. You should update buffered geometry in sql.
    ``` UPDATE sensitivity_sensitivearea SET geom_buffered = ST_BUFFER(geom, <your new value>); ```

see :ref:`import-sensitive-areas` to import data.

Import from https://biodiv-sports.fr
''''''''''''''''''''''''''''''''''''''

In user interface, in the top-right menu, clic on "Imports" and choose "Biodiv'Sports".

On command line, run

.. code-block :: bash

    sudo geotrek import geotrek.sensitivity.parsers.BiodivParser


Import from shapefile
'''''''''''''''''''''''

In user interface, in the top-right menu, go to Imports and choose "Shapefile zone sensible espèce"
or "Shapefile zone sensible réglementaire".

.. note::
  The file must be a zip containing all the shapefile extensions (.shp, .shx, .prj, .dbf, .cpg)

.. figure:: ../images/advanced-configuration/import_shapefile.png
   :alt: Import shapefile in user interface
   :align: center

   Import shapefile in user interface


On command line, run:

.. code-block :: bash

    sudo geotrek import geotrek.sensitivity.parsers.SpeciesSensitiveAreaShapeParser <file.shp>

or:

.. code-block :: bash

    sudo geotrek  import geotrek.sensitivity.parsers.RegulatorySensitiveAreaShapeParser <file.shp>.

Attributes for "zones espèces sensibles" are:

* ``espece`` : species name. Mandatory. A species with this name must have been previously created.
* ``contact`` : contact (text or HTML format). Optional.
* ``description`` : description (text or HTML format). Optional.

Attributes for "zones sensibles réglementaires" are:

* ``name``: zone name.
* ``contact`` : contact (text or HTML format). Optional.
* ``description`` : description (text or HTML format). Optional.
* ``periode`` : month numbers of zone occupation, separated by comas, without spaces (ex. « 6,7,8 » for june, july and august)
* ``pratiques`` : sport practices names, separated by comas, without spaces (ex. « Terrestre,Aérien »). A sport practice with this name must have been previously created.
* ``url`` : card url. Optional.


Sync to Geotrek-rando
'''''''''''''''''''''''

Just run:

.. code-block :: bash

    sudo geotrek sync_rando <parameters>

If sensitivity module is enabled, sensitive areas will be automatically synchronized.


Feedback reports settings
-------------------------

Send acknowledge email
~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: SEND_REPORT_ACK

    If ``False``, no email will be sent to the sender of any feedback on Geotrek-rando website.

    Example::

        SEND_REPORT_ACK = True

    Default::

        False

.. _suricate-support:

Suricate support
~~~~~~~~~~~~~~~~

Suricate is the French national database gathering such reports. It exposes an API for external software to connect to. For Geotrek to connect to Suricate, you need to request two pairs of API keys allowing access.

Geotrek reports can work together with Suricate API, using one of three modes. Proceed through a mode full configuration before proceeding to the next mode.

**1 - No Suricate (default)**

This mode sends no report data to Suricate.

To initialize Report forms (Geotrek-admin, Geotrek-rando-V2, Geotrek-rando-V3) load lists for categories, activities, statuses and problem magnitude:

.. code-block:: python

    geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/feedback/fixtures/basic.json

**2 - Suricate Standard**

This mode forwards reports to Suricate, using the Standard API to post reports.

Reports are forwarded as long as we enter a value for the `email address` field at creation, otherwise they are kept for internal usage only.

Set your account settings in ``custom.py``:

.. code-block:: python

    SURICATE_REPORT_ENABLED = True

    SURICATE_REPORT_SETTINGS = {
        'URL': '<Suricate Standard API Url>',
        'ID_ORIGIN': '<Suricate origin ID>',
        'PRIVATE_KEY_CLIENT_SERVER': '<your private key client / server>',
        'PRIVATE_KEY_SERVER_CLIENT': '<your private key server / client>',
    }

**3 - Suricate Management (Workflow)**

This mode allows to retrieve reports and related data directly from Suricate, using the Management API to get data. It is used to process and manage reports, using the Intervention module and following a predefined worklow, while sending all progress to Suricate. It implies enabling Suricate Report mode as well.

.. figure:: ../images/advanced-configuration/suricate.png
   :alt: Suricate workflow
   :align: center

   Suricate workflow


Suricate Workflow mode defines a strict process, composed of several steps representing the lifecycle of a user report, from creation to closing. A report is always characterized with a status, depicting how far in the process the report is, and displayed using a specific color on the map.

**Reports**

A report consists of the following information :
    * A GPS position
    * A message describing the problem
    * A category : environment, security, usage conflit, signages
    * A magnitude : usage is possible, difficult, or impossible
    * A practice : trekking, cycling, horse-riding…
    * Up to three pictures

**Stakeholders and responsibility**

This workflow defines three stakeholders categories :
    * The sentinel : the person who submitted the report. They do not have a Geotrek user account nor intervene in the workflow, but they are kept updated on the processing of their report via semi-automatic e-mails.
    * Supervisors : they are assigned (a) report(s) for treatment. They are tasked with planning an Intervention on Geotrek and enter information about it.
    * The manager : they maintain a global view of all reports on the territory, assign reports to supervisors, handle messaging to the sentinel, and confirm reports resolution.

Any Geotrek user account can be used as a supervisor, as long as they have proper access and modification rights on both Report and Intervention modules. There can only be one Manager.

**Report processing**

Every night, Geotrek fetches new reports and updates through Suricate API. The manager receives an e-mail listing new reports (with “Filed” status). They can visualize them on Geotrek.

**1** - Qualification

The manager has three options when handling a newly filed report:
    * Classify : The report isn’t relevant. The manager sets the report to “Classified” and enters a message for the sentinel, explaining their choice. The report is considered closed.
    * Reject treatment : The report does not involve an area or an equipment under responsibility of the workflow users, but could be handled by another member of the Suricate community. The report is excluded from Geotrek workflow but is still accessible to the community via other applications using Suricate API.
    * Assignation : The manager selects a supervisor from a drop-down selector, and enters a message with instructions or further information. The supervisor receives an e-mail notifying them about the newly assigned report, along with the manager’s message. * The manager also enters a message destined to the sentinel, to notify them that the report is about to be handled. The report is set to status “Waiting”. Only after assignation can we proceed to the following steps.


**2** - Planification

The supervisor logs onto Geotrek and creates an Intervention linked to the assigned report, with a planification date. The intervention has status “Plannified”. If too many days have passed between report assignation and intervention creation, the report is automatically set to “Late intervention” status, marked with color red, and the supervisor receives a reminder by e-mail.

**3** - Resolution

The supervisor sets their intervention to “Resolved” status. The manager receives an e-mail notifying that a report is ready to be closed. If too many days have passed between intervention creation and intervention resolution, the report is automatically set to “Late resolution” status, marked with color red, and the supervisor receives a reminder e-mail.

**4** - Closing

Following the intervention’s resolution, the manager has to confirm the report was handled and sets it to “Resolved”. They enter a message for the sentinel to inform them that the report’s processing is over. The report is considered closed.

**5** - GPS relocalisation

At any point, the manager or the supervisor can re-define GPS location for the report. Relocating it outside of the district marked as workflow responsibility area causes the treatment to be rejected (see part 1 Qualification).
Furthermore, it is now possible to display the report layer on other Geotrek modules, for instance to compare positions between reports and signages or treks.

**6** - Reports visibility

When a supervisor logs in to Geotrek, they can only see reports that are currently assigned to them. Both the manager and administrators can see all existing reports.

**7** - Predefined messages

As we have seen above, the manager enters messages destined to the sentinel or to supervisors. These messages can be predefined in the administration interface and picked from a drop-down selector, then modified before sending. It is possible to automatically retrieve in a message the intervention date and the username of the supervisor that handled it.

**Workflow configuration**

Even though the workflow is a strict process, the following items are customisable.

Through administration interface :
    * Colors for each status
    * Selecting the manager
    * Selecting the workflow responsibility area
    * Predefined messages

**Through application configuration**:
    * API keys to connect to Suricate
    * Enabling of Workflow mode or any other mode
    * Enabling/disabling status colors on map
    * Duration of timers setting reports to “late” statuses

**Synchronization and network losses**

Communication between Suricate and Geotrek operates as follows :
    * Suricate to Geotrek : new information is fetched once a night
    * Geotrek to Suricate : every report update on Geotrek is immediately forwarded to Suricate

Maintaining synchronization between Suricate and Geotrek confronts us to the challenges of distributed software architecture. At any point, the connection between both applications can be lost, meaning that Suricate and Geotrek will no longer agree on a report’s status. Most of the time, this is simply due to temporary network failure.
A system is in place to compensate for such failures. If a request to Suricate API fails, it is stored in the database and resent a few hours later. In case of a long term loss of connection, Django commands are available for an administrator to run some connection tests and resend stored information once connection is recovered.


For technical documentation refer to : https://geotrek.ecrins-parcnational.fr/ressources/technique/2023-02-Geotrek-Suricate-configuration.pdf

You can find the same detailled explanation on the workflow in this article in french : https://makina-corpus.com/geotrek/gestion-territoires-naturels-geotrek-traitement-signalements-suricate

- Set your settings in ``custom.py`` :

.. code-block:: python

    SURICATE_WORKFLOW_ENABLED = True

    SURICATE_MANAGEMENT_SETTINGS = {
        'URL': '<Suricate Management API Url>',
        'ID_ORIGIN': '<Suricate origin ID>',
        'PRIVATE_KEY_CLIENT_SERVER': '<your private key client / server>',
        'PRIVATE_KEY_SERVER_CLIENT': '<your private key server / client>',
    }

    SURICATE_WORKFLOW_SETTINGS = {
        "SURICATE_RELOCATED_REPORT_MESSAGE": "This report is not located in Workflow responsiblity area.",
        "SKIP_MANAGER_MODERATION": False
    }

You can use the following command to test your connection settings:

.. code-block:: python

    geotrek sync_suricate -v 2 --connection-test

Load lists for activities and/or report statuses from Suricate:

.. code-block:: python

    geotrek sync_suricate --activities --statuses -v 2

Load alerts from Suricate (located in your bounding box) :

.. code-block:: python

    geotrek sync_suricate -v 2 --no-notification

- Then load extra required statuses for Reports and Interventions:

.. code-block:: python

    geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/feedback/fixtures/management_workflow.json
    geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/maintenance/fixtures/basic.json

- Go to the configuration site and :

  - if you want to include the moderation steps (``SKIP_MANAGER_MODERATION = False``), select a user as Workflow Manager (`/admin/feedback/workflowmanager/`). Their role is to assign reports to other users.
  - select a district as Workflow District (`/admin/feedback/workflowdistrict/`). This zone defines the area of reponsibility for reports. Reports relocated outside of the district will be excluded from workflow.
  - create predefined emails (`/admin/feedback/predefinedemail/`) to notify Suricate Sentinels and Administrators. You can use `##intervention_end_date##` and `##supervisor##` in the messages' body to automatically replace with the report's linked Intervention date and author. The Extended Username field will be dsiplayed (see User Profile under `/admin/auth/user/`).
  - Make sure Users involved in the workflow have proper permissions to create and update Reports and Interventions (`/admin/auth/user/`)

.. note::

  - Be aware that, when enabling Suricate Management mode, Suricate becomes the master database for reports. This means **reports created in Geotrek-admin will not be saved to the database, they will only be sent to Suricate**.
  - Reports are only saved when synchronized back from Suricate, when the synchronization command is run. 

Make sure to run these three commands daily to maintain synchronization and update reports (thanks to `cron` for instance) :

.. code-block:: python

    geotrek retry_failed_requests_and_mails
    geotrek check_timers
    geotrek sync_suricate


Display reports with status defined colors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: ENABLE_REPORT_COLORS_PER_STATUS

    Go to the Configuration site and select colors to display for each status (`/admin/feedback/reportstatus/`).

    Example::

        ENABLE_REPORT_COLORS_PER_STATUS = True

    Default::

        False


Use timers to receive alerts for your reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tip::
  - It is possible to enable receiving email alerts for reports that have remained in the same status for too long.
  - For instance, I can create two report statuses "To program" with timer days set to 10 and "Programmed" with timer days set to 0.
  - If a report has had status "To program" for 10 days, an email alert will be sent. If its status is changed to "Programmed" within these 10 days, this will cancel the alert.
  - The email alert will be sent to the assigned user for this report, or to managers (setting `MANAGERS`) if there is no assigned user.

**To enable the alerts :**

- Go to the Configuration module and set "Timer days" to some integer other than 0 in relevant statuses (`/admin/feedback/reportstatus/`)

- Select the "Uses timers" checkbox on reports that you wish to receive alerts for (in report update form)

- Make sure to run this commands daily to send email alerts and clear obsolete timers (thanks to `cron` for instance) :

.. code-block:: python

    geotrek check_timers


Anonymize feedback reports
~~~~~~~~~~~~~~~~~~~~~~~~~~

To be compliant to GDPR, you cannot keep personnal data infinitely,
and should notice your users on how many time you keep their email.

A Django command is available to anonymize reports, by default older
than 365 days.

.. code-block:: bash

    geotrek erase_emails

Or if you want to erase emails for reports older than 90 days

.. code-block:: bash

    geotrek erase_emails --days 90


Attachments
-----------

View attachments in the browser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: MAPENTITY_CONFIG for medias

    Attached files are downloaded by default by browser, with the following line, files will be opened in the browser :

    Example::

        MAPENTITY_CONFIG['SERVE_MEDIA_AS_ATTACHMENT'] = False

    Default::

        True

Resizing uploaded pictures
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: PAPERCLIP_RESIZE_ATTACHMENTS_ON_UPLOAD

    Attached pictures can be resized at upload by enabling this parameter :

    Example::

        PAPERCLIP_RESIZE_ATTACHMENTS_ON_UPLOAD = True

    Default::

        False


These corresponding height/width parameters can be overriden to select resized image size:

.. code-block:: python

    PAPERCLIP_MAX_ATTACHMENT_WIDTH = 1280
    PAPERCLIP_MAX_ATTACHMENT_HEIGHT = 1280


Prohibit usage of big pictures and small width / height
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: PAPERCLIP_MAX_BYTES_SIZE_IMAGE

    If you want to prohibit the usage of heavy pictures:

    Example::

        PAPERCLIP_MAX_BYTES_SIZE_IMAGE = 50000 # Bytes

If you want to prohibit the usage of small pictures in pixels:

.. code-block:: python

    PAPERCLIP_MIN_IMAGE_UPLOAD_WIDTH = 100
    PAPERCLIP_MIN_IMAGE_UPLOAD_HEIGHT = 100

These three settings will also not allow downloading images from the parsers.


Prohibit usage of certain file types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Paperclip will only accept attachment files matching a list of allowed extensions.
Here is the default value for this setting, which you can extend if needed:

.. code-block:: python

    PAPERCLIP_ALLOWED_EXTENSIONS = [
        'jpeg',
        'jpg',
        'mp3',
        'mp4',
        'odt',
        'pdf',
        'png',
        'svg',
        'txt',
        'gif',
        'tiff',
        'tif',
        'docx',
        'webp',
        'bmp',
        'flac',
        'mpeg',
        'doc',
        'ods',
        'gpx',
        'xls',
        'xlsx',
        'odg',
    ]

It will verify that the mimetype of the file matches the extension. 

.. envvar:: PAPERCLIP_EXTRA_ALLOWED_MIMETYPES

    You can add extra allowed mimetypes for a given extension with the following syntax:

    Example::

        PAPERCLIP_EXTRA_ALLOWED_MIMETYPES['gpx'] = ['text/xml']

.. envvar:: PAPERCLIP_ALLOWED_EXTENSIONS

    You can also entirely deactivate these checks with the following:

    Example::

        PAPERCLIP_ALLOWED_EXTENSIONS = None

.. note::

  These two settings will also not allow downloading images from the parsers.


Interface
---------

Configure columns displayed in lists views and exports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each module, use the following syntax to configure columns to display in the main table.

.. code-block:: python

    COLUMNS_LISTS['<module>_view'] = ['list', 'of', 'columns']


For each module, use the following syntax to configure columns to export as CSV or SHP.

.. code-block:: python

    COLUMNS_LISTS['<module>_export'] = ['list', 'of', 'columns']

Another setting exists to enable a more detailed export of jobs costs in the interventions module. When enabling this settings, interventions list exports will contain a new column for each job's total cost.

.. envvar:: ENABLE_JOBS_COSTS_DETAILED_EXPORT

    Enable a more detailed export

    Example::

        ENABLE_JOBS_COSTS_DETAILED_EXPORT = True

    Default::

       False

Custom columns available
''''''''''''''''''''''''

A (nearly?) exhaustive list of attributes available for display and export as columns in each module.

.. code-block:: python

    COLUMNS_LISTS["path_view"] = [
        "length_2d",
        "valid",
        "structure",
        "visible",
        "min_elevation",
        "max_elevation",
        "date_update",
        "date_insert",
        "stake",
        "networks",
        "comments",
        "departure",
        "arrival",
        "comfort",
        "source",
        "usages",
        "draft",
        "trails",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["trail_view"] = [
        "departure",
        "arrival",
        "category",
        "length",
        "structure",
        "min_elevation",
        "max_elevation",
        "date_update",
        "length_2d",
        "date_insert",
        "comments",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["landedge_view"] = [
        "eid",
        "min_elevation",
        "max_elevation",
        "date_update",
        "length_2d",
        "date_insert",
        "owner",
        "agreement",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["circulationedge_view"] = [
        "eid",
        "min_elevation",
        "max_elevation",
        "date_update",
        "length_2d",
        "date_insert",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["physicaledge_view"] = [
        "eid",
        "date_insert",
        "date_update",
        "length",
        "length_2d",
        "min_elevation",
        "max_elevation",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["competenceedge_view"] = [
        "eid",
        "date_insert",
        "date_update",
        "length",
        "length_2d",
        "min_elevation",
        "max_elevation",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["signagemanagementedge_export"] = [
        "eid",
        "date_insert",
        "date_update",
        "length",
        "length_2d",
        "min_elevation",
        "max_elevation",
        "uuid",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["workmanagementedge_export"] = [
        "eid",
        "date_insert",
        "date_update",
        "length",
        "length_2d",
        "min_elevation",
        "max_elevation",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["infrastructure_view"] = [
        "condition",
        "cities",
        "structure",
        "type",
        "description",
        "accessibility",
        "date_update",
        "date_insert",
        "implantation_year",
        "usage_difficulty",
        "maintenance_difficulty",
        "published",
        "uuid",
        "eid",
        "provider",
        "access",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["signage_view"] = [
        "code",
        "type",
        "condition",
        "structure",
        "description",
        "date_update",
        "date_insert",
        "implantation_year",
        "printed_elevation",
        "coordinates",
        "sealing",
        "access",
        "manager",
        "published",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["intervention_view"] = [
        "begin_date",
        "end_date",
        "type",
        "target",
        "status",
        "stake",
        "structure",
        "subcontracting",
        "status",
        "disorders",
        "length",
        "material_cost",
        "min_elevation",
        "max_elevation",
        "heliport_cost",
        "contractor_cost",
        "date_update",
        "date_insert",
        "description",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["project_view"] = [
        "structure",
        "begin_year",
        "end_year",
        "constraint",
        "global_cost",
        "type",
        "date_update",
        "domain",
        "contractors",
        "project_owner",
        "project_manager",
        "founders",
        "date_insert",
        "comments",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["trek_view"] = [
        "structure",
        "departure",
        "arrival",
        "duration",
        "description_teaser",
        "description",
        "gear",
        "route",
        "difficulty",
        "ambiance",
        "access",
        "accessibility_infrastructure",
        "advised_parking",
        "parking_location",
        "public_transport",
        "themes",
        "practice",
        "min_elevation",
        "max_elevation",
        "length_2d",
        "date_update",
        "date_insert",
        "accessibilities",
        "accessibility_advice",
        "accessibility_covering",
        "accessibility_exposure",
        "accessibility_level",
        "accessibility_signage",
        "accessibility_slope",
        "accessibility_width",
        "ratings_description",
        "ratings",
        "points_reference",
        "source",
        "reservation_system",
        "reservation_id",
        "portal",
        "uuid",
        "eid",
        "eid2",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["poi_view"] = [
        "structure",
        "description",
        "type",
        "min_elevation",
        "date_update",
        "date_insert",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["service_view"] = [
        "structure",
        "min_elevation",
        "type",
        "length_2d",
        "date_update",
        "date_insert",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["dive_view"] = [
        "structure",
        "description_teaser",
        "description",
        "owner",
        "practice",
        "departure",
        "disabled_sport",
        "facilities",
        "difficulty",
        "levels",
        "depth",
        "advice",
        "themes",
        "source",
        "portal",
        "date_update",
        "date_insert",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["touristic_content_view"] = [
        "structure",
        "description_teaser",
        "description",
        "category",
        "contact",
        "email",
        "website",
        "practical_info",
        "accessibility",
        "label_accessibility",
        "type1",
        "type2",
        "source",
        "reservation_system",
        "reservation_id",
        "date_update",
        "date_insert",
        "uuid",
        "eid",
        "provider"
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["touristic_event_view"] = [
        "structure",
        "themes",
        "description_teaser",
        "description",
        "meeting_point",
        "start_time",
        "end_time",
        "duration",
        "begin_date",
        "contact",
        "email",
        "website",
        "end_date",
        "organizers",
        "speaker",
        "type",
        "accessibility",
        "capacity",
        "portal",
        "source",
        "practical_info",
        "target_audience",
        "booking",
        "date_update",
        "date_insert",
        "uuid",
        "eid",
        "provider",
        "bookable",
        "cancelled",
        "cancellation_reason"
        "place",
        'preparation_duration',
        'intervention_duration',
        'price',
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["feedback_view"] = [
        "email",
        "comment",
        "activity",
        "category",
        "problem_magnitude",
        "status",
        "related_trek",
        "uuid",
        "eid",
        "external_eid",
        "locked",
        "origin"
        "date_update",
        "date_insert",
        "created_in_suricate",
        "last_updated_in_suricate",
        "assigned_user",
        "uses_timers",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["sensitivity_view"] = [
        "structure",
        "species",
        "published",
        "publication_date",
        "contact",
        "pretty_period",
        "category",
        "pretty_practices",
        "description",
        "date_update",
        "date_insert",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["outdoor_site_view"] = [
        "structure",
        "name",
        "practice",
        "description",
        "description_teaser",
        "ambiance",
        "advice",
        "accessibility",
        "period",
        "labels",
        "themes",
        "portal",
        "source",
        "information_desks",
        "web_links",
        "eid",
        "orientation",
        "wind",
        "ratings",
        "managers",
        "type",
        "description",
        "description_teaser",
        "ambiance",
        "period",
        "orientation",
        "wind",
        "labels",
        "themes",
        "portal",
        "source",
        "managers",
        "min_elevation",
        "date_insert",
        "date_update",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["outdoor_course_view"] = [
        "structure",
        "name",
        "parent_sites",
        "description",
        "advice",
        "equipment",
        "accessibility",
        "eid",
        "height",
        "ratings",
        "gear",
        "duration"
        "ratings_description",
        "type",
        "points_reference",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["path_export"] = [
        "structure",
        "valid",
        "visible",
        "name",
        "comments",
        "departure",
        "arrival",
        "comfort",
        "source",
        "stake",
        "usages",
        "networks",
        "date_insert",
        "date_update",
        "length_2d",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["trail_export"] = [
        "structure",
        "name",
        "comments",
        "departure",
        "arrival",
        "category",
        "certifications",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["landedge_export"] = [
        "eid",
        "land_type",
        "owner",
        "agreement",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["circulationedge_export"] = [
        "eid",
        "circulation_type",
        "authorization_type",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["physicaledge_export"] = [
        "eid",
        "physical_type",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["competenceedge_export"] = [
        "eid",
        "organization",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["signagemanagementedge_export"] = [
        "eid",
        "organization",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["workmanagementedge_export"] = [
        "eid",
        "organization",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "length_2d",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["infrastructure_export"] = [
        "name",
        "type",
        "condition",
        "access",
        "description",
        "accessibility",
        "implantation_year",
        "published",
        "publication_date",
        "structure",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "usage_difficulty",
        "maintenance_difficulty"
        "uuid",
        "eid",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["signage_export"] = [
        "structure",
        "name",
        "code",
        "type",
        "condition",
        "description",
        "implantation_year",
        "published",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "lat_value",
        "lng_value",
        "printed_elevation",
        "sealing",
        "access",
        "manager",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "uuid",
        "eid",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["intervention_export"] = [
        "name",
        "begin_date",
        "end_date",
        "type",
        "target",
        "status",
        "stake",
        "disorders",
        "total_manday",
        "project",
        "subcontracting",
        "width",
        "height",
        "length",
        "area",
        "structure",
        "description",
        "date_insert",
        "date_update",
        "material_cost",
        "heliport_cost",
        "contractor_cost",
        "total_cost_mandays",
        "total_cost",
        "cities",
        "districts",
        "areas",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["project_export"] = [
        "structure",
        "name",
        "period",
        "type",
        "domain",
        "constraint",
        "global_cost",
        "interventions",
        "interventions_total_cost",
        "comments",
        "contractors",
        "project_owner",
        "project_manager",
        "founders",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["trek_export"] = [
        "eid",
        "eid2",
        "structure",
        "name",
        "departure",
        "arrival",
        "duration",
        "duration_pretty",
        "description",
        "description_teaser",
        "gear",
        "networks",
        "advice",
        "ambiance",
        "difficulty",
        "information_desks",
        "themes",
        "practice",
        "accessibilities",
        "accessibility_advice",
        "accessibility_covering",
        "accessibility_exposure",
        "accessibility_level",
        "accessibility_signage",
        "accessibility_slope",
        "accessibility_width",
        "ratings_description",
        "ratings",
        "access",
        "route",
        "public_transport",
        "advised_parking",
        "web_links",
        "labels",
        "accessibility_infrastructure",
        "parking_location",
        "points_reference",
        "children",
        "parents",
        "pois",
        "review",
        "published",
        "publication_date",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "source",
        "portal",
        "length_2d",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["poi_export"] = [
        "structure",
        "eid",
        "name",
        "type",
        "description",
        "treks",
        "review",
        "published",
        "publication_date",
        "structure",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["service_export"] = [
        "eid",
        "type",
        "length",
        "ascent",
        "descent",
        "min_elevation",
        "max_elevation",
        "slope",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["dive_export"] = [
        "eid",
        "structure",
        "name",
        "departure",
        "description",
        "description_teaser",
        "advice",
        "difficulty",
        "levels",
        "themes",
        "practice",
        "disabled_sport",
        "published",
        "publication_date",
        "date_insert",
        "date_update",
        "areas",
        "source",
        "portal",
        "review",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["touristic_content_export"] = [
        "structure",
        "eid",
        "name",
        "category",
        "type1",
        "type2",
        "description_teaser",
        "description",
        "themes",
        "contact",
        "email",
        "website",
        "practical_info",
        "accessibility",
        "label_accessibility",
        "review",
        "published",
        "publication_date",
        "source",
        "portal",
        "date_insert",
        "date_update",
        "cities",
        "districts",
        "areas",
        "approved",
        "uuid",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["touristic_event_export"] = [
        "structure",
        "eid",
        "name",
        "type",
        "description_teaser",
        "description",
        "themes",
        "begin_date",
        "end_date",
        "duration",
        "meeting_point",
        "start_time",
        "end_time",
        "contact",
        "email",
        "website",
        "organizers",
        "speaker",
        "accessibility",
        "capacity",
        "booking",
        "target_audience",
        "practical_info",
        "date_insert",
        "date_update",
        "source",
        "portal",
        "review",
        "published",
        "publication_date",
        "cities",
        "districts",
        "areas",
        "approved",
        "uuid",
        "provider",
        "bookable",
        "cancelled",
        "cancellation_reason"
        "place",
        'preparation_duration',
        'intervention_duration',
        'price',
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["feedback_export"] = [
        "comment",
        "activity",
        "category",
        "problem_magnitude",
        "status",
        "related_trek",
        "uuid",
        "eid",
        "external_eid",
        "locked",
        "origin"
        "date_update",
        "date_insert",
        "created_in_suricate",
        "last_updated_in_suricate",
        "assigned_user",
        "uses_timers",
        "provider",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["sensitivity_export"] = [
        "species",
        "published",
        "description",
        "contact",
        "pretty_period",
        "pretty_practices",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["outdoor_site_export"] = [
        "structure",
        "name",
        "practice",
        "description",
        "description_teaser",
        "ambiance",
        "advice",
        "accessibility",
        "period",
        "labels",
        "themes",
        "portal",
        "source",
        "information_desks",
        "web_links",
        "eid",
        "orientation",
        "wind",
        "ratings",
        "managers",
        "type",
        "description",
        "description_teaser",
        "ambiance",
        "period",
        "orientation",
        "wind",
        "labels",
        "themes",
        "portal",
        "source",
        "managers",
        "min_elevation",
        "date_insert",
        "date_update",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]
    COLUMNS_LISTS["outdoor_course_export"] = [
        "structure",
        "name",
        "parent_sites",
        "description",
        "advice",
        "equipment",
        "accessibility",
        "eid",
        "height",
        "ratings",
        "gear",
        "duration"
        "ratings_description",
        "type",
        "points_reference",
        "uuid",
        "last_author",
        "creator",
        "authors",
    ]


Configure form fields in creation views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: HIDDEN_FORM_FIELDS

    For each module, use the following syntax to configure fields to hide in the creation form.

    Example::

        HIDDEN_FORM_FIELDS['<module>'] = ['list', 'of', 'fields']


Hideable form fields
''''''''''''''''''''

An exhaustive list of form fields hideable in each module.

.. code-block:: python

    HIDDEN_FORM_FIELDS["path"] = [
            "departure",
            "name",
            "stake",
            "comfort",
            "arrival",
            "comments",
            "source",
            "networks",
            "usages",
            "valid",
            "draft",
            "reverse_geom",
        ],
    HIDDEN_FORM_FIELDS["trek"] = [
            "structure",
            "name",
            "review",
            "published",
            "labels",
            "departure",
            "arrival",
            "duration",
            "difficulty",
            "gear",
            "route",
            "ambiance",
            "access",
            "description_teaser",
            "description",
            "points_reference",
            "accessibility_infrastructure",
            "advised_parking",
            "parking_location",
            "public_transport",
            "advice",
            "themes",
            "networks",
            "practice",
            "accessibilities",
            "accessibility_advice",
            "accessibility_covering",
            "accessibility_exposure",
            "accessibility_level",
            "accessibility_signage",
            "accessibility_slope",
            "accessibility_width",
            "web_links",
            "information_desks",
            "source",
            "portal",
            "children_trek",
            "eid",
            "eid2",
            "ratings",
            "ratings_description",
            "reservation_system",
            "reservation_id",
            "pois_excluded",
            "hidden_ordered_children",
        ],
    HIDDEN_FORM_FIELDS["trail"] = [
            "departure",
            "arrival",
            "comments",
            "category",
        ],
    HIDDEN_FORM_FIELDS["landedge"] = [
            "owner",
            "agreement"
        ],
    HIDDEN_FORM_FIELDS["infrastructure"] = [
            "condition",
            "access",
            "description",
            "accessibility",
            "published",
            "implantation_year",
            "usage_difficulty",
            "maintenance_difficulty"
        ],
    HIDDEN_FORM_FIELDS["signage"] = [
            "condition",
            "description",
            "published",
            "implantation_year",
            "code",
            "printed_elevation",
            "manager",
            "sealing",
            "access"
        ],
    HIDDEN_FORM_FIELDS["intervention"] = [
            "disorders",
            "description",
            "type",
            "subcontracting",
            "end_date",
            "length",
            "width",
            "height",
            "stake",
            "project",
            "material_cost",
            "heliport_cost",
            "contractor_cost",
        ],
    HIDDEN_FORM_FIELDS["project"] = [
            "type",
            "domain",
            "end_year",
            "constraint",
            "global_cost",
            "comments",
            "project_owner",
            "project_manager",
            "contractors",
        ],
    HIDDEN_FORM_FIELDS["site"] = [
            "parent",
            "review",
            "published",
            "practice",
            "description_teaser",
            "description",
            "ambiance",
            "advice",
            "period",
            "orientation",
            "wind",
            "labels",
            "themes",
            "information_desks",
            "web_links",
            "portal",
            "source",
            "managers",
            "eid"
        ],
    HIDDEN_FORM_FIELDS["course"] = [
            "review",
            "published",
            "description",
            "advice",
            "equipment",
            "accessibility",
            "height",
            "children_course",
            "eid",
            "gear",
            "duration"
            "ratings_description",
        ]
    HIDDEN_FORM_FIELDS["poi"] = [
            "review",
            "published",
            "description",
            "eid",
        ],
    HIDDEN_FORM_FIELDS["service"] = [
            "eid",
        ],
    HIDDEN_FORM_FIELDS["dive"] = [
            "review",
            "published",
            "practice",
            "advice",
            "description_teaser",
            "description",
            "difficulty",
            "levels",
            "themes",
            "owner",
            "depth",
            "facilities",
            "departure",
            "disabled_sport",
            "source",
            "portal",
            "eid",
        ],
    HIDDEN_FORM_FIELDS["touristic_content"] = [
            'label_accessibility'
            'type1',
            'type2',
            'review',
            'published',
            'accessibility',
            'description_teaser',
            'description',
            'themes',
            'contact',
            'email',
            'website',
            'practical_info',
            'approved',
            'source',
            'portal',
            'eid',
            'reservation_system',
            'reservation_id'
        ],
    HIDDEN_FORM_FIELDS["touristic_event"] = [
            'review',
            'published',
            'description_teaser',
            'description',
            'themes',
            'end_date',
            'duration',
            'meeting_point',
            'start_time',
            'end_time',
            'contact',
            'email',
            'website',
            'organizers',
            'speaker',
            'type',
            'accessibility',
            'capacity',
            'booking',
            'target_audience',
            'practical_info',
            'approved',
            'source',
            'portal',
            'eid',
            "bookable",
            'cancelled',
            'cancellation_reason'
            'place',
            'preparation_duration',
            'intervention_duration',
            'price'
        ],
    HIDDEN_FORM_FIELDS["report"] = [
            "email",
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "locked",
            "uid",
            "origin",
            "assigned_user",
            "uses_timers"
        ],
    HIDDEN_FORM_FIELDS["sensitivity_species"] = [
            "contact",
            "published",
            "description",
        ],
    HIDDEN_FORM_FIELDS["sensitivity_regulatory"] = [
            "contact",
            "published",
            "description",
            "pictogram",
            "elevation",
            "url",
            "period01",
            "period02",
            "period03",
            "period04",
            "period05",
            "period06",
            "period07",
            "period08",
            "period09",
            "period10",
            "period11",
            "period12",
        ],
    HIDDEN_FORM_FIELDS["blade"] = [
            "condition",
            "color",
        ],
    HIDDEN_FORM_FIELDS["report"] = [
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "locked",
            "uid",
            "origin"
        ],
    HIDDEN_FORM_FIELDS["circulationedge"] = [
        ]

.. note::

  ``assigned_user`` is hidden by default in ``HIDDEN_FORM_FIELDS["report"]``, it is possible to force it to appear using ``HIDDEN_FORM_FIELDS["report"] = []``.


Configure form fields required or needed for review or publication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set ``error_on_publication`` to avoid publication without completeness fields
and ``error_on_review`` if you want this fields to be required before sending to review.

.. envvar:: COMPLETENESS_LEVEL

    Configure completeness level

    Example::

        COMPLETENESS_LEVEL = 'warning'

.. envvar:: COMPLETENESS_FIELDS

    For each module, configure fields to be needed or required on review or publication

    Example::

        COMPLETENESS_FIELDS = {
        'trek': ['practice', 'departure', 'duration', 'difficulty', 'description_teaser'],
        'dive': ['practice', 'difficulty', 'description_teaser'],
        }

Edition
-------

WYSIWYG editor configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Text form fields are enhanced using `TinyMCE <http://tinymce.com>`_.

Its configuration can be customized using advanced settings (see above paragraph).

.. envvar:: TINYMCE_DEFAULT_CONFIG

    For example, in order to control which buttons are to be shown, and which tags are to be kept when cleaning-up, add this bloc :

    Example::

        TINYMCE_DEFAULT_CONFIG = {
        'theme_advanced_buttons1': 'bold,italic,forecolor,separator,code',
        'valid_elements': "img,p,a,em/i,strong/b",
        }

.. note::

  - This will apply to all text fields.
  - For more information on configuration entries available, please refer to the official documentation of *TinyMCE version 3*.


Max characters count
~~~~~~~~~~~~~~~~~~~~

.. envvar:: MAPENTITY_CONFIG for characters

    Add ``MAX_CHARACTERS_BY_FIELD`` setting to be able to define a maximum number of characters for text fields.

    Example::

        MAPENTITY_CONFIG['MAX_CHARACTERS_BY_FIELD'] = {
           "tourism_touristicevent": [{'field': 'description_teaser_fr', 'value': 50}, {'field': 'accessibility_fr', 'value': 25}],
           "trekking_trek": [{'field': 'description_teaser_fr', 'value': 150}],
        }

.. note::

  - This will apply to all text fields.
  - See `this issue <https://github.com/GeotrekCE/Geotrek-admin/issues/2901>`_ for details.


Copyright on pictures
~~~~~~~~~~~~~~~~~~~~~


.. envvar:: THUMBNAIL_COPYRIGHT_FORMAT

    If you want copyright added to your pictures, change this parameter like so :

    Example::

        THUMBNAIL_COPYRIGHT_FORMAT = "{title} {author}"

.. note::

  - This will apply to all text fields.
  - For more information on configuration entries available, please refer to the official documentation of *TinyMCE version 3*.


You can also add ``{legend}``: ``"{title}-:-{author}-:-{legend}"``

.. envvar:: THUMBNAIL_COPYRIGHT_SIZE

    Change the size of thumbnail

    Example::

        THUMBNAIL_COPYRIGHT_SIZE = 15


Facebook configuration
~~~~~~~~~~~~~~~~~~~~~~

When a content is shared to Facebook in Geotrek-rando V2,
it needs static html files built by synchronization (thanks to option ``--rando-url``).

In Facebook developper dashboard, create a Facebook app dedicated to Geotrek-rando and activate it.

.. image:: /images/facebookappid.png


.. envvar:: FACEBOOK_APP_ID

    In ``custom.py`` set Facebook App ID:

    Example::

        FACEBOOK_APP_ID = '<your Facebook AppID>'

**You can also override these settings:**

.. code-block:: python

    FACEBOOK_IMAGE = '/images/logo-geotrek.png'
    FACEBOOK_IMAGE_WIDTH = 200
    FACEBOOK_IMAGE_HEIGHT = 200


Override translations
~~~~~~~~~~~~~~~~~~~~~

Translations are managed by https://weblate.makina-corpus.net/ where you can contribute.
But you can also override default translation files available in each module
(for example those from trekking module available in ``/opt/geotrek-admin/lib/python3.6/site-packages/geotrek/trekking/locale/fr/LC_MESSAGES/django.po``).

Don't edit these default files, use them to find which words you want to override.

**Create the custom translations destination folder:**

- Create a ``django.po`` file in ``/opt/geotrek-admin/var/conf/extra_locale`` directory.
- You can do one folder and one ``django.po`` file for each language (example ``/opt/geotrek-admin/var/conf/extra_locale/fr/LC_MESSAGES/django.po`` for French translation overriding)

Override the translations that you want in these files.

**Example of content for the French translation overriding:**

.. code-block:: python

    # MY FRENCH CUSTOM TRANSLATION
    # Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
    # This file is distributed under the same license as the PACKAGE package.
    # FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
    #
    msgid ""
    msgstr ""
    "Report-Msgid-Bugs-To: \n"
    "POT-Creation-Date: 2018-11-15 15:32+0200\n"
    "PO-Revision-Date: 2018-11-15 15:33+0100\n"
    "Last-Translator: \n"
    "Language-Team: LANGUAGE <LL@li.org>\n"
    "MIME-Version: 1.0\n"
    "Content-Type: text/plain; charset=UTF-8\n"
    "Content-Transfer-Encoding: 8bit\n"
    "Project-Id-Version: PACKAGE VERSION\n"
    "Plural-Forms: nplurals=2; plural=(n > 1);\n"
    "Project-Id-Version: \n"
    "X-Generator: Poedit 1.5.4\n"

    msgid "City"
    msgstr "Région"

    msgid "District"
    msgstr "Pays"

**Apply changes (French translation in this example):**

.. code-block:: bash

    cd /opt/geotrek-admin/var/conf/extra_locale
    sudo chown geotrek. fr/LC_MESSAGES/
    sudo geotrek compilemessages
    sudo service geotrek restart


Override public PDF templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PDF are generated from HTML templates, using `Django templating <https://docs.djangoproject.com/en/1.11/ref/templates/>`_.
Treks, touristic contents, touristic events, outdoor sites and courses can be exported in PDF files.

- Treks : ``geotrek/trekking/templates/trekking/trek_public_pdf.html``
- Touristic contents : ``geotrek/tourism/templates/tourism/touristiccontent_public_pdf.html``
- Touristic events : ``geotrek/tourism/templates/tourism/touristicevent_public_pdf.html``
- Outdoor sites : ``geotrek/outdoor/templates/outdoor/site_public_pdf.html``
- Outdoor courses : ``geotrek/outdoor/templates/outdoor/course_public_pdf.html``

Overriden templates have to be located in ``/opt/geotrek-admin/var/conf/extra_templates/<appname>``, with ``<appname>`` = ``trekking`` or ``tourism``.
To override trekking PDF for example, copy the file ``geotrek/trekking/templates/trekking/trek_public_pdf.html``
to ``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``. Or add inside your file::

    {% extends "trekking/trek_public_pdf.html" %}


These templates derive from base templates, which content is organized in blocks.
To override for example the description block of trek PDF, copy and change the ``{% block description }…{% endblock description %}``
in your ``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``.

It is also possible to use color defined for practice for pictogram by adding in your
``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html`` file::

    {% block picto_attr %}style="background-color: {{ object.practice.color }};"{% endblock picto_attr %}

CSS can be overriden like html templates: copy them to ``var/media/templates/trekking/`` or ``var/media/templates/tourism/`` folder
``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.css`` for example.

**You can also create a template for each portal.**

Add a folder ``portal_{id_portal}`` (portal ids are located in the portal url path ``/admin/common/targetportal/{id_portal}``) in
``/opt/geotrek-admin/var/conf/extra_templates/<appname>``, as the first template, and add at the top of your file:

::

    {% extends "trekking/trek_public_pdf.html" %}


The template for a specific portal will use the modification made on the overriden template in  ``/opt/geotrek-admin/var/conf/extra_templates/<appname>``
( except if you change specific  block)

.. note::

  This modification is not mandatory, if you have multiple portal and you want to modify the template of only one portal, you create one folder for this specific portal

**You might need to use your own images in the PDF templates.**

Add your own images in ``/opt/geotrek-admin/var/conf/extra_static/images/``.

You can then use these images in your PDF templates with ``{% static 'images/file.jpg' %}``, after adding ``{% load static %}`` at the top of the file.

Example of a customised template (``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``) with a customised logo and URL:

::

    {% extends "trekking/trek_public_pdf.html" %}
    {% load static %}

    {% block logo %}
       <img src="{% static 'images/logo-gte.jpg' %}" alt="Grand tour des Ecrins">
    {% endblock %}
    {% block url %}
       <div class="main">Grand tour des Ecrins</div>
       <div class="geo"><a href="https://www.grand-tour-ecrins.fr">grand-tour-ecrins.fr</a></div>
    {% endblock url %}

.. note::

  The default template may change in the future versions. You will be in charge of porting the modification to your copy.

Test your modifications by exporting a trek or a content to PDF from Geotrek-admin application.


PDF as booklet
~~~~~~~~~~~~~~

.. envvar:: USE_BOOKLET_PDF

    Use booklet for PDF

    Example::

        USE_BOOKLET_PDF = True

    Default::

        False

.. note::

  - During the synchro, pois details will be removed, and the pages will be merged.
  - It is possible to customize the pdf, with trek_public_booklet_pdf.html.

Custom font in public document template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to use custom fonts in trek PDF, it is necessary to install the
font files on the server.

*Microsoft* fonts like *Arial* and *Verdana* can be installed via the package
manager:

::

    sudo apt-get install ttf-mscorefonts-installer

For specific fonts, copy the ``.ttf`` (or ``.otf``) files into the folder
``/usr/local/share/fonts/custom/`` as root, and run the following command:

.. code-block:: bash

    fc-cache

For more information, check out Ubuntu documentation.


Custom colors in public document template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: MAPENTITY_CONFIG for custom colors in PDF

    Trek export geometries are translucid red by default. In order to control the apparence of objects in public trek PDF exports, use the following setting:

    Example::

        MAPENTITY_CONFIG['MAP_STYLES']['print']['path'] = {'weight': 3}

See *Leaflet* reference documentation for detail about layers apparence.


Primary color in PDF templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: PRIMARY_COLOR

    You can override ``PRIMARY_COLOR`` to change emphase text in PDF export.

    Example::

        PRIMARY_COLOR = "#7b8c12"

.. note::

  Beware of contrast, white colour is used for text so we advise you to avoid light colour.


Custom logos
~~~~~~~~~~~~

You might also need to deploy logo images in the following places :

* ``var/conf/extra_static/images/favicon.png``
* ``var/conf/extra_static/images/logo-login.png``
* ``var/conf/extra_static/images/logo-header.png``


Settings for Geotrek-rando
--------------------------

.. _distances:

Distances
~~~~~~~~~

.. envvar:: TOURISM_INTERSECTION_MARGIN

   Distance to which tourist contents, tourist events, treks, pois, services will be displayed

    Example::

        TOURISM_INTERSECTION_MARGIN = 500 # meters

    Default::

        500

.. note:: 
  This distance can be changed by practice for treks in the admin.

.. envvar:: DIVING_INTERSECTION_MARGIN

   Distance to which dives will be displayed.

    Example::

        DIVING_INTERSECTION_MARGIN = 500 # meters

    Default::

        500


Limits
~~~~~~

.. envvar:: TREK_EXPORT_POI_LIST_LIMIT

   Limit of the number of POIs on treks pdf.

    Example::

        TREK_EXPORT_POI_LIST_LIMIT = 14

.. note::

  ``14`` is already a huge amount of POI, but it's possible to add more

.. envvar:: TREK_EXPORT_INFORMATION_DESK_LIST_LIMIT

   Limit of the number of information desks on treks pdf.

    Example::

        TREK_EXPORT_INFORMATION_DESK_LIST_LIMIT = 14

.. note::

  You can put ``-1`` if you want all the information desks

Categories
~~~~~~~~~~~

.. envvar:: SPLIT_TREKS_CATEGORIES_BY_PRACTICE

   On the Geotrek-rando V2 website, treks practices will be displayed separately

    Example::

        SPLIT_TREKS_CATEGORIES_BY_PRACTICE = False

    Default::

        True

.. note::

  Field order for each practices in admin will be taken in account

.. envvar:: SPLIT_TREKS_CATEGORIES_BY_ACCESSIBILITY

  On the Geotrek-rando V2 website, accessibilites will be displayed separately

    Example::

        SPLIT_TREKS_CATEGORIES_BY_ACCESSIBILITY = False

    Default::

        True

.. envvar:: SPLIT_TREKS_CATEGORIES_BY_ITINERANCY

  On the Geotrek-rando V2 website, if a trek has a children it will be displayed separately

    Example::

        SPLIT_TREKS_CATEGORIES_BY_ITINERANCY = False

    Default::

        True

.. envvar:: SPLIT_DIVES_CATEGORIES_BY_PRACTICE

  On the Geotrek-rando V2 website, dives practices will be displayed separately


    Example::

        SPLIT_DIVES_CATEGORIES_BY_PRACTICE = True

    Default::

        False

.. envvar:: HIDE_PUBLISHED_TREKS_IN_TOPOLOGIES

  On the Geotrek-rando V2 website, treks near other are hidden


    Example::

        HIDE_PUBLISHED_TREKS_IN_TOPOLOGIES = False

    Default::

        True

.. envvar:: TREK_WITH_POIS_PICTURES

  It enables correlated pictures on Geotrek-rando V2 to be displayed in the slideshow


    Example::

        TREK_WITH_POIS_PICTURES = False

    Default::

        True

.. envvar:: ONLY_EXTERNAL_PUBLIC_PDF

  On Geotrek-rando V2 website, only PDF imported with filetype "Topoguide"will be used and not autogenerated.

    Example::

        ONLY_EXTERNAL_PUBLIC_PDF = False

    Default::

        True

**Order of all the objects without practices on Geotrek-rando website** :

.. code-block:: python

    TREK_CATEGORY_ORDER = 1
    ITINERANCY_CATEGORY_ORDER = 2
    DIVE_CATEGORY_ORDER = 10
    TOURISTIC_EVENT_CATEGORY_ORDER = 99


.. note:: 
  - All the settings about order are the order inside Geotrek-rando website.
  - Practices of diving, treks and categories of touristic contents are taken in account


Settings for Geotrek-mobile
---------------------------

.. envvar:: SYNC_MOBILE_ROOT

  Path on your server where the datas for mobile will be saved.

    Example::

        SYNC_MOBILE_ROOT = os.path.join(VAR_DIR, 'mobile')

.. note:: 
  - If you want to modify it, do not forget to import os at the top of the file.
  - Check `import Python <https://docs.python.org/3/reference/import.html>`_ , if you need any information

.. envvar:: SYNC_MOBILE_OPTIONS

  Options of the sync_mobile command.

    Example::

        SYNC_MOBILE_OPTIONS = {'skip_tiles': False}

    Default::

        True

.. envvar:: MOBILE_NUMBER_PICTURES_SYNC

  Number max of pictures that will be displayed and synchronized for each object (trek, POI, etc.) in the mobile app.

    Example::

        MOBILE_NUMBER_PICTURES_SYNC = 3

.. envvar:: MOBILE_TILES_URL

  URL's Tiles used for the mobile.

    Example with OpenTopoMap::

        MOBILE_TILES_URL = ['https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png']

    Example with IGN::

        MOBILE_TILES_URL = ['https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}']

.. envvar:: MOBILE_LENGTH_INTERVALS

  Intervals of the mobile for the length filter.

    Example::

        MOBILE_LENGTH_INTERVALS =  [
        {"id": 1, "name": "< 10 km", "interval": [0, 9999]},
        {"id": 2, "name": "10 - 30", "interval": [9999, 29999]},
        {"id": 3, "name": "30 - 50", "interval": [30000, 50000]},
        {"id": 4, "name": "> 50 km", "interval": [50000, 999999]}
        ]

.. note::

  - Interval key is in meters.
  - You can add new intervals

.. envvar:: MOBILE_ASCENT_INTERVALS

  Intervals of the mobile for the ascent filter.

    Example::

        MOBILE_ASCENT_INTERVALS = [
        {"id": 1, "name": "< 300 m", "interval": [0, 299]},
        {"id": 2, "name": "300 - 600", "interval": [300, 599]},
        {"id": 3, "name": "600 - 1000", "interval": [600, 999]},
        {"id": 4, "name": "> 1000 m", "interval": [1000, 9999]}
        ]

.. note::

  Do the same as above

.. envvar:: MOBILE_DURATION_INTERVALS

  Intervals of the mobile for the duration filter.

    Example::

        MOBILE_DURATION_INTERVALS = [
        {"id": 1, "name": "< 1 heure", "interval": [0, 1]},
        {"id": 2, "name": "1h - 2h30", "interval": [1, 2.5]},
        {"id": 3, "name": "2h30 - 5h", "interval": [2.5, 5]},
        {"id": 4, "name": "5h - 9h", "interval": [5, 9]},
        {"id": 5, "name": "> 9h", "interval": [9, 9999999]}
        ]

.. note::

  Check ``MOBILE_LENGTH_INTERVALS`` section to use it, here interval correspond to 1 unit of hour

.. envvar:: ENABLED_MOBILE_FILTERS

  List of all the filters enabled on mobile.

    Example::

        ENABLED_MOBILE_FILTERS = [
        'practice',
        'difficulty',
        'duration',
        'ascent',
        'length',
        'themes',
        'route',
        'districts',
        'cities',
        'accessibilities',
        ]

.. note:: 
  Remove any of the filters if you don't want one of them. It's useless to add other one.

