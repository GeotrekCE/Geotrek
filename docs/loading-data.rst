.. _loading-data-section:

============
LOADING DATA
============

Required Initial Data
---------------------

Load basic data :

::

    make load_data

:note:

    This command will load default users, groups, default values for lists... in French and English. So you need to enable EN and FR at least in ``etc/settings.ini``


Required Super User
-------------------

.. code-block:: bash

    bin/django createsuperuser


You will be prompted to enter an username, a password and mail address for your super user.
This first user will allow you to login in Geotrek, having all permissions to create and manage other users.


Prerequisites for your data
---------------------------

Layers
~~~~~~

* WMS (scan + ortho)
* Projection
* Bounding box in native projection

Core
~~~~

* Only LineString geometries
* Simple geometries
* Not overlapping

If possible :

* Connex graph
* Name column
* Data source

Formats: Shapefile or pure SQL dump SQL (CREATE TABLE + INSERT)


Land
~~~~

* Cities polygons (Shapefile or SQL, simple and valid Multi-Polygons)
* Districts (Shapefile ou SQL, simple and valid Multi-Polygons)
* Restricted Areas (Shapefile ou SQL, simple and valid Multi-Polygons)

Extras
~~~~~~

* Languages list
* Structures list (and default one)


Load MNT raster
---------------

`In QGIS <http://docs.qgis.org/latest/en/docs/training_manual/processing/cutting_merging.html>`_,
you can visualize your DEM, or merge several tiles together (in *Raster* > *Misc* > *Merge*).

The elevation data of DEM must be integer values. If the elevation data are floating numbers, you can convert them in integer values with the Raster calculator processing of SAGA (Processing > Toolbox > SAGA > Raster calculus > Raster calculator) with formula parameter set to ``int(a)``.

Generate a GeoTIFF, and upload both files (``.tif`` + ``.tfw``) on the server.
And use the Geotrek command to load it into PostGIS :


::

    bin/django loaddem <PATH>/dem.tif


:note:

    This command makes use of *GDAL* and ``raster2pgsql`` internally. It
    therefore supports all GDAL raster input formats. You can list these formats
    with the command ``raster2pgsql -G``.
    
:note:

    If you only have a ``.tif`` file, you can generate the ``.tfw`` file with the command ``gdal_translate -co "TFW=YES" in.tif out.tif``. It will generate a new ``.tif`` file with its ``.tfw`` metadata file.
