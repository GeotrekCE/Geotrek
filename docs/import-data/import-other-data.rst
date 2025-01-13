=============
From a file
=============

.. abstract:: Keywords

   ``command line``, ``import en ligne de commande``

You can add parsers in your custom `parsers.py` file (``/opt/geotrek-admin/var/conf/parsers.py``) which will allow you to
import data from files directly in your admin (superusers only).
For example, some parsers are not available by default but you can use them adding some lines in your parsers file :

.. code-block:: python

    from geotrek.trekking.parsers import TrekParser # only without dynamic segmentation (`TREKKING_TOPOLOGY_ENABLED` = False)
    from geotrek.trekking.parsers import POIParser

You can also use some of Geotrek commands to import data from a vector file handled by `GDAL <https://gdal.org/drivers/vector/index.html>`_ (e.g.: ESRI Shapefile, GeoJSON, GeoPackage etc.)

Possible data are : POI, infrastructures, signages, cities, districts, restricted areas, paths.

You must use these commands to import spatial data because of the :ref:`dynamic segmentation <configuration-dynamic-segmentation>`, which will not be computed if you enter the data manually. 

Here are the Geotrek commands available to import data from file:

- ``loadpoi``
- ``loadinfrastructure``
- ``loadsignage``
- ``loadcities`` ==> See :ref:`in Areas section <import-cities>`
- ``loaddistricts`` ==> See :ref:`in Areas section <import-districts>`
- ``loadrestrictedareas`` ==> See :ref:`in Areas section <import-restricted-areas>`

Usually, these commands come with ability to match file attributes to model fields.

To get help about a command:

::

    sudo geotrek help <subcommand>

.. _import-pois:

Load POIs
==========

.. ns-detail::

    .. 

.. example:: sudo geotrek help loadpoi
    :collapsible:

    ::

      usage: manage.py loadpoi [-h] [--encoding ENCODING] [--name-field NAME_FIELD]
                         [--type-field TYPE_FIELD]
                         [--description-field DESCRIPTION_FIELD]
                         [--name-default NAME_DEFAULT]
                         [--type-default TYPE_DEFAULT] [--version]
                         [-v {0,1,2,3}] [--settings SETTINGS]
                         [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                         [--force-color] [--skip-checks]
                         point_layer

      Load a layer with point geometries in a model

      positional arguments:
        point_layer

      optional arguments:
      -h, --help            show this help message and exit
      --encoding ENCODING, -e ENCODING
                            File encoding, default utf-8
      --name-field NAME_FIELD, -n NAME_FIELD
                            Name of the field that contains the name attribute.
                            Required or use --name-default instead.
      --type-field TYPE_FIELD, -t TYPE_FIELD
                            Name of the field that contains the POI Type
                            attribute. Required or use --type-default instead.
      --description-field DESCRIPTION_FIELD, -d DESCRIPTION_FIELD
                            Name of the field that contains the description of the
                            POI (optional)
      --name-default NAME_DEFAULT
                            Default value for POI name. Use only if --name-field
                            is not set
      --type-default TYPE_DEFAULT
                            Default value for POI Type. Use only if --type-field
                            is not set
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

    * **Optional fields** : Description, SRID, Encoding
    * **Required fields** : Name, Type
    * **Geometric type** : Point
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`poi.geojson <../files/import/poi.geojson>`
    * **Good to know** : 
       * The SRID must be 4326
       * The default encoding is UTF-8
       * Imported POIs are unpublished by default
       * When importing a Geopackage, the first layer is always used

**Default values**

- When a default value is provided without a fieldname to import the default value is set for all POIs objects.
- When a default value is provided in addition to a fieldname to import it is used as a fallback for entries without the specified import field.

**Import command examples :**

.. md-tab-set::
    :name: poi-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadpoi \
          ./var/conf/poi.geojson \
          --encoding latin1 \
          --name-field name --name-default "Point d'intérêt" \
          --type-field type --type-default "Faune" \
          --description-field description 


    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadpaths \
          ./var/conf/poi.geojson \
          --encoding latin1 \
          --name-field name --name-default "Point d'intérêt" \
          --type-field type --type-default "Faune" \
          --description-field description 

.. _import-infrastructure:

Load Infrastructure
======================

.. ns-detail::

    .. 

.. example:: sudo geotrek help loadinfrastructure
    :collapsible:

    ::

      usage: manage.py loadinfrastructure [-h] [--use-structure]
                                      [--encoding ENCODING]
                                      [--name-field NAME_FIELD]
                                      [--name-default NAME_DEFAULT]
                                      [--type-field TYPE_FIELD]
                                      [--type-default TYPE_DEFAULT]
                                      [--category-field CATEGORY_FIELD]
                                      [--category-default CATEGORY_DEFAULT]
                                      [--condition-field CONDITION_FIELD]
                                      [--condition-default CONDITION_DEFAULT]
                                      [--structure-field STRUCTURE_FIELD]
                                      [--structure-default STRUCTURE_DEFAULT]
                                      [--description-field DESCRIPTION_FIELD]
                                      [--description-default DESCRIPTION_DEFAULT]
                                      [--year-field YEAR_FIELD]
                                      [--year-default YEAR_DEFAULT]
                                      [--eid-field EID_FIELD] [--version]
                                      [-v {0,1,2,3}] [--settings SETTINGS]
                                      [--pythonpath PYTHONPATH] [--traceback]
                                      [--no-color] [--force-color]
                                      [--skip-checks]
                                      point_layer

      Load a layer with point geometries and import features as infrastructures objects
      (expected formats: shapefile or geojson)

      positional arguments:
        point_layer

      optional arguments:
      -h, --help            show this help message and exit
      --use-structure       If set the given (or default) structure is used to
                            select or create conditions and types of
                            infrastructures.
      --encoding ENCODING, -e ENCODING
                            File encoding, default utf-8
      --name-field NAME_FIELD, -n NAME_FIELD
                            The field to be imported as the `name` of the
                            infrastructure
      --name-default NAME_DEFAULT
                            Default name for all infrastructures, fallback for
                            entries without a name
      --type-field TYPE_FIELD, -t TYPE_FIELD
                            The field to select or create the type value of the
                            infrastructure (field `InfrastructureType.label`)
      --type-default TYPE_DEFAULT
                            Default type for all infrastructures, fallback for
                            entries without a type.
      --category-field CATEGORY_FIELD, -i CATEGORY_FIELD
                            The field to select or create the type value of the
                            infrastructure (field `InfrastructureType.type`)
      --category-default CATEGORY_DEFAULT
                            Default category for all infrastructures, "B" by
                            default. Fallback for entries without a category
      --condition-field CONDITION_FIELD, -c CONDITION_FIELD
                            The field to select or create the condition value of
                            the infrastructure (field
                            `InfrastructureCondition.label`)
      --condition-default CONDITION_DEFAULT
                            Default condition for all infrastructures, fallback
                            for entries without a category
      --structure-field STRUCTURE_FIELD, -s STRUCTURE_FIELD
                            The field to be imported as the structure of the
                            infrastructure
      --structure-default STRUCTURE_DEFAULT
                            Default Structure for all infrastructures
      --description-field DESCRIPTION_FIELD, -d DESCRIPTION_FIELD
                            The field to be imported as the description of the
                            infrastructure
      --description-default DESCRIPTION_DEFAULT
                            Default description for all infrastructures, fallback
                            for entries without a description
      --year-field YEAR_FIELD, -y YEAR_FIELD
                            The field to be imported as the `implantation_year` of
                            the infrastructure
      --year-default YEAR_DEFAULT
                            Default year for all infrastructures, fallback for
                            entries without a year
      --eid-field EID_FIELD
                            The field to be imported as the `eid` of the
                            infrastructure (external ID)
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

    * **Optional fields** : Structure, Description, Status, Year, External ID, SRID, Encoding
    * **Required fields** : Name, Type, Category
    * **Geometric type** : Point
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`infrastructure.geojson <../files/import/infrastructure.geojson>`
    * **Good to know** : 
       * The SRID must be 4326
       * The default encoding is UTF-8
       * Imported infrastructures are unpublished by default
       * When importing a Geopackage, the first layer is always used
       * The command will select or create InfrastructureType values based on the `type-field` argument, taking the default value "A" for the category

**Required fields**

The following fields are mandatory to create an Infrastructure object: `name`, `type` and `category`. For each of those fields either an import field and/or a default value MUST be provided. If the command is unable to determine values for those fields for a given layer, the layer is skipped with an error message.

**Default values**

- When a default value is provided without a fieldname to import the default value is set for all Infrastructure objects.
- When a default value is provided in addition to a fieldname to import it is used as a fallback for entries without the specified import field.

**Selection and addition of parameterized values**

Infrastructure objects have several values from Geotrek's parameterized values sets :

- `type` from InfrastructureType values (and `category` which is implied by the `type` value),
- `condition` from InfrastructureCondition values.

New parameterized values are created and added to Geotrek Admin if necessary. The command checks if the imported `type` value already exists by looking for an InfrastructureType with the right `type` + `category`.

- ``A`` category value stands for Building
- ``E`` category value stands for Equipment

.. md-tab-set::
    :name: infrastructure-import-type-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadinfrastructure  --type-field "type"  --category-field "cat" [...]

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadinfrastructure --type-field "type"  --category-field "cat" [...]


**Import command examples :**

.. md-tab-set::
    :name: infrastructures-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadinfrastructure \
          ./var/conf/infrastructure.geojson \
          --encoding latin1 \
          --name-field name --name-default "Banc" \
          --type-field type --type-default "Banc" \
          --category-field categorie --category-default "E" \
          --description-field descriptio --description-default "Banc confortable" \
          --condition-field etat --condition-default "Bon état" \
          --structure-field structure --structure-default "Ma structure" \
          --year-field annee --year-default "2024" \
          --eid-field id

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadinfrastructure \
          ./var/conf/infrastructure.geojson \
          --encoding latin1 \
          --name-field name --name-default "Banc" \
          --type-field type --type-default "Banc" \
          --category-field categorie --category-default "E" \
          --description-field descriptio --description-default "Banc confortable" \
          --condition-field etat --condition-default "Bon état" \
          --structure-field structure --structure-default "Ma structure" \
          --year-field annee --year-default "2024" \
          --eid-field id

.. _import-signage:

Load Signage
===============

.. ns-detail::

    .. 
      
.. example:: sudo geotrek help loadsignage
    :collapsible:

    ::

      usage: manage.py loadsignage [-h] [--use-structure] [--encoding ENCODING]
                               [--name-field NAME_FIELD]
                               [--type-field TYPE_FIELD]
                               [--condition-field CONDITION_FIELD]
                               [--manager-field MANAGER_FIELD]
                               [--sealing-field SEALING_FIELD]
                               [--structure-field STRUCTURE_FIELD]
                               [--description-field DESCRIPTION_FIELD]
                               [--year-field YEAR_FIELD]
                               [--code-field CODE_FIELD] [--eid-field EID_FIELD]
                               [--type-default TYPE_DEFAULT]
                               [--name-default NAME_DEFAULT]
                               [--condition-default CONDITION_DEFAULT]
                               [--manager-default MANAGER_DEFAULT]
                               [--sealing-default SEALING_DEFAULT]
                               [--structure-default STRUCTURE_DEFAULT]
                               [--description-default DESCRIPTION_DEFAULT]
                               [--year-default YEAR_DEFAULT]
                               [--code-default CODE_DEFAULT] [--version]
                               [-v {0,1,2,3}] [--settings SETTINGS]
                               [--pythonpath PYTHONPATH] [--traceback]
                               [--no-color] [--force-color] [--skip-checks]
                               point_layer


      Load a layer with point geometries in te structure model

      positional arguments:
        point_layer

      optional arguments:
      -h, --help            show this help message and exit
      --use-structure       Allow to use structure for condition and type of
                            infrastructures
      --encoding ENCODING, -e ENCODING
                            File encoding, default utf-8
      --name-field NAME_FIELD, -n NAME_FIELD
                            Name of the field that will be mapped to the Name
                            field in Geotrek
      --type-field TYPE_FIELD, -t TYPE_FIELD
                            Name of the field that will be mapped to the Type
                            field in Geotrek
      --condition-field CONDITION_FIELD, -c CONDITION_FIELD
                            Name of the field that will be mapped to the Condition
                            field in Geotrek
      --manager-field MANAGER_FIELD, -m MANAGER_FIELD
                            Name of the field that will be mapped to the Manager
                            field in Geotrek
      --sealing-field SEALING_FIELD
                            Name of the field that will be mapped to the sealing
                            field in Geotrek
      --structure-field STRUCTURE_FIELD, -s STRUCTURE_FIELD
                            Name of the field that will be mapped to the Structure
                            field in Geotrek
      --description-field DESCRIPTION_FIELD, -d DESCRIPTION_FIELD
                            Name of the field that will be mapped to the
                            Description field in Geotrek
      --year-field YEAR_FIELD, -y YEAR_FIELD
                            Name of the field that will be mapped to the Year
                            field in Geotrek
      --code-field CODE_FIELD
                            Name of the field that will be mapped to the Code
                            field in Geotrek
      --eid-field EID_FIELD
                            Name of the field that will be mapped to the External
                            ID in Geotrek
      --type-default TYPE_DEFAULT
                            Default value for Type field
      --name-default NAME_DEFAULT
                            Default value for Name field
      --condition-default CONDITION_DEFAULT
                            Default value for Condition field
      --manager-default MANAGER_DEFAULT
                            Default value for the Manager field
      --sealing-default SEALING_DEFAULT
                            Default value for the Sealing field
      --structure-default STRUCTURE_DEFAULT
                            Default value for Structure field
      --description-default DESCRIPTION_DEFAULT
                            Default value for Description field
      --year-default YEAR_DEFAULT
                            Default value for Year field
      --code-default CODE_DEFAULT
                            Default value for Code field
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

    * **Optional fields** : Comment, SRID, Encoding
    * **Required fields** : Structure, Name
    * **Geometric type** : Point
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`signage.geojson <../files/import/signage.geojson>`
    * **Good to know** : 
       * The default SRID code is 4326
       * The default encoding is UTF-8
       * Imported signage are unpublished by default
       * When importing a Geopackage, the first layer is always used

**Default values**

- When a default value is provided without a fieldname to import the default value is set for all Signage objects.
- When a default value is provided in addition to a fieldname to import it is used as a fallback for entries without the specified import field.

**Import command examples :**

.. md-tab-set::
    :name: signage-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadsignage \
          ./var/conf/signage.geojson \
          --encoding latin1 \
          --name-field name \
          --type-field type --type-default "Directionnelle" \
          --condition-field etat --condition-default "Bon état" \
          --manager-field gestionnaire \
          --sealing-field scellement --sealing-default "Planté" \
          --structure-field structure \
          --description-field description --description-default "Poteau planté" \
          --year-field annee --year-default "2024" \
          --code-field code --code-default "81150_PR2_P1" \
          --eid-field id

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadsignage \
          ./var/conf/signage.geojson \
          --encoding latin1 \
          --name-field name \
          --type-field type --type-default "Directionnelle" \
          --condition-field etat --condition-default "Bon état" \
          --manager-field gestionnaire \
          --sealing-field scellement --sealing-default "Planté" \
          --structure-field structure \
          --description-field description --description-default "Poteau planté" \
          --year-field annee --year-default "2024" \
          --code-field code --code-default "81150_PR2_P1" \
          --eid-field id

.. important::

    Blades are not yet supported, therefore this command only imports signages in the database. 

