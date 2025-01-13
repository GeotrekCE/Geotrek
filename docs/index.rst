Geotrek-admin's documentation
=============================

**Geotrek-admin** is a web application designed to manage, centralize, and structure geographical and touristic information for your territory. It is the back-office application of the Geotrek ecosystem.

.. image:: http://geotrek.fr/assets/img/screen-1.png
   :align: center
   :alt: Interface de Geotrek-admin

With **Geotrek-admin**, you can:

- Manage treks, touristic information, and related content (media, descriptions, etc.).
- Organize your data with maps, layers, and metadata.
- Export content to various public interfaces, such as Geotrek-rando or printed topoguides.

You can explore **Geotrek-admin** in action through the demonstration website:

- `https://demo-admin.geotrek.fr/ <https://demo-admin.geotrek.fr/>`_ (demo / demo)

**Geotrek-admin** is built on Django and leverages a PostGIS database for handling geographical data. It serves as the data source for Geotrek-rando, Geotrek-widget, and other tools of the Geotrek ecosystem.

.. seealso::
    Learn more about Geotrek-admin in the :ref:`general documentation (french) <qu-est-ce-que-geotrek>`.

.. toctree::
    :caption: 💡 A propos
    :hidden:

    about/geotrek.rst

.. toctree::
    :caption: 🚀 Manuel d'utilisation
    :hidden:

    user-manual/overview.rst
    user-manual/interfaces.rst
    user-manual/management-modules.rst
    user-manual/touristic-modules.rst 
    user-manual/editing-objects.rst
    user-manual/configuration-ttw.rst
    user-manual/apis.rst
    user-manual/static-pages.rst

.. toctree::
    :caption: 💡 Tutoriels
    :hidden:

    tutorials/vizualize-data-in-qgis.rst
    tutorials/update-basemaps-layers.rst
    tutorials/topologies-issues.rst

.. toctree::
    :caption: 🔧 Installation & configuration
    :hidden:

    installation-and-configuration/installation
    installation-and-configuration/upgrade
    installation-and-configuration/configuration
    installation-and-configuration/maintenance
    installation-and-configuration/exploitation-commands
    installation-and-configuration/synchronization

.. toctree::
    :caption: ⚙️ Advanced configuration
    :hidden:

    advanced-configuration/application-settings
    advanced-configuration/map-settings
    advanced-configuration/modules-and-components
    advanced-configuration/feedback-report-settings
    advanced-configuration/attachments
    advanced-configuration/interface
    advanced-configuration/edition
    advanced-configuration/settings-for-geotrek-rando
    advanced-configuration/settings-for-geotrek-mobile

.. toctree::
    :caption: 🗃️ Import data
    :hidden:

    import-data/minimal-initial-data
    import-data/import-dem-raster
    import-data/import-paths
    import-data/import-areas
    import-data/import-touristic-data-systems
    import-data/import-other-data
    import-data/import-aggregator

.. toctree::
    :caption: ✨ Contribute
    :hidden:

    contribute/contributing
    contribute/guidelines
    contribute/development
    contribute/translating
    contribute/documentation
    contribute/design

.. toctree::
    :caption: 📝 Others
    :hidden:

    others/troubleshooting
    others/authors
    changelog
