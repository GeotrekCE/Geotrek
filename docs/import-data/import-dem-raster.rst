.. _altimetry-dem:

================
Altimetry (DEM)
================

.. abstract:: Keywords

   ``DEM``, ``MNT``, ``raster``, ``QGIS``


Refer to :ref:`this section <altimetry-dem-source-list>` to learn about the available downloadable data sources.

.. warning::

    - We recommend not importing a DEM with too precise resolution for performance reasons. For example, the BD Alti DEM with a 25m resolution is perfect to cover a department.
    - If you downloaded the BD Alti or RGE Alti, you will need to convert the ``.asc`` DEM to ``.tif`` format (e.g. with QGIS) before uploading it on the server.

In `QGIS <http://docs.qgis.org/latest/en/docs/training_manual/processing/cutting_merging.html>`_,
you can visualize your DEM, or merge several tiles together (in *Raster* > *Misc* > *Merge*).

Generate a GeoTIFF, and upload both files (``.tif`` + ``.tfw``) on the server.
And use the Geotrek-admin command to load it into PostGIS :

::

    sudo geotrek loaddem <PATH>/dem.tif

.. note::

    - This command makes use of *GDAL* and ``raster2pgsql`` internally. It therefore supports all GDAL raster input formats. You can list these formats with the command ``raster2pgsql -G``.
    - The elevation data of DEM must be integer values. If the elevation data are floating numbers, you can convert them in integer values with the Raster calculator processing of `SAGA in QGis <https://docs.qgis.org/3.34/en/docs/user_manual/processing/3rdParty.html#saga>`_ (Processing > Toolbox > SAGA > Raster calculus > Raster calculator) with formula parameter set to ``int(a)``.
    - If you only have a ``.tif`` file, you can generate the ``.tfw`` file with the command ``gdal_translate -co "TFW=YES" in.tif out.tif``. It will generate a new ``.tif`` file with its ``.tfw`` metadata file.
    - If you want to  update the altimetry of the topologies you need to use the option ``--update-altimery``

.. _import-dem-altimetry:

Load DEM 
=========

.. example:: sudo geotrek help loaddem
    :collapsible:

    ::

      usage: manage.py loaddem [-h] [--replace] 
      					 [--update-altimetry]
      					 [--version]
                         [-v {0,1,2,3}] [--settings SETTINGS]
                         [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                         [--force-color] [--skip-checks]
                         dem_path

	  Load DEM data (projecting and clipping it if necessary). You may need to create a GDAL Virtual Raster if your DEM is composed of several files.

	  positional arguments:
	      dem_path

	  optional arguments:
	  -h, --help            show this help message and exit
	  --replace             Replace existing DEM if any.
	  --update-altimetry    Update altimetry of all 3D geometries, /!\ This option
		                        takes lot of time to perform
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

**Import command examples :**

.. md-tab-set::
    :name: dem-import-command-tabs

    .. md-tab-item:: Example with Debian

         .. code-block:: bash

		    sudo geotrek loaddem \
		    .var/conf/dem.tif \
		    --replace \
		    --update-altimetry 

    .. md-tab-item:: Example with Docker

         .. code-block:: bash
    
		    docker compose run --rm web ./manage.py loaddem \
		    .var/conf/dem.tif \
		    --replace \
		    --update-altimetry 
			    

