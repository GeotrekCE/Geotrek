.. _map-settings:

===============
Map settings
===============

Leaflet configuration
----------------------

Change or add WMTS tiles layers (IGN, OSM, Mapbox…)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, you have two basemaps layers in your Geotrek-admin (OSM and OpenTopoMap)

You can change or add more basemaps layers like this:

Specify the tiles URLs this way in your custom Django setting file:

Syntax::

    LEAFLET_CONFIG['TILES'] = [('NAME_OF_TILE', 'URL', 'COPYRIGHT'), ...]

.. note:: 
  To use some IGN Geoportail WMTS tiles (Scan25, Scan100, etc.), you may need an API key. You can find more information about this on https://geoservices.ign.fr/services-geoplateforme-diffusion.

.. md-tab-set::
    :name: leaflet-config-tile-tabs

    .. md-tab-item:: Default configuration

        .. code-block:: python

    
                LEAFLET_CONFIG['TILES'] = [
                    (
                        'OpenTopoMap',
                        'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                        {
                            'attribution': 'map data: © <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>; contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | map style: © <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>;)',
                            'maxNativeZoom': 17,
                            'maxZoom': 22
                        }
                    ),
                    (
                        'OpenStreetMap',
                        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        {
                            'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">Contributeurs d\'OpenStreetMap</a>',
                            'maxNativeZoom': 19,
                            'maxZoom': 22
                        }
                    )
                ]
    .. md-tab-item:: Example with IGN and OSM basemaps

         .. code-block:: python

    
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

Map overlays
~~~~~~~~~~~~~~

.. note::
  It is possible to add overlay tiles layer on maps. For example, it can be useful to:
    - Display the cadastral parcels on top of satellite images
    - Display home made layers (*with Tilemill or QGisMapserver for example*).
    - Display the park center borders, traffic maps, IGN BDTopo® or even the Geotrek paths that are marked as invisible in the database!

.. md-tab-set::
    :name: leaflet-config-overlay-tabs

    .. md-tab-item:: Basic example

        You can configure overlays layers like this:

        .. code-block:: python

    
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
    .. md-tab-item:: Advanced example

         .. code-block:: python

    
                LEAFLET_CONFIG['OVERLAYS'] = [
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

Map layers zoom
~~~~~~~~~~~~~~~~

You can define the max_zoom the user can zoom for all tiles.

Example::

    LEAFLET_CONFIG['MAX_ZOOM'] = 19

.. note::
  It can be interesting when your tiles can't go to a zoom. For example OpenTopoMap is 17.

Mapentity configuration
-------------------------

Map layers colors and style
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All layers colors can be customized from the settings. See `Leaflet reference <http://leafletjs.com/reference.html#path>`_ for vectorial layer style.

.. md-tab-set::
    :name: mapentity-config-tabs

    .. md-tab-item:: Default configuration

        See the default values in `geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_ for the complete list of available styles.

        .. code-block:: python

    
                MAPENTITY_CONFIG['MAP_STYLES'] = {
                    'path': {'weight': 2, 'color': '#FF4800', 'opacity': 1.0},
                    'draftpath': {'weight': 5, 'opacity': 1, 'color': 'yellow', 'dashArray': '8, 8'},
                    'city': {'weight': 4, 'color': '#FF9700', 'opacity': 0.3, 'fillOpacity': 0.0},
                    'district': {'weight': 6, 'color': '#FF9700', 'opacity': 0.3, 'fillOpacity': 0.0, 'dashArray': '12, 12'},
                    'restrictedarea': {'weight': 2, 'color': 'red', 'opacity': 0.5, 'fillOpacity': 0.5},
                    'land': {'weight': 4, 'color': 'red', 'opacity': 1.0},
                    'physical': {'weight': 6, 'color': 'red', 'opacity': 1.0},
                    'circulation': {'weight': 6, 'color': 'red', 'opacity': 1.0},
                    'competence': {'weight': 4, 'color': 'red', 'opacity': 1.0},
                    'workmanagement': {'weight': 4, 'color': 'red', 'opacity': 1.0},
                    'signagemanagement': {'weight': 5, 'color': 'red', 'opacity': 1.0},
    
                    'filelayer': {'color': 'blue', 'opacity': 1.0, 'fillOpacity': 0.9, 'weight': 3, 'radius': 5},
                    
                    'detail': {'color': '#ffff00'},
                    'others': {'color': '#ffff00'},
    
                    'print': {
                        'path': {'weight': 1},
                        'trek': {'color': '#FF3300', 'weight': 7, 'opacity': 0.5,
                                'arrowColor': 'black', 'arrowSize': 10},
                    }
                }
    .. md-tab-item:: Examples

            Example to override configuration for displaying ``Path`` objects::

                MAPENTITY_CONFIG['MAP_STYLES']['path'] = {'color': 'red', 'weight': 5}

            Example to override a specific parameter::

                MAPENTITY_CONFIG['MAP_STYLES']['city']['opacity'] = 0.8

Colors pool
~~~~~~~~~~~~

Regarding colors that depend from database content, such as land layers (physical types, work management...) or restricted areas. We use a specific setting that receives a list of colors:

.. md-tab-set::
    :name: mapentity-config-color-pools-tabs

    .. md-tab-item:: Default configuration

        See the default values in `geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_ for the complete list of colors.

        .. code-block:: python

    
                COLORS_POOL = {
                               'land': ['#f37e79', '#7998f3', '#bbf379', '#f379df', '#f3bf79', '#9c79f3', '#7af379'],
                               'physical': ['#f3799d', '#79c1f3', '#e4f379', '#de79f3', '#79f3ba', '#f39779', '#797ff3'],
                               'circulation': ['#f3799d', '#79c1f3', '#e4f379', '#de79f3', '#79f3ba', '#f39779', '#797ff3'],
                               'competence': ['#a2f379', '#f379c6', '#79e9f3', '#f3d979', '#b579f3', '#79f392', '#f37984'],
                               'signagemanagement': ['#79a8f3', '#cbf379', '#f379ee', '#79f3e3', '#79f3d3'],
                               'workmanagement': ['#79a8f3', '#cbf379', '#f379ee', '#79f3e3', '#79f3d3'],
                               'restrictedarea': ['plum', 'violet', 'deeppink', 'orchid',
                                                  'darkviolet', 'lightcoral', 'palevioletred',
                                                  'MediumVioletRed', 'MediumOrchid', 'Magenta',
                                                  'LightSalmon', 'HotPink', 'Fuchsia']}
    .. md-tab-item:: Example

         .. code-block:: python

    
                COLORS_POOL['restrictedarea'] = ['#ff00ff', 'red', '#ddddd'...]
.. note:: 
  - Each of the object types for Status module (``land``, ``physical``, ``competence``, ``signagemanagement``, ``workmanagement``...) should have values defined.
  - For ``restrictedarea``: add as many color there are restricted area types

Disable darker map backgrounds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since IGN map backgrounds are very dense and colourful, a dark opacity is applied. In order to disable, change this MapEntity setting:

Default value::

    MAPENTITY_CONFIG['MAP_BACKGROUND_FOGGED'] = True

Map screenshots
----------------

When you generate a PDF in Geotrek-admin, a screenshot of the map with the object location is done. This section list all the available parameters to configure this screenshot. Therefore, if you change one of those values, pdfs will be rendered differently.

.. note::
  For all these settings, we recommand you to check the result every time. Be careful, map screenshots are stored in cache so you need to force the re-generation of the computed images. To do so, you need to update the geometry of an object and save it, it will re-create image and help check your configuration.

  After validation of your modifications, to force Geotrek to re-create all the screenshots, you need to delete cached files in the folder ``/opt/geotrek-admin/var/media/maps``.

  .. code-block:: bash

    cd /opt/geotrek-admin/var/media/maps
    rm *


Display related objects
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    SHOW_SENSITIVE_AREAS_ON_MAP_SCREENSHOT = True
    SHOW_POIS_ON_MAP_SCREENSHOT = True
    SHOW_SERVICES_ON_MAP_SCREENSHOT = True
    SHOW_SIGNAGES_ON_MAP_SCREENSHOT = True
    SHOW_INFRASTRUCTURES_ON_MAP_SCREENSHOT = True

Map capture size
~~~~~~~~~~~~~~~~~

Allow to change the size in pixels of the screenshot.

Example::

    MAP_CAPTURE_SIZE = 800

Geographical CRUD
-------------------

Path snapping distance
~~~~~~~~~~~~~~~~~~~~~~~

Minimum distance to merge two paths in unit of SRID.

.. md-tab-set::
    :name: path-snapping-distance-tabs

    .. md-tab-item:: Default configuration

    
            .. code-block:: python
    
                PATH_SNAPPING_DISTANCE = 1.0
    .. md-tab-item:: Example

         .. code-block:: python

    
                PATH_SNAPPING_DISTANCE = 2.0

.. note::
  Used only when ``TREKKING_TOPOLOGY_ENABLED = True``

Snap distance
~~~~~~~~~~~~~~~

Distance of snapping for the cursor in pixels on Leaflet map.

Default value::

    SNAP_DISTANCE = 30

Path merge snapping distance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Minimum distance to merge two paths.

Default value::

    PATH_MERGE_SNAPPING_DISTANCE = 2

.. note::
  - Should be higher or the same as ``PATH_SNAPPING_DISTANCE``. 
  - Used only when ``TREKKING_TOPOLOGY_ENABLED = True``.

Enable treks points of reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Points of reference are enabled on form of treks.

Default value::

    TREK_POINTS_OF_REFERENCE_ENABLED = True

Enable outdoor course points of reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Points of reference are enabled on form of otudoor courses.

Default value::

    OUTDOOR_COURSE_POINTS_OF_REFERENCE_ENABLED = True

Topology static offset
~~~~~~~~~~~~~~~~~~~~~~~~

Land objects are added on other objects (path for example) with offset, avoiding overlay.

.. image:: /images/advanced-configuration/status.jpg
   :align: center
   :alt: Status


.. md-tab-set::
    :name: topology-static-offset-tabs

    .. md-tab-item:: Default configuration

        .. code-block:: python

    
                TOPOLOGY_STATIC_OFFSETS = {'land': -5,
                                        'physical': 0,
                                        'circulation': 15,
                                        'competence': 5,
                                        'signagemanagement': -10,
                                        'workmanagement': 10}
    .. md-tab-item:: Example

         .. code-block:: python

    
                TOPOLOGY_STATIC_OFFSETS = {'land': -5, 
                                        'physical': 0, 
                                        'competence': 5, 
                                        'signagemanagement': -10, 
                                        'workmanagement': 10}

Altimetric profile
~~~~~~~~~~~~~~~~~~~~~

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
  For all these settings, we recommand you to check the result every time. Be careful, altimetric profiles are stored in cache so you need to force the re-generation of the computed images. To do so, you need to update the geometry of an object and save it, it will re-create image and help check your configuration.

  After validation of your modifications, to force Geotrek to re-create all the altimetric profiles, you need to delete cached files in the folder ``/opt/geotrek-admin/var/media/profiles``.

  .. code-block:: bash

    cd /opt/geotrek-admin/var/media/profiles
    rm *

