.. _design-section:

======
Design
======

Architecture
------------

.. image:: ../images/architecture-1.0.png
    :width: 50%

* **Geotrek-admin**, the web application
* **Convertit**, a Web API to convert document and image formats (*.odt to .doc*, *.svg to .png*)
* **Screamshotter**, a Web API to perform Web pages screenshots (*map image exports*).


Main components
---------------

The whole project is built on top of *mapentity*, a generic application in charge of:

* Menus and models registry
* List/Detail/Create/Update/Delete views
* Filtering
* Map images exports
* File attachment
* Document export
* Shapefile/GPX/CSV serializers

For a Django model, we use the registry to activate all views and menus:

.. image:: ../images/mapentity.jpg
    :width: 50%

Business specific notions are implemented in Geotrek-admin respective applications:

* **common**: shared concepts between all applications (*Organism*, *utils*, ...)
* **authent**: groups, user, profile and structure notions. Optional external authent backend.
* **core**: paths, snapping, spatial referencing (topologies)
* **land**: physical types, competence, signage and work management
* **infrastructure**: buildings
* **signage**: signages and blades related content
* **maintenance**: interventions (on paths or on infrastructures) and projects
* **trekking**: POIs and treks
* **outdoor**: outdoor sites and courses
* **zoning**: static cities/districts/restricted areas layers
* **altimetry**: elevation, DEM
* **api**: manage all external communications interfaces (api v2, mobile)
* **cirkwi**: implementation of cirkwi related api
* **feedback**: feedbacks content, implementation of suricate workflow
* **flatpages**: flatpages models, used for publishing content on rando and mobile apps
* **sensitivity**: sensitive areas and species related content, link with Biodiv'Sport
* **tourism**: touristic contents and events, links with SIT (apidae, tourinsoft)


Django conventions twists
-------------------------

We have a couple of Django conventions infringements:

* SQL triggers everywhere: since Geotrek-admin database is to become the central storage
  component of all territory organisation data, it has to behave consistently whether data is
  modified through the Web application or raw access tools (pgadmin, QGIS).
  (For example, insertion & update timestamps, geometry computation or DEM wrapping.)
* Safe delete: update field ``deleted = True`` instead of performing actual delete in table.
  Requires every querysets to be filtered on deleted. (**TODO**: use dango-safedelete, `issue 813 <https://github.com/GeotrekCE/Geotrek-admin/issues/813>`_)


Main roles of PostgreSQL triggers
---------------------------------

Automatic computation of fields :

* Date insert/update
* Geometry computation of linear referencing (topologies)
* DEM elevation wrapping (3D length, slope, etc.)

Topological path network :

* Split paths at intersection
* Snap paths extremities
