=============
Configuration
=============

.. _basic-configuration-update:

Basic configuration update
===========================

To update basic configuration (server name, database connection, languages, or set workers number or timeout), run:

.. md-tab-set::
    :name: update-configuration-tabs

    .. md-tab-item:: With Debian

            .. code-block:: bash
    
                sudo dpkg-reconfigure geotrek-admin 

    .. md-tab-item:: With Docker

         .. code-block:: bash

                docker compose run --rm web update.sh 

The basic configuration is stored in ``/opt/geotrek-admin/var/conf/env`` file, not to be changed manually.
This file also contains the PostgreSQL authentification details, if you need to access your Geotrek-admin database.

.. _custom-setting-file:

Custom setting file
====================

Geotrek-admin advanced configuration is done in ``/opt/geotrek-admin/var/conf/custom.py`` file.

The list of all overridable setting and default values can be found at : 
`geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_.

After any change in ``custom.py``, run:

.. md-tab-set::
    :name: restart-service-tabs

    .. md-tab-item:: With Debian

            .. code-block:: bash
    
                sudo service geotrek restart 

    .. md-tab-item:: With Docker

         .. code-block:: bash

                docker compose down && up -d 


Sometimes you also have to run:

.. md-tab-set::
    :name: reconfigure-tabs

    .. md-tab-item:: With Debian

            .. code-block:: bash
    
                sudo dpkg-reconfigure geotrek-admin 

    .. md-tab-item:: With Docker

         .. code-block:: bash

                docker compose run --rm web update.sh 

.. note::

    Don't override the ``os.getenv()`` settings as they are managed with Basic configuration.

.. _nginx-configuration:

NGINX configuration
-------------------

NGINX configuration is controlled by Geotrek-admin and will be erased at each upgrade.
Do not modify ``/etc/nginx/sites-available/geotrek.conf`` or ``/etc/nginx/sites-enable/geotrek.conf``.
Modify ``/opt/geotrek-admin/var/conf/nginx.conf.in`` instead. To update ``nginx.conf``, then run:

.. md-tab-set::
    :name: reconfigure-ngninx-tabs

    .. md-tab-item:: With Debian
    
            .. code-block:: bash
    
                sudo dpkg-reconfigure geotrek-admin 

    .. md-tab-item:: With Docker

         .. code-block:: bash

                docker compose run --rm web update.sh 

.. _activate-ssl-https:

Activate SSL / HTTPS
=====================

To activate https, you need firstly to change ``custom.py`` and add:

.. code-block:: python

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

After this, edit ``nginx.conf.in`` to add your certificate.

If you generate it with letsencrypt :
You can use certbot to add the certificate in your configuration.
But you will have to move the configuration automatically added into ``nginx.conf``, to the file ``nginx.conf.in`` in ``/opt/geotrek-admin/var/conf/`` directory.

You have to move the configuration to the file ``nginx.conf.in`` because ``nginx.conf`` is automatically changed during command ``dpkg-reconfigure geotrek-admin``.

.. warning::

    You need to replace the ``$`` from Certbot with ``${DOLLAR}`` everywhere in the ``nginx.conf.in`` file, then run the command ``sudo dpkg-reconfigure geotrek-admin`` to regenerate the file.

.. _mandatory-settings:

Mandatory settings
==================

Spatial reference identifier
----------------------------

.. code-block:: python

    SRID = 2154

Spatial reference identifier of your database. Default 2154 is RGF93 / Lambert-93 - France

*It should not be change after any creation of geometries.*

*Choose wisely with epsg.io for example*

.. _default-structure:

Default Structure
----------------------------

.. code-block:: python

    DEFAULT_STRUCTURE_NAME = "GEOTEAM"

Name for your default structure.

   *This one can be changed, except it's tricky.*

   * *First change the name in the admin (authent/structure),*
   * *Stop your instance admin.*
   * *Change in the settings*
   * *Re-run the server.*

.. _configuration-dynamic-segmentation:

Dynamic segmentation
----------------------

.. code-block:: python

    TREKKING_TOPOLOGY_ENABLED = True

Use dynamic segmentation or not.

:ref:`Dynamic segmentation <segmentation-dynamique>` is used by default when installing Geotrek-admin.

With this mode, linear objects are built and stored related to paths.

Without this mode, linear geometry of objects is built and stored as an independent geographic object without relation to paths.

So if you want to use Geotrek-admin without dynamic segmentation, set TREKKING_TOPOLOGY_ENABLED to false after installation.

Do not change it again to true after setting it to false.

Translations
-------------

.. code-block:: python

    LANGUAGE_CODE = 'fr'

Language of your interface.

.. code-block:: python

   MODELTRANSLATION_LANGUAGES = ('en', 'fr', 'it', 'es')

Languages of your project. It will be used to generate fields for translations. (ex: description_fr, description_en)

*You won't be able to change it easily, avoid to add any languages and do not remove any.*

.. note::
  It is preferable, when in doubt, to include all necessary languages during the initial installation, even if some remain unused afterward, rather than missing some and facing complications to add them later.

Spatial extents
----------------

Bounding box of your project : x minimum , y minimum , x max, y max::

        4 ^
          |
    1     |     3
    <-----+----->
          |
          |
        2 v

Default values::

    SPATIAL_EXTENT = (105000, 6150000, 1100000, 7150000)

.. warning::
  * If you extend spatial extent, don't forget to load a new DEM that covers all the zone.
  * If you shrink spatial extent, be sure there is no element in the removed zone or you will no more be able to see and edit it.

In order to check your configuration of spatial extents, a small tool
is available at ``https://<server_url>/tools/extents/``. Administrator privileges are required.

.. image:: /images/installation-and-configuration/toolextent.jpg
   :align: center
   :alt: Interface de Tool extents

.. _users-management:

Users management
==================

See :ref:`User management section in usage <user-management-section>`.

.. _database-users:

Database users
===============

It is not safe to use the ``geotrek`` user in QGIS, or to give its password to
many collaborators.

A wise approach, is to create a *read-only* user, or with specific permissions.

With *pgAdmin*, you can create database users like this:

::

    CREATE ROLE lecteur LOGIN;
    ALTER USER lecteur PASSWORD 'passfacile';
    GRANT CONNECT ON DATABASE geotrekdb TO lecteur;

And give them permissions by schema :

::

    GRANT USAGE ON SCHEMA public TO lecteur;
    GRANT USAGE ON SCHEMA geotrek TO lecteur;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO lecteur;
    GRANT SELECT ON ALL TABLES IN SCHEMA geotrek TO lecteur;

You can also create groups, etc. See `PostgreSQL documentation <https://www.postgresql.org/docs/>`_.


