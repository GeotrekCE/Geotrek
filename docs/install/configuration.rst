=============
Configuration
=============

.. contents::
   :local:
   :depth: 2
   

Basic configuration update
--------------------------

To update basic configuration (server name, database connection, languages, or set workers number or timeout), run:

.. code-block:: bash

    sudo dpkg-reconfigure geotrek-admin

The basic configuration is stored in ``/opt/geotrek-admin/var/conf/env`` file, not to be changed manually.
This file also contains the PostgreSQL authentification details, if you need to access your Geotrek-admin database.


Custom setting file
-------------------

Geotrek-admin advanced configuration is done in ``/opt/geotrek-admin/var/conf/custom.py`` file.

The list of all overridable setting and default values can be found
`there <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_.

After any change in ``custom.py``, run:

.. code-block:: bash

    sudo service geotrek restart

Sometimes you also have to run:

.. code-block:: bash

    sudo dpkg-reconfigure -u geotrek-admin

.. note::

    Don't override the ``os.getenv()`` settings as they are managed with Basic configuration.


NGINX configuration
-------------------

NGINX configuration is controlled by Geotrek-admin and will be erased at each upgrade.
Do not modify ``/etc/nginx/sites-available/geotrek.conf`` or ``/etc/nginx/sites-enable/geotrek.conf``.
Modify ``/opt/geotrek-admin/var/conf/nginx.conf.in`` instead. To update ``nginx.conf``, then run:

.. code-block:: bash

    sudo dpkg-reconfigure geotrek-admin


Activate SSL / HTTPS
--------------------

To activate https, you need firstly to change ``custom.py`` and add:

.. code-block:: python

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

After this, edit ``nginx.conf.in`` to add your certificate.

If you generate it with letsencrypt :
You can use certbot to add the certificate in your configuration.
But you will have to move the configuration automatically added into ``nginx.conf``, to the file ``nginx.conf.in`` in ``/opt/geotrek-admin/var/conf/`` directory.

You have to move the configuration to the file ``nginx.conf.in`` because ``nginx.conf`` is automatically changed during command ``dpkg-reconfigure geotrek-admin``.

.. note::

    You need to replace the ``$`` from Certbot with ``${DOLLAR}`` everywhere in the ``nginx.conf.in`` file, then run the command ``sudo dpkg-reconfigure geotrek-admin`` to regenerate the file.


Mandatory settings
------------------

Spatial reference identifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    SRID = 2154

Spatial reference identifier of your database. Default 2154 is RGF93 / Lambert-93 - France

*It should not be change after any creation of geometries.*

*Choose wisely with epsg.io for example*

.. _default-structure:

Default Structure
~~~~~~~~~~~~~~~~~

.. code-block:: python

    DEFAULT_STRUCTURE_NAME = "GEOTEAM"

Name for your default structure.

   *This one can be changed, except it's tricky.*

   * *First change the name in the admin (authent/structure),*
   * *Stop your instance admin.*
   * *Change in the settings*
   * *Re-run the server.*


Dynamic segmentation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    TREKKING_TOPOLOGY_ENABLED = True

Use dynamic segmentation or not.

`Dynamic segmentation <https://geotrek.readthedocs.io/en/latest/usage/editing-objects.html#segmentation-dynamique>`_ is used by default when installing Geotrek-admin.

With this mode, linear objects are built and stored related to paths.

Without this mode, linear geometry of objects is built and stored as an independent geographic object without relation to paths.

So if you want to use Geotrek-admin without dynamic segmentation, set TREKKING_TOPOLOGY_ENABLED to false after installation.

Do not change it again to true after setting it to false.


Translations
~~~~~~~~~~~~

.. code-block:: python

    LANGUAGE_CODE = 'fr'

Language of your interface.

.. code-block:: python

   MODELTRANSLATION_LANGUAGES = ('en', 'fr', 'it', 'es')

Languages of your project. It will be used to generate fields for translations. (ex: description_fr, description_en)

*You won't be able to change it easily, avoid to add any languages and do not remove any.*


Spatial extents
~~~~~~~~~~~~~~~

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

*If you extend spatial extent, don't forget to load a new DEM that covers all the zone.*
*If you shrink spatial extent, be sure there is no element in the removed zone or you will no more be able to see and edit it.*

In order to check your configuration of spatial extents, a small tool
is available at ``http://<server_url>/tools/extents/``.

.. note::

    Administrator privileges are required.


Users management
----------------

See :ref:`user management section in usage <user-management-section>`.


Database users
--------------

It is not safe to use the ``geotrek`` user in QGIS, or to give its password to
many collaborators.

A wise approach, is to create a *read-only* user, or with specific permissions.

With *pgAdmin*, you can create database users like this:

::


    CREATE USER lecteur WITH ENCRYPTED PASSWORD 'passfacile';
    GRANT CONNECT ON DATABASE geotrekdb TO lecteur;

And give them permissions by schema :

::

    GRANT USAGE ON SCHEMA public TO lecteur;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO lecteur;


You can also create groups, etc. See PostgreSQL documentation.

