===============
Synchronization
===============

.. _geotrek-mobile-app-v3:

Geotrek-mobile app v3
======================

The Geotrek-mobile app v3 has its own API and synchronization command called ``sync_mobile``.

::

    geotrek sync_mobile [-h] [--languages LANGUAGES] [--portal PORTAL]
                        [--skip-tiles] [--url URL] [--indent INDENT]
                        [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                        [--pythonpath PYTHONPATH] [--traceback]
                        [--no-color] [--force-color]
                        path

.. _automatic-synchronization:

Automatic synchronization
==========================

You can set up automatic synchronization by creating a file ``/etc/cron.d/geotrek_sync`` that contains:

.. md-tab-set::
    :name: automatic-synchronization-tabs

    .. md-tab-item:: With Debian

         .. code-block:: bash

         	0 3 * * * root /usr/sbin/geotrek sync_mobile /opt/geotrek-admin/var/data 

    .. md-tab-item:: With Docker

         .. code-block:: bash

         	0 3 * * * root /usr/bin/docker compose run --rm web ./manage.py sync_mobile /opt/geotrek-admin/var/data 

This example will automatically synchronize data a 3 am every day.

Note: it is required to give the full path to the geotrek command since cron sets the PATH only to `bin:/usr/sbin` with Debian and `bin:/usr/bin` with Docker.
