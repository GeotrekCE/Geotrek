.. _modules-and-components:

=======================
Modules and components
=======================

See the default values in `geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_ for the complete list of available parameters.

Enable Apps
------------

In order to disable a full set of modules, in the custom settings file, add the following code:

.. code-block:: python

    # Disable infrastructure and maintenance
    _INSTALLED_APPS = list(INSTALLED_APPS)
    _INSTALLED_APPS.remove('geotrek.infrastructure')
    _INSTALLED_APPS.remove('geotrek.maintenance')
    INSTALLED_APPS = _INSTALLED_APPS

Trail model enabled
~~~~~~~~~~~~~~~~~~~~
.. ns-only::

    .. 

In order to remove notion of trails:

.. md-tab-set::
    :name: trail-model-enabled-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                TRAIL_MODEL_ENABLED = True

    .. md-tab-item:: Example

         .. code-block:: python
    
                TRAIL_MODEL_ENABLED = False

Landedge model enabled
~~~~~~~~~~~~~~~~~~~~~~~

.. ns-only::

    .. 

In order to remove landedge model:

.. md-tab-set::
    :name: landedge-model-enabled-tabs

    .. md-tab-item:: Default configuration
    
         .. code-block:: python
    
                LANDEDGE_MODEL_ENABLED = True

    .. md-tab-item:: Example

         .. code-block:: python
    
                LANDEDGE_MODEL_ENABLED = False


In order to remove zoning combo-boxes on list map:

.. code-block:: python

    LAND_BBOX_CITIES_ENABLED = False
    LAND_BBOX_DISTRICTS_ENABLED = False
    LAND_BBOX_AREAS_ENABLED = False

Tourism enabled
~~~~~~~~~~~~~~~~~

In order to hide TouristicContents and TouristicEvents on menu.

.. md-tab-set::
    :name: tourism-enabled-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                TOURISM_ENABLED = True

    .. md-tab-item:: Example

         .. code-block:: python
    
                TOURISM_ENABLED = False

Flatpages enabled
~~~~~~~~~~~~~~~~~~~~

In order to hide Flatpages on menu. Flatpages are used in Geotrek-rando:

.. md-tab-set::
    :name: flatpages-enabled-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                FLATPAGES_ENABLED = True

    .. md-tab-item:: Example

         .. code-block:: python
    
                FLATPAGES_ENABLED = False

Accessibility attachments enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to hide the accessibility menu for attachments:

.. md-tab-set::
    :name: accessibility-attachements-enabled-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                ACCESSIBILITY_ATTACHMENTS_ENABLED = True

    .. md-tab-item:: Example

         .. code-block:: python
    
                ACCESSIBILITY_ATTACHMENTS_ENABLED = False

.. note::
  - By doing so, some software upgrades may not be as smooth as usual.
  - Never forget to mention this customization if you ask for community support.

Paths
------

Allow path deletion enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``False``, it forbids to delete a path when at least one topology is linked to this path.

.. md-tab-set::
    :name: allow-path-deletion-topology-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                ALLOW_PATH_DELETION_TOPOLOGY = False

    .. md-tab-item:: Example

         .. code-block:: python
    
                ALLOW_PATH_DELETION_TOPOLOGY = True

Alert draft
~~~~~~~~~~~~~

If ``True``, it sends a message to managers (MANAGERS) whenever a path has been changed to draft.

.. md-tab-set::
    :name: alert-draft-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                ALERT_DRAFT = False

    .. md-tab-item:: Example

         .. code-block:: python
    
                ALERT_DRAFT = True

Alert review
~~~~~~~~~~~~~

If ``True``, it sends a message to managers (MANAGERS) whenever an object which can be published has been changed to review mode.

.. md-tab-set::
    :name: alert-review-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                ALERT_REVIEW = False

    .. md-tab-item:: Example

         .. code-block:: python
    
                ALERT_REVIEW = True

.. note::
  Email configuration takes place in ``/opt/geotrek-admin/var/conf/custom.py``, where you control recipients emails (``ADMINS``, ``MANAGERS``) and email server configuration.

Signage and Blade
-------------------

``BLADE_ENABLED`` and ``LINE_ENABLED`` settings (default to ``True``) allow to enable or disable blades and lines submodules.

``DIRECTION_ON_LINES_ENABLED`` setting (default to ``False``) allow to have the `direction` field on lines instead of blades.

Blade code type
~~~~~~~~~~~~~~~~

Type of the blade code (string or integer)


Example::

    BLADE_CODE_TYPE = INT

.. note::
  - It can be string or integer
  - If you have an integer code : ``int``
  - If you have an string code : ``str``

Blade code format
~~~~~~~~~~~~~~~~~~

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

Line code format
~~~~~~~~~~~~~~~~~

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
----

Trek POI intersection margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Buffer around treks to intersects POIs (works only without dynamic segmentation).

.. md-tab-set::
    :name: trek-poi-intersection-marging-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                TREK_POI_INTERSECTION_MARGIN = 500  # meters

    .. md-tab-item:: Example

         .. code-block:: python
    
                TREK_POI_INTERSECTION_MARGIN = 800  # meters

Diving
-------

Installed app for Diving
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable diving module, in the custom settings file, add the following code:

Example::

    INSTALLED_APPS += ('geotrek.diving', )

Then run ``sudo dpkg-reconfigure -pcritical geotrek-admin``.

You can also insert diving minimal data (default practices, difficulties, levels and group permissions values):

.. md-tab-set::
    :name: loaddata-diving-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash
    
                sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/basic.json
                cp /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/upload/* /opt/geotrek-admin/var/media/upload/

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web ./manage.py loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/basic.json
                cp /opt/geotrek-admin/lib/python*/site-packages/geotrek/diving/fixtures/upload/* /opt/geotrek-admin/var/media/upload/

You can insert licenses of attachments with this command :

.. md-tab-set::
    :name: loaddata-license-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash
    
                sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/common/fixtures/licenses.json

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web ./manage.py loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/common/fixtures/licenses.json

Land
-----

You can insert circulation and authorization types with this command :

.. md-tab-set::
    :name: loaddata-circulation-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash
    
                sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/land/fixtures/circulations.json

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web ./manage.py loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/land/fixtures/circulations.json

.. _outdoor:

Outdoor
--------

Installed app for Outdoor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable Outdoor module, in the custom settings file, add the following code:

Example::

    INSTALLED_APPS += ('geotrek.outdoor', )

Then run ``sudo dpkg-reconfigure -pcritical geotrek-admin``.

You can also insert Outdoor minimal data:

.. md-tab-set::
    :name: loaddata-outdoor-minimal-data-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash
    
                sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/outdoor/fixtures/basic.json

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web ./manage.py loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/outdoor/fixtures/basic.json


After installing Outdoor module, you have to add permissions to your user groups on outdoor sites and courses.

.. note::
  - Outdoor module is not compatible with PostGIS <= 2.4 that is included in Ubuntu 18.04.
  - You should either upgrade to Ubuntu 20.04 or upgrade postGIS to 2.5 with https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa

.. _sensitivity:

Sensitive areas
-----------------

.. note::
    The sensitivity module was developed as part of the Biodiv'Sports project to provide a central platform for sensitive areas. 

    The official address of the Geotrek instance of the Biodiv'Sports project is: https://biodiv-sports.fr, and is the base URL for the following API URLs.

Installed app for Sensitive areas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable sensitivity module, in the custom settings file, add the following code:

Example::

    INSTALLED_APPS += ('geotrek.sensitivity', )


You can insert rules of sensitive area with these commands:

.. md-tab-set::
    :name: loaddata-outdoor-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash
    
                sudo geotrek loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/rules.json
                cp -r /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/upload/rules/ /opt/geotrek-admin/var/media/upload/

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web ./manage.py loaddata /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/rules.json
                cp -r /opt/geotrek-admin/lib/python*/site-packages/geotrek/sensitivity/fixtures/upload/rules/ /opt/geotrek-admin/var/media/upload/

The following settings are related to sensitive areas:

Sensitivity default radius
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default radius of sensitivity bubbles when not specified for species

.. md-tab-set::
    :name: sensitivity-default-radius-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                SENSITIVITY_DEFAULT_RADIUS = 100  # meters

    .. md-tab-item:: Example

         .. code-block:: python
    
                SENSITIVITY_DEFAULT_RADIUS = 200  # meters


Sensitive area intersection margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Buffer around treks to intersects sensitive areas

.. md-tab-set::
    :name: sensitive-areas-intersection-margin-tabs

    .. md-tab-item:: Default configuration

         .. code-block:: python
    
                SENSITIVE_AREA_INTERSECTION_MARGIN = 500  # meters

    .. md-tab-item:: Example

         .. code-block:: python
    
                SENSITIVE_AREA_INTERSECTION_MARGIN = 800  # meters

.. notes

    # Take care if you change this value after adding data. You should update buffered geometry in SQL.
    ```UPDATE sensitivity_sensitivearea SET geom_buffered = ST_BUFFER(geom, <your new value>);```

.. seealso::
  
  See :ref:`sensitive-areas-import` to import data.

