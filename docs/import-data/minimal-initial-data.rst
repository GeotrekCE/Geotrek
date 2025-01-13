.. _minimal-initial-data:

======================
Minimal initial data
======================

.. abstract:: Keywords

   ``IGN``, ``INPN``


.. IMPORTANT::
   These data are the minimal initial data required to have a functional Geotrek-admin after completing the :ref:`installation <installation>`.

.. _altimetry-dem-source-list:

Altimetry (DEM)
===============

**Data sources recommandations**

.. list-table:: Altimetric Data
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - **Name**
     - **Provider**
     - **Coverage**
     - **Resolution**
     - **Format**
   * - `BD Alti <https://geoservices.ign.fr/bdalti>`_
     - IGN
     - Departmental
     - 25 m
     - ``.asc``
   * - `RGE Alti <https://geoservices.ign.fr/rgealti#telechargement5m>`_
     - IGN
     - Departmental
     - 1 m or 5 m
     - ``.asc``

.. seealso::

	Refer to :ref:`this section <altimetry-dem>` to learn more about loading a DEM file in your Geotrek-admin.

Areas
=======

.. _cities-source-list:

Cities
-------

**Data sources recommandations**

.. list-table:: Administrative Boundaries Data
   :widths: 20 15 20 15 15 15
   :header-rows: 1

   * - **Name**
     - **Provider**
     - **Coverage**
     - **Scale**
     - **Format**
     - **Update Frequency**
   * - `Admin Express <https://geoservices.ign.fr/adminexpress#telechargement>`_ (COMMUNE)
     - IGN
     - Metropolitan France, Overseas Territories
     - Municipality
     - Geopackage, Shapefile
     - Annually
   * - `Administrative Boundaries <https://github.com/datagouv/decoupage-administratif#via-des-urls>`_ ➡ `Communes <https://unpkg.com/@etalab/decoupage-administratif/data/communes.json>`_
     - Etalab
     - Metropolitan France, Overseas Territories
     - Municipality
     - GeoJSON
     - Annually

.. seealso::

	Refer to :ref:`this section <import-cities>` to learn more about loading cities in your Geotrek-admin.

.. _districts-source-list:

Districts
----------

**Data sources recommandations**

.. list-table:: Administrative Boundaries Data (EPCI)
   :widths: 20 15 20 15 15 15
   :header-rows: 1

   * - **Name**
     - **Provider**
     - **Coverage**
     - **Scale**
     - **Format**
     - **Update Frequency**
   * - `Admin Express <https://geoservices.ign.fr/adminexpress#telechargement>`_ (EPCI)
     - IGN
     - Metropolitan France, Overseas Territories
     - EPCI
     - Geopackage, Shapefile
     - Annually
   * - `Administrative Boundaries <https://github.com/datagouv/decoupage-administratif#via-des-urls>`_ ➡ `EPCI <https://unpkg.com/@etalab/decoupage-administratif/data/epci.json>`_
     - Etalab
     - Metropolitan France, Overseas Territories
     - EPCI
     - GeoJSON
     - Annually

Districts are not necessarily administrative boundaries. They can be intercommunalities, departments, parks, or natural regions. The advantage of importing them as Districts is that you will be able to filter them in Geotrek-rando, which will not be possible with Restricted areas.

.. seealso::

	Refer to :ref:`this section <import-districts>` to learn more about loading districts in your Geotrek-admin.

.. _restrictedareas-source-list:

Restricted areas
-----------------

**Data sources recommandations**

.. list-table:: Protected Areas Data
   :widths: 20 15 20 15 15
   :header-rows: 1

   * - **Name**
     - **Provider**
     - **Coverage**
     - **Format**
     - **Update Frequency**
   * - `Natura 2000 <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/nat/natura>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `ZNIEFF1 <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/inv/znieff1>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `ZNIEFF2 <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/inv/znieff2>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `ZNIEFF1 Mer <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/inv/znieff1_mer>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `ZNIEFF2 Mer <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/inv/znieff2_mer>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `Biotope Protection Orders <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/apb>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `National Nature Reserves <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/rnn>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `Regional Nature Reserves <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/rnr>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually
   * - `Biological Reserves <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/rb>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually

.. seealso::

	Refer to :ref:`this section <import-restricted-areas>` to learn more about loading restricted areas in your Geotrek-admin.

.. _sensitiveareas-source-list:

Sensitive areas
----------------

**Data source recommandation**

.. list-table:: Sensitive Natural Areas Data
   :widths: 20 15 20 15 15
   :header-rows: 1

   * - **Name**
     - **Provider**
     - **Coverage**
     - **Format**
     - **Update Frequency**
   * - `Sensitive Natural Areas <https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ap/ens>`_
     - INPN
     - Metropolitan France, Overseas Territories
     - Shapefile
     - Annually

.. seealso::

	Refer to :ref:`this section <sensitive-areas-import>` to learn more about loading sensitive areas in your Geotrek-admin.
