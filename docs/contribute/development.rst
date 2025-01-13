.. _development-section:

===========
Development
===========

Quickstart
==========

Download or git clone the source code of Geotrek-admin.

::

    cp .env.dist .env
    # Edit .env if need be
    docker compose build
    docker compose run --rm web update.sh
    docker compose run --rm web load_data.sh
    docker compose run --rm web ./manage.py createsuperuser
    docker compose up

Edit ``/etc/hosts`` file to add ``geotrek.local`` alias to ``127.0.0.1``

Go to ``http://geotrek.local:8000`` in your browser

PDF generation might not work unless you use this domain and is correctly set to ``SERVER_NAME`` variable in your ``.env`` file.

Install git hooks
=================

* Several git hooks are available to prevent pushing to master branch or launch quality tests before committing. Install them with following commands:

::

    ln -s -f ../../.githooks/pre-push .git/hooks/pre-push
    ln -s -f ../../.githooks/pre-commit .git/hooks/pre-commit

Adding or upgrade dependencies
==============================

Consider using pip-tools to manage dependencies.

* add your dependencies in ``setup.py`` for general dependencies, ``dev-requirements.in`` for dev dependencies, then run:

.. md-tab-set::
    :name: upgrade-dependencies-tabs

    .. md-tab-item:: With Make

            .. code-block:: python
    
                make deps

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web pip-compile
                docker compose run --rm web pip-compile dev-requirements.in

Model modification
==================

::

   docker compose run --rm web ./manage.py makemigrations <appName>
   docker compose run --rm web ./manage.py migrate

.. note::

    Add migration file to source control.

Definition of Done for new model fields
---------------------------------------

When updating or adding a new field ``my_field`` to a model ``MyModel``, please proceed with the following changes to ensure this field is included in existing functionalities.

**In** ``MyModel`` **class** :

- If ``my_field`` is a ``ForeignKey``:

  - make sure to override ``related_name`` with an explicit set name

  - if ``my_field`` causes cascading deletion (argument ``on_delete=models.CASCADE``), make sure to log potential deletions (see example ``log_cascade_deletion_from_sector_practice`` in ``geotrek/outdoor/models.py``)

- Make sure to set ``verbose_name`` on the field and add proper translations in ``.po`` files

**Outside of model class** :

- To display ``my_field`` in detail views, add a row in template ``mymodel_detail_attributes.html``

- Look for form class ``MyModelForm(CommonForm)`` :

  - If it exists, and field needs to be included in form, add ``my_field`` to form attributes (``fields`` on the ``Meta`` class, sometimes ``fieldslayout`` as well).

  - If field is added to the form **and is optional**, please add ``my_field`` to the documentation for hideable form fields : in ``docs/advanced-configuration.rst`` look for ``HIDDEN_FORM_FIELDS['mymodel']`` and add your field to the list.

- Look for list view class ``MyModelList(CustomColumnsMixin, MapEntityList)`` :

  - If it exists, please add ``my_field`` to the documentation for custom list view columns : in ``docs/advanced-configuration.rst`` look for ``COLUMNS_LISTS['mymodel_view']`` and add your field to the list.

  - If it exists, and if you wish to display a column for ``my_field`` in the list view for this model by default, simply add ``my_field`` to ``default_extra_colums`` on this class.

- Look for exports view class ``MyModelFormatList(MapEntityFormat, MyModelList)`` :

  - If it exists, please add ``my_field`` to the documentation for custom list exports columns : in ``docs/advanced-configuration.rst`` look for ``COLUMNS_LISTS['mymodel_export']`` and add your field to the list.

  - If it exists, and if you wish to display a column for ``my_field`` in CSV/SHP exports for this model by default, simply add ``my_field`` to ``default_extra_colums`` on this class.

- Follow the documentation you just edited to test that custom columns and hideable fields do work properly with your new field.

- Look for sql file defaults ``geotrek/{app_name}/sql/post_90_defaults.sql`` :

  - If it exists find your modelname in the list and depending on the default value alter column ``my_field`` or add ``-- my_field``

  - If the modelname doesn't exist, create a new section (even if you don't need to alter column)

- Look for sql view file ``geotrek/{app_name}/sql/post_20_views.sql`` and update the view for your model with an alias for the new field

**In API v2** :

If ``MyModel`` is served by APIv2, make sure to add a serializer for the new field in ``geotrek/api/v2/serializers.py`` and if you wish to filter on this field, create a new filter and add it to the right ``ViewSet`` under ``geotrek/api/v2/views``, using attribute ``filter_backends``.

When updating a field ``my_field`` in a model ``MyModel`` for ``new_field``, check if this field is translated in ``geotrek/{app}/translation.py``.

If so, you need to add a migration just after the migration generated by Django.
This migration should rename the old fields generated by modeltranslation ``my_field_en`` by ``new_field_en``
(example : ``geotrek/trekking/migrations/0014_auto_20200228_2127.py``)

Check quality
=============

**Flake8**

.. md-tab-set::
    :name: flake-tabs

    .. md-tab-item:: With Make

            .. code-block:: python
    
                make flake8

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm web flake8 geotrek

Run tests
=========

**Django tests :**

To run all test suites and report global coverage:

::

    make coverage

To run a specific test suite:

.. md-tab-set::
    :name: test-specific-tabs

    .. md-tab-item:: With Make

            .. code-block:: python
    
                make coverage

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm -e ENV=tests web ./manage.py test

You can run test with non dynamic segmentation :

.. md-tab-set::
    :name: test-nds-tabs

    .. md-tab-item:: With Make

            .. code-block:: python
    
                make tests_nds

    .. md-tab-item:: With Docker

         .. code-block:: python
    
                docker compose run --rm -e ENV=tests_nds web ./manage.py test

**Cypress tests :**

Create an empty project with Docker :

::

    docker compose down
    docker compose up -d

Install elements for the cypress tests

::

    make load_data
    make load_test_integration
    make load_test_integration_workflow

Move in cypress folder and install

::

    cd cypress
    npm ci

Launch tests

::

    ./node_modules/.bin/cypress run

Pictures of the problem and videos are generated in ``cypress/videos`` and ``cypress/screenshots``.

Setup to use screamshotter-related features locally
===================================================

Use the domain defined in ``SERVER_NAME`` in your ``.env`` to reach your local Geotrek-admin web instance. By default the address is ``http://geotrek.local:8000``.

Database reset
==============

Data only:

::

   docker compose run --rm web ./manage.py flush

Restore existing Database
=========================

Assuming a dump of your database is located in your project directory:

::

   docker compose run --rm web pg_restore --clean --no-owner --no-acl -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB /opt/geotrek-admin/<path_to_backup>.dump

Restore your ``./var/conf/`` project files, and data files into ``./var/media``.

Then run a synchronization.

Mapentity development
=====================

See `Django-Mapentity documentation <https://django-mapentity.readthedocs.io/>`_

UML diagrams of data model
==========================

UML diagrams of Geotrek-admin data models are available in `docs/data-model <https://github.com/GeotrekCE/Geotrek-admin/tree/master/docs/data-model>`_ directory.
To regenerate them from PostgreSQL, install postgresql-autodoc and graphviz Ubuntu packages
and run ``make uml``.
