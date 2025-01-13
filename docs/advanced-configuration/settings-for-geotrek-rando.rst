.. _settings-for-geotrek-rando:

===========================
Settings for Geotrek-rando
===========================

See the default values in `geotrek/settings/base.py <https://github.com/GeotrekCE/Geotrek-admin/blob/master/geotrek/settings/base.py>`_ for the complete list of available parameters.

.. _distances:

Distances
----------

Tourism intersection margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Distance to which tourist contents, tourist events, treks, pois, services will be displayed.

.. md-tab-set::
    :name: tourism-intersection-margin-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                TOURISM_INTERSECTION_MARGIN = 500 # meters

    .. md-tab-item:: Example

         .. code-block:: python
    
               TOURISM_INTERSECTION_MARGIN = 800 # meters

.. note:: 
  This distance can be changed by practice for treks in the admin.

Diving intersection margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Distance to which dives will be displayed.

.. md-tab-set::
    :name: diving-intersection-margin-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                DIVING_INTERSECTION_MARGIN = 500 # meters

    .. md-tab-item:: Example

         .. code-block:: python
    
               DIVING_INTERSECTION_MARGIN = 800 # meters

Limits
-------

Trek export POI list limit 
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Limit of the number of POIs on treks PDF.

.. md-tab-set::
    :name: trek-export-poi-list-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                TREK_EXPORT_POI_LIST_LIMIT = 14

    .. md-tab-item:: Example

         .. code-block:: python
    
               TREK_EXPORT_POI_LIST_LIMIT = 20

.. note:: 
  ``14`` is already a huge amount of POI, but it's possible to add more

Trek export information desk list limit 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Limit of the number of information desks on treks PDF.

.. md-tab-set::
    :name: trek-export-informationdesk-list-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                TREK_EXPORT_INFORMATION_DESK_LIST_LIMIT = 2

    .. md-tab-item:: Example

         .. code-block:: python
    
               TREK_EXPORT_INFORMATION_DESK_LIST_LIMIT = 5

.. note:: 
  You can put ``-1`` if you want all the information desks

Categories
-----------

Split treks categories by practice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the Geotrek-rando V2 website, treks practices will be displayed separately.

.. md-tab-set::
    :name: split-treks-categories-by-practices-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                SPLIT_TREKS_CATEGORIES_BY_PRACTICE = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               SPLIT_TREKS_CATEGORIES_BY_PRACTICE = True

.. note:: 
  Field order for each practices in admin will be taken in account

Split treks categories by accessibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the Geotrek-rando V2 website, accessibilites will be displayed separately.

.. md-tab-set::
    :name: split-treks-categories-by-accessibility-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                SPLIT_TREKS_CATEGORIES_BY_ACCESSIBILITY = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               SPLIT_TREKS_CATEGORIES_BY_ACCESSIBILITY = True

Split treks categories by itinerancy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the Geotrek-rando V2 website, if a trek has a children it will be displayed separately.

.. md-tab-set::
    :name: split-treks-categories-by-itinerancy-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                SPLIT_TREKS_CATEGORIES_BY_ITINERANCY = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               SPLIT_TREKS_CATEGORIES_BY_ITINERANCY = True

Split dives categories by practice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the Geotrek-rando V2 website, dives practices will be displayed separately.

.. md-tab-set::
    :name: split-dives-categories-by-practices-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                SPLIT_DIVES_CATEGORIES_BY_PRACTICE = True

    .. md-tab-item:: Example

         .. code-block:: python
    
               SPLIT_DIVES_CATEGORIES_BY_PRACTICE = False

Hide published treks in topologies 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the Geotrek-rando V2 website, treks near other are hidden.

.. md-tab-set::
    :name: hide-published-treks-in-topologies-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                HIDE_PUBLISHED_TREKS_IN_TOPOLOGIES = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               HIDE_PUBLISHED_TREKS_IN_TOPOLOGIES = True

Trek with POIs pictures
~~~~~~~~~~~~~~~~~~~~~~~~

It enables correlated pictures on Geotrek-rando V2 to be displayed in the slideshow.

.. md-tab-set::
    :name: trek-with-pois-pictures-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                TREK_WITH_POIS_PICTURES = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               TREK_WITH_POIS_PICTURES = True

Only external public PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~

On Geotrek-rando V2 website, only PDF imported with filetype "Topoguide"will be used and not autogenerated.

.. md-tab-set::
    :name: only-external-public-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                ONLY_EXTERNAL_PUBLIC_PDF = False

    .. md-tab-item:: Example

         .. code-block:: python
    
               ONLY_EXTERNAL_PUBLIC_PDF = True

**Order of all the objects without practices on Geotrek-rando website** :

.. code-block:: python

    TREK_CATEGORY_ORDER = 1
    ITINERANCY_CATEGORY_ORDER = 2
    DIVE_CATEGORY_ORDER = 10
    TOURISTIC_EVENT_CATEGORY_ORDER = 99

.. note:: 
  - All the settings about order are the order inside Geotrek-rando website.
  - Practices of diving, treks and categories of touristic contents are taken in account


