.. _import-paths:

=======
Paths
=======

.. abstract:: Keywords

   ``command line``, ``import en ligne de commande``, ``QGIS``


.. ns-only::

    .. 
      
Requirements
=============

.. important::
    With :ref:`dynamic segmentation <configuration-dynamic-segmentation>`, importing paths is very risky if paths are already present in the same area in Geotrek,
    it is only safe for an area where no path is already created.

    Indeed, if you import paths where there are existing paths, treks, POIs or trails linked topology might be impacted.

Before import paths layer, it is important to prepare them. Paths must be:

- valid geometry
- simple geometry (no intersection)
- all intersections must cut the paths
- not double or covering others

Clean paths
=============

We use QGis to clean a path layer, with plugin Grass.
Here are the operations:

- check the SRID (must be the same as in Geotrek)

- vectors → geometric tools → "collect geometries"

- vectors → geometric tools → "group"

- clean geometries
    - search "v_clean" in "Processing toolbox"
    - select following options in cleaning tool: break, snap, duplicate (ou rmdup), rmline, rmdangle, chdangle, bpol, prune
    - in threshold enter 2,2,2,2,2,2,2,2 (2 meters for each option)

- delete duplicate geometries
    - search "duplicate" in "Processing toolbox"

- regroup lines
    - search "v.build.polyline" in "Processing toolbox")
    - select "first" in "Category number mode"

There are two ways to import path : importing your shapefile with command line,
or `via QGis following this blog post <https://makina-corpus.com/sig-webmapping/importer-une-couche-de-troncons-dans-geotrek>`_.

**To import a shapefile containing your paths, use the command** ``loadpaths``

Load paths
===========

.. example:: sudo geotrek help loadpaths
    :collapsible:

    ::

      usage: manage.py loadpaths [-h] [--structure STRUCTURE]
                             [--name-attribute NAME]
                             [--comments-attribute [COMMENT [COMMENT ...]]]
                             [--encoding ENCODING] [--srid SRID] [--intersect]
                             [--fail] [--dry] [--version] [-v {0,1,2,3}]
                             [--settings SETTINGS] [--pythonpath PYTHONPATH]
                             [--traceback] [--no-color] [--force-color]
                             [--skip-checks]
                             file_path

      Load a layer with point geometries in a model

      positional arguments:
        point_layer

      optional arguments:
      -h, --help            show this help message and exit
      --structure STRUCTURE
                            Define the structure
      --name-attribute NAME, -n NAME
                            Name of the name's attribute inside the file
      --comments-attribute [COMMENT [COMMENT ...]], -c [COMMENT [COMMENT ...]]
      --encoding ENCODING, -e ENCODING
                            File encoding, default utf-8
      --srid SRID, -s SRID  File's SRID
      --intersect, -i       Check paths intersect spatial extent and not only
                            within
      --fail, -f            Allows to grant fails
      --dry, -d             Do not change the database, dry run. Show the number
                            of fail and objects potentially created
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

    * **Optional fields** : Name, Comment, SRID, Encoding
    * **Required fields** : Structure
    * **Geometric type** : Linestring
    * **Expected formats** (supported by GDAL) : Shapefile, Geojson, Geopackage
    * **Template** : :download:`paths.geojson <../files/import/paths.geojson>`
    * **Good to know** : 
       * The default SRID code is 4326
       * The default encoding is UTF-8
       * When importing a Geopackage, the first layer is always used
       * The `--structure` requires an existing value and cannot retrieve it from a field in the file.

**Import command examples :**

.. md-tab-set::
    :name: path-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

          sudo geotrek loadpaths \
          ./var/conf/paths.geojson \
          --srid=2154 \
          --encoding latin1 \
          --structure "DEMO" \
          --name-attribute id \
          --comments-attribute commentaire


    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
          docker compose run --rm web ./manage.py loadpaths \
          ./var/conf/paths.geojson \
          --srid=2154 \
          --encoding latin1 \
          --structure "DEMO" \
          --name-attribute id \
          --comments-attribute commentaire
