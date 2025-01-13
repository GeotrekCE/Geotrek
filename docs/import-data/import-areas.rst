======
Areas
======

.. abstract:: Keywords

   ``Biodiv'Sport``, ``command line``, ``import en ligne de commande``, ``shapefile``


.. _import-cities:

Load Cities
==============

Refer to :ref:`this section <cities-source-list>` to learn about the available downloadable data sources.

.. example:: sudo geotrek help loadcities
    :collapsible:

    ::

      usage: manage.py loadcities [-h] [--code-attribute CODE]
                              [--name-attribute NAME] [--encoding ENCODING]
                              [--srid SRID] [--intersect] [--version]
                              [-v {0,1,2,3}] [--settings SETTINGS]
                              [--pythonpath PYTHONPATH] [--traceback]
                              [--no-color] [--force-color] [--skip-checks]
                              file_path

      Load Cities from a file within the spatial extent

      positional arguments:
        file_path             File's path of the cities

      optional arguments:
      -h, --help            show this help message and exit
      --code-attribute CODE, -c CODE
                            Name of the code's attribute inside the file
      --name-attribute NAME, -n NAME
                            Name of the name's attribute inside the file
      --encoding ENCODING, -e ENCODING
                            File encoding, default utf-8
      --srid SRID, -s SRID  File's SRID
      --intersect, -i       Check features intersect spatial extent and not only
                            within
      --version             Show program's version number and exit.
      -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
      --settings SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
      --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
      --traceback           Raise on CommandError exceptions.
      --no-color            Don't colorize the command output.
      --force-color         Force colorization of the command output.
      --skip-checks         Skip system checks.

.. note::

    * **Optional fields** : Code, SRID, Encoding
    * **Required fields** : Name
    * **Geometric type** : Polygon
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`cities.geojson <../files/import/cities.geojson>`
    * **Good to know** : 
       * The default SRID code is 4326
       * The default encoding is UTF-8
       * Imported cities are unpublished by default
       * When importing a Geopackage, the first layer is always used

**Import command examples :**

.. md-tab-set::
    :name: cities-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadcities \
          ./var/conf/cities.geojson \
          --intersect \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom \
          --code-attribute insee_com

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadcities \
          ./var/conf/cities.geojson \
          --intersect \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom \
          --code-attribute insee_com

.. hint::

    The ``--intersect`` option allows you to import features outside the spatial extent of the project.

.. _import-districts:

Load Districts
=================

Refer to :ref:`this section <districts-source-list>` to learn about the available downloadable data sources.

.. example:: sudo geotrek help loaddistricts
    :collapsible:

    ::

      usage: manage.py loaddistricts [-h] [--name-attribute NAME]
                                 [--encoding ENCODING] [--srid SRID]
                                 [--intersect] [--version] [-v {0,1,2,3}]
                                 [--settings SETTINGS] [--pythonpath PYTHONPATH]
                                 [--traceback] [--no-color] [--force-color]
                                 [--skip-checks]
                                 file_path

      Load Districts from a file within the spatial extent

      positional arguments:
        file_path             File's path of the districts

      optional arguments:
        -h, --help            show this help message and exit
        --name-attribute NAME, -n NAME
                              Name of the name's attribute inside the file
        --encoding ENCODING, -e ENCODING
                              File encoding, default utf-8
        --srid SRID, -s SRID  File's SRID
        --intersect, -i       Check features intersect spatial extent and not only
                              within
        --version             Show program's version number and exit.
        -v {0,1,2,3}, --verbosity {0,1,2,3}
                              Verbosity level; 0=minimal output, 1=normal output,
                              2=verbose output, 3=very verbose output
        --settings SETTINGS   The Python path to a settings module, e.g.
                              "myproject.settings.main". If this isn't provided, the
                              DJANGO_SETTINGS_MODULE environment variable will be
                              used.
        --pythonpath PYTHONPATH
                              A directory to add to the Python path, e.g.
                              "/home/djangoprojects/myproject".
        --traceback           Raise on CommandError exceptions.
        --no-color            Don't colorize the command output.
        --force-color         Force colorization of the command output.
        --skip-checks         Skip system checks.
            -h, --help            show this help message and exit
            --name-attribute NAME, -n NAME
                                  Name of the name's attribute inside the file
            --encoding ENCODING, -e ENCODING
                                  File encoding, default utf-8
            --srid SRID, -s SRID  File's SRID
            --intersect, -i       Check features intersect spatial extent and not only within
            --version             show program's version number and exit
            -v {0,1,2,3}, --verbosity {0,1,2,3}
                                  Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
            --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
            --pythonpath PYTHONPATH
                                  A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
            --traceback           Raise on CommandError exceptions
            --no-color            Don't colorize the command output.
            --force-color         Force colorization of the command output.
            --skip-checks         Skip system checks.

.. note::

    * **Optional fields** : SRID, Encoding
    * **Required fields** : Name
    * **Geometric type** : Polygon
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`districts.geojson <../files/import/districts.geojson>`
    * **Good to know** : 
       * The default SRID code is 4326
       * The default encoding is UTF-8
       * Imported districts are unpublished by default
       * When importing a Geopackage, the first layer is always used

**Import command examples :**

.. md-tab-set::
    :name: districts-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loaddistricts \
          ./var/conf/districts.geojson \
          --intersect \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loaddistricts \
          ./var/conf/districts.geojson \
          --intersect \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom

.. hint::

    The ``--intersect`` option allows you to import features outside the spatial extent of the project.

.. _import-restricted-areas:

Load Restricted areas
========================

Refer to :ref:`this section <restrictedareas-source-list>` to learn about the available downloadable data sources.

.. example:: sudo geotrek help loadrestrictedareas
    :collapsible:

    ::

      usage: manage.py loadrestrictedareas [-h] [--name-attribute NAME]
                                       [--encoding ENCODING] [--srid SRID]
                                       [--intersect] [--version] [-v {0,1,2,3}]
                                       [--settings SETTINGS]
                                       [--pythonpath PYTHONPATH] [--traceback]
                                       [--no-color] [--force-color]
                                       [--skip-checks]
                                       file_path area_type

      Load Restricted Area from a file within the spatial extent

      positional arguments:
        file_path             File's path of the restricted area
        area_type             Type of restricted areas in the file

      positional arguments:
        file_path             File's path of the restricted area
        area_type             Type of restricted areas in the file

      optional arguments:
        -h, --help            show this help message and exit
        --name-attribute NAME, -n NAME
                              Name of the name's attribute inside the file
        --encoding ENCODING, -e ENCODING
                              File encoding, default utf-8
        --srid SRID, -s SRID  File's SRID
        --intersect, -i       Check features intersect spatial extent and not only
                              within
        --version             Show program's version number and exit.
        -v {0,1,2,3}, --verbosity {0,1,2,3}
                              Verbosity level; 0=minimal output, 1=normal output,
                              2=verbose output, 3=very verbose output
        --settings SETTINGS   The Python path to a settings module, e.g.
                              "myproject.settings.main". If this isn't provided, the
                              DJANGO_SETTINGS_MODULE environment variable will be
                              used.
        --pythonpath PYTHONPATH
                              A directory to add to the Python path, e.g.
                              "/home/djangoprojects/myproject".
        --traceback           Raise on CommandError exceptions.
        --no-color            Don't colorize the command output.
        --force-color         Force colorization of the command output.
        --skip-checks         Skip system checks.

.. note::

    * **Optional fields** : SRID, Encoding
    * **Required fields** : Name, Type zone
    * **Geometric type** : Polygon
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`restrictedareas.geojson <../files/import/restrictedareas.geojson>`
    * **Good to know** : 
       * The default SRID code is 4326
       * The default encoding is UTF-8
       * Imported restricted areas are unpublished by default
       * When importing a Geopackage, the first layer is always used
       * Only objects within the project bounding box can be imported

**Import command examples :**

.. md-tab-set::
    :name: restrictedareas-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadrestrictedareas \
          ./var/conf/restrictedareas.geojson \
          --intersect \
          "Réserve naturelle"  \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom_site

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadrestrictedareas \
          ./var/conf/restrictedareas.geojson \
          --intersect \
          "Réserve naturelle"  \
          --srid=2154 \
          --encoding latin1 \
          --name-attribute nom_site

.. hint::

    The ``--intersect`` option allows you to import features outside the spatial extent of the project.

.. _sensitive-areas-import:

Sensitive areas import
=======================

Geotrek-admin provides tools to import sensitive areas data when the module is enabled. The imports can be done through the web interface or the command line. Below are the available options:

Import from Biodiv'Sports
----------------------------

Automatically import sensitive areas from Biodiv'Sports:

From the web interface
~~~~~~~~~~~~~~~~~~~~~~~

1. Click on the **user button** (top-right corner) and go to **Imports**.
2. Under **Data to import from network**, select **Biodiv'Sports** and click **Import**.
3. Wait for the import process to complete.
4. Check the Sensitivity module in Geotrek to view the imported data.

.. warning::
    If no data appears, Biodiv'Sports might not have data for your region. Consider adding your data directly to Biodiv'Sports for shared access across users.

From the command line
~~~~~~~~~~~~~~~~~~~~~~~

.. md-tab-set::
    :name: import-from-biodiv-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: python

          sudo geotrek import geotrek.sensitivity.parsers.BiodivParser

    .. md-tab-item:: Example with Docker

         .. code-block:: python
    
          docker compose run --rm web ./manage.py import  geotrek.sensitivity.parsers.BiodivParser

Import from a Shapefile
--------------------------

Refer to :ref:`this section <sensitiveareas-source-list>` to learn about the available downloadable data sources.

Sensitive areas can also be imported from an ESRI Shapefile (zipped). Ensure the following:

- The archive must include ``.shp``, ``.shx``, ``.dbf``, ``.prj``, etc.
- Field names must be configured correctly, as detailed below.

.. warning::
    Re-importing the same file will create duplicates.

**Species sensitive areas**:

- ``espece``: Species name (required, must exist in Biodiv'Sports).
- ``contact``: Optional contact information (text or HTML).
- ``descriptio``: Optional description (text or HTML).

**Regulatory sensitive areas**:

- ``name``: Area name (required).
- ``contact``: Optional contact information (text or HTML).
- ``descriptio``: Optional description (text or HTML).
- ``periode``: Months during which the area is sensitive (comma-separated, e.g., ``6,7,8`` for June-August).
- ``practices``: Practices associated with the area (comma-separated).
- ``url``: Optional URL for the record.

.. warning::
    Field names in shapefiles are limited to 10 characters (e.g., ``descriptio``).

From the web interface
~~~~~~~~~~~~~~~~~~~~~~~

1. Click on the **user button** (top-right corner) and go to **Imports**.
2. Select the data type (**species** or **regulatory area**).
3. Upload the zipped shapefile and select the appropriate encoding (UTF-8 or Windows-1252).
4. Click **Import** and monitor the progress.
5. View the import report for details.

.. figure:: ../images/advanced-configuration/import_shapefile.png
     :alt: Import shapefile in user interface
     :align: center

     Import shapefile in user interface

From the command line
~~~~~~~~~~~~~~~~~~~~~~~

- For species sensitive areas:

.. md-tab-set::
    :name: import-species-sensitive-areas-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: python

          sudo geotrek import geotrek.sensitivity.parsers.SpeciesSensitiveAreaShapeParser <file.zip>

    .. md-tab-item:: Example with Docker

         .. code-block:: python
    
          docker compose run --rm web ./manage.py import  geotrek.sensitivity.parsers.SpeciesSensitiveAreaShapeParser <file.zip>

- For regulatory sensitive areas:

.. md-tab-set::
    :name: import-regulatory-sensitive-areas-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: python

          sudo geotrek import geotrek.sensitivity.parsers.RegulatorySensitiveAreaShapeParser <file.zip>

    .. md-tab-item:: Example with Docker

         .. code-block:: python
    
          docker compose run --rm web ./manage.py import geotrek.sensitivity.parsers.RegulatorySensitiveAreaShapeParser <file.zip>

