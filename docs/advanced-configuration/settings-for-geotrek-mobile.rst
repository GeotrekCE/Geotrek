.. _settings-for-geotrek-mobile:

============================
Settings for Geotrek-mobile
============================

See the default values in `geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_ for the complete list of available parameters.


SYNC_MOBILE_ROOT
-----------------

Path on your server where the datas for mobile will be saved.

Example::

    SYNC_MOBILE_ROOT = os.path.join(VAR_DIR, 'mobile')

.. note:: 
  - If you want to modify it, do not forget to import os at the top of the file.
  - Check `import Python <https://docs.python.org/3/reference/import.html>`_ , if you need any information

SYNC_MOBILE_OPTIONS
--------------------

Options of the sync_mobile command.

.. md-tab-set::
    :name: sync-mobile-options-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                SYNC_MOBILE_OPTIONS = {'skip_tiles': False}

    .. md-tab-item:: Example

         .. code-block:: python
    
                SYNC_MOBILE_OPTIONS = {'skip_tiles': True}

MOBILE_NUMBER_PICTURES_SYNC
----------------------------

Number max of pictures that will be displayed and synchronized for each object (trek, POI, etc.) in the mobile app.

.. md-tab-set::
    :name: sync-mobile-pictures-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                MOBILE_NUMBER_PICTURES_SYNC = 3

    .. md-tab-item:: Example

         .. code-block:: python
    
                MOBILE_NUMBER_PICTURES_SYNC = 5

MOBILE_TILES_URL
-----------------

URL's Tiles used for the mobile.

Example with OpenTopoMap::

    MOBILE_TILES_URL = ['https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png']

Example with IGN::

    MOBILE_TILES_URL = ['https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}']

MOBILE_LENGTH_INTERVALS
-------------------------

Intervals of the mobile for the length filter.

.. md-tab-set::
    :name: mobile-length-intervals-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                    MOBILE_LENGTH_INTERVALS =  [
                      {"id": 1, "name": "< 10 km", "interval": [0, 9999]},
                      {"id": 2, "name": "10 - 30", "interval": [9999, 29999]},
                      {"id": 3, "name": "30 - 50", "interval": [30000, 50000]},
                      {"id": 4, "name": "> 50 km", "interval": [50000, 999999]}
                      ]

    .. md-tab-item:: Example

         .. code-block:: python
    
                    MOBILE_LENGTH_INTERVALS =  [
                      {"id": 1, "name": "< 5 km", "interval": [0, 4999]},
                      {"id": 2, "name": "5 - 10", "interval": [5000, 9999]},
                      {"id": 3, "name": "10 - 50", "interval": [10000, 49999]},
                      {"id": 4, "name": "> 50 km", "interval": [50000, 999999]}
                      ]

.. note:: 
  - Interval key is in meters.
  - You can add new intervals

MOBILE_ASCENT_INTERVALS
------------------------

Intervals of the mobile for the ascent filter.

.. md-tab-set::
    :name: mobile-ascent-intervals-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                    MOBILE_ASCENT_INTERVALS = [
                      {"id": 1, "name": "< 300 m", "interval": [0, 299]},
                      {"id": 2, "name": "300 - 600", "interval": [300, 599]},
                      {"id": 3, "name": "600 - 1000", "interval": [600, 999]},
                      {"id": 4, "name": "> 1000 m", "interval": [1000, 9999]}
                      ]

    .. md-tab-item:: Example

         .. code-block:: python
    
                    MOBILE_ASCENT_INTERVALS = [
                      {"id": 1, "name": "< 100 m", "interval": [0, 99]},
                      {"id": 2, "name": "100 - 300", "interval": [99, 299]},
                      {"id": 3, "name": "300 - 600", "interval": [300, 599]},
                      {"id": 4, "name": "> 600 m", "interval": [600, 9999]}
                      ]

.. note:: 
  Do the same as above

MOBILE_DURATION_INTERVALS
---------------------------

Intervals of the mobile for the duration filter.

.. md-tab-set::
    :name: mobile-duration-intervals-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                    MOBILE_DURATION_INTERVALS = [
                      {"id": 1, "name": "< 1 heure", "interval": [0, 1]},
                      {"id": 2, "name": "1h - 2h30", "interval": [1, 2.5]},
                      {"id": 3, "name": "2h30 - 5h", "interval": [2.5, 5]},
                      {"id": 4, "name": "5h - 9h", "interval": [5, 9]},
                      {"id": 5, "name": "> 9h", "interval": [9, 9999999]}
                      ]

    .. md-tab-item:: Example

         .. code-block:: python
    
                    MOBILE_DURATION_INTERVALS = [
                      {"id": 1, "name": "< 1 heure", "interval": [0, 1]},
                      {"id": 2, "name": "1h - 3h30", "interval": [1, 3.5]},
                      {"id": 3, "name": "3h30 - 5h", "interval": [3.5, 5]},
                      {"id": 4, "name": "5h - 10h", "interval": [5, 10]},
                      {"id": 5, "name": "> 10h", "interval": [10, 9999999]}
                      ]

.. note:: 
  Check ``MOBILE_LENGTH_INTERVALS`` section to use it, here interval correspond to 1 unit of hour

ENABLED_MOBILE_FILTERS
-----------------------

List of all the filters enabled on mobile.

.. md-tab-set::
    :name: enabled-mobile-filters-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
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

    .. md-tab-item:: Example

         .. code-block:: python
    
                    ENABLED_MOBILE_FILTERS = [
                    'practice',
                    'difficulty',
                    'duration',
                    'length',
                    'themes',
                    'route',
                    'accessibilities',
                    ]


.. note:: 
  Remove any of the filters if you don't want one of them. 

