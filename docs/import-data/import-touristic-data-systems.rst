.. _import-from-touristic-data-systems:

=======================
Touristic Data Systems
=======================

.. abstract:: Keywords

   ``SIT``, ``parser``, ``command line``, ``import en ligne de commande``


Real-time integration
======================

Geotrek-admin integrates with various Tourism Information Systems (SIT) such as Apidae, Tourinsoft, and others, enabling real-time retrieval of data entered by tourism offices. This includes information on points of interest, accommodations, cultural heritage, and more.

These imported data elements are automatically linked to nearby treks, regardless of activity type (trekking, trail running, mountain biking, cycling, gravel, climbing, rafting, etc.). 

This seamless integration enriches the descriptive pages of routes, ensuring that users benefit from comprehensive and up-to-date information with no additional effort required from administrators or agents.

.. _generic-settings-for-your-parser:

Generic settings for your parser
=================================

This settings may be overriden when you define a new parser:

- ``label`` parser display name (default: ``None``)
- ``model`` import content with this model (default: ``None``)
- ``filename`` file imported if no url (default: ``None``)
- ``url`` flow url imported from if no filename (default: ``None``)
- ``simplify_tolerance`` (default: ``0``)  # meters
- ``update_only`` don't create new contents (default: ``False``)
- ``delete`` (default: ``False``)
- ``duplicate_eid_allowed`` if True, allows differents contents with same eid (default: ``False``)
- ``fill_empty_translated_fields`` if True, fills empty translated fields with same value  (default: ``False``)
- ``warn_on_missing_fields`` (default: ``False``)
- ``warn_on_missing_objects`` (default: ``False``)
- ``separator`` (default: ``'+'``)
- ``eid`` field name for eid (default: ``None``)
- ``provider`` (default: ``None``)
- ``fields`` (default: ``None``)
- ``m2m_fields``  (default: ``{}``)
- ``constant_fields`` (default: ``{}``)
- ``m2m_constant_fields`` (default: ``{}``)
- ``m2m_aggregate_fields`` (default: ``[]``)
- ``non_fields`` (default: ``{}``)
- ``natural_keys`` (default: ``{}``)
- ``field_options`` (default: ``{}``)
- ``default_language`` use another default language for this parser (default: ``None``)

.. _start-import-from-command-line:

Start import from command line
===============================

Just run:

.. md-tab-set::
    :name: import-from-hebergement-parser-tabs

    .. md-tab-item:: With Debian

         .. code-block:: python

          sudo geotrek import HebergementParser

    .. md-tab-item:: With Docker

         .. code-block:: python
    
          docker compose run --rm web ./manage.py import  HebergementParser

Change ``HebergementParser`` to match one of the class names in ``var/conf/parsers.py`` file.
You can add ``-v2`` parameter to make the command more verbose (show progress).
Thank to ``cron`` utility you can configure automatic imports.

.. _start-import-from-geotrek-admin-ui:

Start import from Geotrek-admin UI
===================================

Open the top right menu and clic on ``imports``.

.. _import-from-apidae:

Import from APIDAE
====================

Import touristic content 
------------------------

To import touristic content from APIDAE (ex-SITRA), edit ``/opt/geotrek-admin/var/conf/parsers.py`` file with the following content:

::

    from geotrek.tourism.parsers import TouristicContentApidaeParser

    class HebergementParser(TouristicContentApidaeParser):
        label = "Hébergements"
        api_key = 'xxxxxxxx'
        project_id = 9999
        selection_id = 99999
        category = "Hébergement"
        type1 = ["Camping"]
        type2 = ["3 étoiles", "Tourisme et Handicap"]  # just remove this line if no type2

Then set up appropriate values:

* ``label`` at your convenience,
* ``api_key``, ``project_id`` and ``selection_id`` according to your APIDAE (ex-SITRA) configuration
* ``category``, ``type1`` and ``type2`` (optional) to select in which Geotrek category/type imported objects should go
* You can add ``delete = True`` in your class if you want to delete objects in Geotrek databases that has been deleted in your Apidae selection. It will only delete objects that match with your class settings (category, types, portal, provider...)
* You can also use the class ``HebergementParser`` if you only import accomodations
* See `/geotrek/tourism/parsers.py/ <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/tourism/parsers.py/>`_  file for details about Parsers

You can duplicate the class. Each class must have a different name.

To apply changes, you may have to run ``sudo service geotrek restart``.

Import treks
------------

A parser implementation is available to import Treks from APIDAE. Use it by defining a subclass of ``geotrek.trekking.parsers.ApidaeTrekParser`` in your ``var/conf/parsers.py`` configuration file as shown above.

You'll have to configure how to access your APIDAE data: ``api_key``, ``project_id`` and ``selection_id`` (those are setting attributes from the APIDAE base parser).

The ``practices_mapped_with_activities_ids`` and ``practices_mapped_with_default_activities_ids`` attributes define default mapping with the trekking module data fixture. You may override this to match your own types of Trek Practice.

Example of a parser configuration :

::

    class ImportTreksApidae(TrekParser):
        label = "Import trek with eid"
        label_fr = "Import itinéraires avec identifiant externe"
        label_en = "Import trek with eid"
        eid = 'eid'

.. _import-from-tourinsoft:

Import from Tourinsoft
======================

Tourinsoft is a Tourism Information System developed by the company Ingénie for tourism organizations in France, such as Departmental Tourism Committees (CDT), Tourism Development Agencies (ADT), and Tourist Offices. This system allows for the centralization, management, and standardized dissemination of tourism-related information.

Example of a parser configuration :

::

    class RestaurationParser(TouristicContentTourinsoftParser):
        """Restauration parsers"""
        label = "Restauration"
        category = "Restauration"
        url = "<Touristic content data feed URL"  # In the form https://api-v3.tourinsoft.com/api/syndications/decibelles-data.tourinsoft.com/<id>?format=json"

.. _import-from-cirkwi:

Import from Cirkwi
===================

The functionality for importing treks and touristic content from Cirkwi was developed and integrated into `version 2.111.0 of Geotrek-admin <https://github.com/GeotrekCE/Geotrek-admin/releases/tag/2.111.0/>`_.

.. note ::

    - By default, imported content is automatically published.
    - To enable the integration of this data, you need to modify the `parsers.py` file to create a dedicated parser and query a feed provided by Cirkwi.

The following parsers have been developed to facilitate data import from Cirkwi into Geotrek-admin:

- **Trek Parser**: Allows the integration of treks from Cirkwi into Geotrek. This parser is compatible with instances operating in :ref:`Non-Dynamic Segmentation <configuration-dynamic-segmentation>` (NDS) mode only. 

Example of a parser configuration :

::

    class ImportTreksCirkwi(CirkwiTrekParser):
        url = "<Treks data feed URL>"  # In the form https://ws.cirkwi.com/flux/<user>/<code>/circuits.php?widget-id=<id>
        user = "<Username>"
        password = "<Password>"
        auth = (user, password)
        label = "Cirkwi's treks"
        delete = True
        create = True
        provider = "Cirkwi"


- **Touristic content Parser**: Enables the import of touristic content from Cirkwi into Geotrek. 

Example of a parser configuration :

::

    class ImportTouristicContentCirkwi(CirkwiTouristicContentParser):
        url = "<Treks data feed URL>"  # In the form https://ws.cirkwi.com/flux/<user>/<code>/circuits.php?widget-id=<id>"
        user = "<Username>"
        password = "<Password>"
        auth = (user, password)
        label = "Cirkwi's touristic content"
        delete = True
        create = True
        provider = "Cirkwi"
        # results_path = "circuit/pois/poi"  # Uncomment this line if the touristic content to be imported come from the same feed as  treks

.. seealso::

  To import Geotrek treks and POIs into Cirkwi's format you can check :ref:`this section (french)  <geotrek-ignrando-cirkwi-api>`.

.. _import-from-lei:

Import from LEI
================

To import touristic content or touristic event from LEI , create (or update) ``/opt/geotrek-admin/var/conf/parsers.py`` file with the following content:

::

    from geotrek.tourism.parsers import LEITouristicContentParser, LEITouristicEventParser

    class XXXLEIContentParser(LEITouristicContentParser):
        label = "LEI TouristicContent"
        url = "https://url.asp"

    class XXXLEIEventParser(LEITouristicEventParser):
        label = "LEI TouristicEvent"
        url = "https://url.asp"

.. _import-from-marque-esprit-parc:

Import from Marque Esprit Parc
===============================

To import touristic content from Esprit Parc national database, create (or update) ``/opt/geotrek-admin/var/conf/parsers.py`` file with the following content:

::

    from geotrek.tourism.parsers import EspritParcParser

    class XXXEspritParcParser(EspritParcParser):
        label = "Marque Esprit Parc"
        url = "https://gestion.espritparcnational.com/ws/?f=getProduitsSelonParc&codeParc=XXX"

Then set up appropriate values:

* ``XXX`` by unique national park code (ex: PNE)

You can duplicate the class. Each class must have a different name.

In this case categories and types in Geotrek database have to be the same as in Esprit parc database. Otherwise missing categories and types will be created in Geotrek database.

Imported contents will be automatically published and approved (certified). 

If you use an url that filters a unique category, you can change its name. Example to get only Honey products and set the Geotrek category and type in which import them:

::

    class MielEspritParcParser(EspritParcParser):
        label = "Miel Esprit Parc national"
        url = "https://gestion.espritparcnational.com/ws/?f=getProduitsSelonParc&codeParc=XXX&typologie=API"
        constant_fields = {
            'category': "GeotrekCategoryName",
            'published': True,
            'approved': True,
            'deleted': False,
        }
        m2m_constant_fields = {
            'type1': "GeotrekTypeName",
        }

.. _multiple-imports:

Multiple imports
=================

When you need to import data for the same object found in 2 different parsers, you can to force the aggregation of both values in many to many relationship case.
It can be interesting with portals for example.

Parameters for the aggregation : ``m2m_aggregate_fields``

Here is an example with 2 parsers :

::

    class Portal_1Parser(XXXParser):
        portal = "portal_1"

    class AggregateParser(XXXParser):
        portal = "portal_2"
        m2m_aggregate_fields = ["portal"]

Then, when you import the first parser ``Portal_1Parser``, you get multiple objects with ``portal_1`` as portal.
If any object of the ``Portal_1Parser`` is also in ``AggregateParser``, fields in ``m2m_aggregate_fields`` will have their values not be replaced but aggregated.
Then your object in both portals will have as portal: ``portal_1, portal_2``

* Here in this example whenever you import the first parser ``Portal_1Parser``, portals are replaced because ``m2m_aggregate_fields`` is not filled. Then, be careful to import parsers in the right order or add the param ``m2m_aggregate_fields`` on all parsers.

If you need to cancel the aggregation of portals, remove param ``m2m_aggregate_fields``.

.. _importing-from-multiple-sources-with-deletion:

Importing from multiple sources with deletion
==============================================

When importing data for the same model using two (or more) different sources, the ``provider`` field should be used to differenciate between sources, allowing to enable object deletion with ``delete = True`` without causing the last parser to delete objects created by preceeding parsers.

In the following example, ``Provider_1Parser`` and ``Provider_2Parser`` will each import their objects, set the ``provider`` field on these objects, and only delete objects that disappeared from their respective source since last parsing.

.. code-block:: python

    class Provider_1Parser(XXXXParser):
        delete = True
        provider = "provider_1"

    class Provider_2Parser(XXXParser):
        delete = True
        provider = "provider_2"

.. important::

    - It is recommended to use ``provider`` from the first import. 
    - Do not add a ``provider`` field to preexisting parsers that already imported objects, or you will have to manually set the same value for ``provider`` on all objects already created by this parser. 
    - If a parser does not have a ``provider`` value, it will not take providers into account, meaning that it could delete objects from preceeding parsers even if these other parsers do have a ``provider`` themselves.

The following example would cause ``NoProviderParser`` to delete objects from ``Provider_2Parser`` and ``Provider_1Parser``.

.. code-block:: python

    class Provider_1Parser(XXXXParser):
        delete = True
        provider = "provider_1"

    class Provider_2Parser(XXXParser):
        delete = True
        provider = "provider_2"

    class NoProviderParser(XXXParser):
        delete = True
        provider = None # (default)

.. seealso::

  To set up automatic commands you can check the :ref:`Automatic commands section <automatic-commands>`.