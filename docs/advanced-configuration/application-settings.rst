.. _application-settings:

======================
Application settings
======================

Email settings
----------------

Geotrek-admin will send emails:

* to administrators when internal errors occur
* to managers when a feedback report is created

Email configuration takes place in ``/opt/geotrek-admin/var/conf/custom.py``, where you control
recipients emails (``ADMINS``, ``MANAGERS``) and email server configuration.

You can test your configuration with the following command. A fake email will
be sent to the managers:

.. md-tab-set::
    :name: sendtestemail-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: bash
    
                sudo geotrek sendtestemail --managers
    .. md-tab-item:: Example

         .. code-block:: bash
    
                docker compose run --rm web ./manage.py sendtestemail --managers

.. _API:

API
----------------

API is public
~~~~~~~~~~~~~~

Set to ``True`` if you want the API V2 to be available for everyone without authentication (mandatory to use Geotrek-Rando). Set to ``False`` if you don't want to share through API informations marked as 'published'. 

.. md-tab-set::
    :name: api-is-public-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                API_IS_PUBLIC = False

    .. md-tab-item:: Example

         .. code-block:: python
    
                API_IS_PUBLIC = True

.. note::
  - This API provides access to promotion content (Treks, POIs, Touristic Contents ...). 
  - Set to ``False`` if Geotrek is intended to be used only for managing content and not promoting them.
  - This setting does not impact the Path endpoints, which means that the Paths informations will always need authentication to be display in the API, regardless of this setting.


Swagger API documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to enable swagger module to auto-document API, in the custom settings file, add the following code : 

Enable API V2 documentation::

    INSTALLED_APPS += ('drf_yasg', )

Then run ``sudo dpkg-reconfigure -u geotrek-admin``.
The API swagger documentation is now availaible here : ``<GEOTREK_ADMIN_URL>/api/v2``

Share services between several Geotrek instances
--------------------------------------------------

As explained :ref:`in the design section <design-section>`, *Geotrek-admin* relies
on several services. They are generic and reusable, and can thus be shared
between several instances, in order to save system resources for example.

A simple way to achieve this is to install one instance with everything
as usual (*standalone*), and plug the other instances on its underlying services.

Capture and conversion
~~~~~~~~~~~~~~~~~~~~~~~

If you want to use external services, in ``.env``, add following variables:

.. code-block:: python

    CAPTURE_HOST=x.x.x.x
    CAPTURE_PORT=XX
    CONVERSION_HOST=x.x.x.x
    CONVERSION_PORT=XX

Then, you can delete all screamshotter and convertit references in ``docker-compose.yml``.

Shutdown useless services
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that your instances point the shared server. You can shutdown the useless
services on each instance.

Start by stopping everything:

.. md-tab-set::
    :name: shutdown-service-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: bash
    
                sudo systemctl stop geotrek

    .. md-tab-item:: Example

         .. code-block:: bash
    
                docker compose down

Control number of workers and request timeouts
---------------------------------------------------

By default, the application runs on 4 processes, and timeouts after 30 seconds.

To control those values, edit and fix your ``docker-compose.yml`` file in web and api section.

To know how many workers you should set, please refer to `gunicorn documentation <http://gunicorn-docs.readthedocs.org/en/latest/design.html#how-many-workers>`_.

External authent
------------------

You can authenticate user against a remote database table or view.

To enable this feature, fill these fields in ``/opt/geotrek-admin/var/conf/custom.py``:

.. code-block:: python

    AUTHENT_DATABASE = 'authent'
    DATABASES['authent'] = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '<database name>',
        'USER': '<user name>',
        'PASSWORD': '<password>',
        'HOST': '<host>',
        'PORT': '<port>',
    }
    AUTHENT_TABLENAME = '<table name>'
    AUTHENTICATION_BACKENDS = ['geotrek.authent.backend.DatabaseBackend']

Expected columns in table/view are :

* ``username`` : string (*unique*)
* ``first_name`` : string
* ``last_name``: string
* ``password`` : string (simple md5 encoded, or full hashed and salted password)
* ``email`` : string
* ``level`` : integer (1: readonly, 2: redactor, 3: path manager, 4: trekking manager, 5: management and trekking editor, 6: administrator)
* ``structure`` : string
* ``lang`` : string (language code)

.. note::
  - The schema used in ``AUTHENT_TABLENAME`` must be in the user search_path (``ALTER USER $geotrek_db_user SET search_path=public,userschema;``)
  - User management will be disabled from Administration backoffice.
  - In order to disable remote login, just comment *AUTHENTICATION_BACKENDS* line in settings file, and restart instance (see paragraph above).
  - Geotrek-admin can support many types of users authentication (LDAP, oauth, ...), contact us for more details.

Custom SQL
-----------

Put your custom SQL in a file name ``/opt/geotrek-admin/var/conf/extra_sql/<app name>/<pre or post>_<script name>.sql``

* app name is the name of the Django application, eg. trekking or tourism
* ``pre_``… scripts are executed before Django migrations and ``post_``… scripts after
* script are executed in INSTALLED_APPS order, then by alphabetical order of script names

