.. _edition:

==========
Edition
==========

WYSIWYG editor configuration
-----------------------------

Text form fields are enhanced using `TinyMCE <http://tinymce.com>`_.

Its configuration can be customized using advanced settings (see above paragraph).

TinyMCE default config
~~~~~~~~~~~~~~~~~~~~~~~

For example, in order to control which buttons are to be shown, and which tags are to be kept when cleaning-up, add this bloc :

Example::

    TINYMCE_DEFAULT_CONFIG = {
    'theme_advanced_buttons1': 'bold,italic,forecolor,separator,code',
    'valid_elements': "img,p,a,em/i,strong/b",
    }

.. note::
  - This will apply to all text fields.
  - For more information on configuration entries available, please refer to the official documentation of *TinyMCE version 3*.

Max characters count
---------------------

Mapentity for characters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``MAX_CHARACTERS_BY_FIELD`` setting to be able to define a maximum number of characters for text fields.

Example::

    MAPENTITY_CONFIG['MAX_CHARACTERS_BY_FIELD'] = { 
       "tourism_touristicevent": [{'field': 'description_teaser_fr', 'value': 50}, {'field': 'accessibility_fr', 'value': 25}],
       "trekking_trek": [{'field': 'description_teaser_fr', 'value': 150}],
    }

.. note::
  - This will apply field by field, language by language.
  - See `this issue <https://github.com/GeotrekCE/Geotrek-admin/issues/3844>`_ for details.

Copyright on pictures
------------------------

Thumbnail copyright format
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want copyright added to your pictures, change this parameter like so :

Example::

    THUMBNAIL_COPYRIGHT_FORMAT = "{title} {author}"

.. note::
  - This will apply to all text fields.
  - For more information on configuration entries available, please refer to the official documentation of *TinyMCE version 3*.

You can also add ``{legend}``: ``"{title}-:-{author}-:-{legend}"``

Thumbnail copyright size
~~~~~~~~~~~~~~~~~~~~~~~~~~

Change the size of thumbnail:

.. md-tab-set::
    :name: thumbnail-copyright-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                THUMBNAIL_COPYRIGHT_SIZE = 15

    .. md-tab-item:: Example

         .. code-block:: python
    
                THUMBNAIL_COPYRIGHT_SIZE = 20

Facebook configuration
-----------------------

When a content is shared to Facebook in Geotrek-rando V2,
it needs static html files built by synchronization (thanks to option ``--rando-url``).

In Facebook developper dashboard, create a Facebook app dedicated to Geotrek-rando and activate it.

.. image:: /images/facebookappid.png

Facebook App ID
~~~~~~~~~~~~~~~~

In ``custom.py`` set Facebook App ID:

Example::

    FACEBOOK_APP_ID = '<your Facebook AppID>'

**You can also override these settings:**

.. code-block:: python

    FACEBOOK_IMAGE = '/images/logo-geotrek.png'
    FACEBOOK_IMAGE_WIDTH = 200
    FACEBOOK_IMAGE_HEIGHT = 200

Override translations
----------------------

Translations are managed by `Weblate <https://weblate.makina-corpus.net/>`_  where you can contribute.
But you can also override default translation files available in each module
(for example those from trekking module available in ``/opt/geotrek-admin/lib/python3.6/site-packages/geotrek/trekking/locale/fr/LC_MESSAGES/django.po``).

Don't edit these default files, use them to find which words you want to override.

**Create the custom translations destination folder:**

- Create a ``django.po`` file in ``/opt/geotrek-admin/var/conf/extra_locale`` directory.
- You can do one folder and one ``django.po`` file for each language (example ``/opt/geotrek-admin/var/conf/extra_locale/fr/LC_MESSAGES/django.po`` for French translation overriding)

Override the translations that you want in these files.

**Example of content for the French translation overriding:**

.. code-block:: python

    # MY FRENCH CUSTOM TRANSLATION
    # Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
    # This file is distributed under the same license as the PACKAGE package.
    # FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
    #
    msgid ""
    msgstr ""
    "Report-Msgid-Bugs-To: \n"
    "POT-Creation-Date: 2018-11-15 15:32+0200\n"
    "PO-Revision-Date: 2018-11-15 15:33+0100\n"
    "Last-Translator: \n"
    "Language-Team: LANGUAGE <LL@li.org>\n"
    "MIME-Version: 1.0\n"
    "Content-Type: text/plain; charset=UTF-8\n"
    "Content-Transfer-Encoding: 8bit\n"
    "Project-Id-Verésion: PACKAGE VERSION\n"
    "Plural-Forms: nplurals=2; plural=(n > 1);\n"
    "Project-Id-Version: \n"
    "X-Generator: Poedit 1.5.4\n"

    msgid "City"
    msgstr "Région"

    msgid "District"
    msgstr "Pays"

**Apply changes (French translation in this example):**

.. code-block:: bash

    cd /opt/geotrek-admin/var/conf/extra_locale
    sudo chown geotrek. fr/LC_MESSAGES/
    sudo geotrek compilemessages
    sudo service geotrek restart

Override public PDF templates
------------------------------

PDF are generated from HTML templates, using `Django templating <https://docs.djangoproject.com/en/1.11/ref/templates/>`_.
Treks, touristic contents, touristic events, outdoor sites and courses can be exported in PDF files.

- Treks : ``geotrek/trekking/templates/trekking/trek_public_pdf.html``
- Touristic contents : ``geotrek/tourism/templates/tourism/touristiccontent_public_pdf.html``
- Touristic events : ``geotrek/tourism/templates/tourism/touristicevent_public_pdf.html``
- Outdoor sites : ``geotrek/outdoor/templates/outdoor/site_public_pdf.html``
- Outdoor courses : ``geotrek/outdoor/templates/outdoor/course_public_pdf.html``

Overriden templates have to be located in ``/opt/geotrek-admin/var/conf/extra_templates/<appname>``, with ``<appname>`` = ``trekking`` or ``tourism``.
To override trekking PDF for example, copy the file ``geotrek/trekking/templates/trekking/trek_public_pdf.html``
to ``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``. Or add inside your file::

    {% extends "trekking/trek_public_pdf.html" %}

These templates derive from base templates, which content is organized in blocks.
To override for example the description block of trek PDF, copy and change the ``{% block description }…{% endblock description %}``
in your ``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``.

It is also possible to use color defined for practice for pictogram by adding in your
``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html`` file::

    {% block picto_attr %}style="background-color: {{ object.practice.color }};"{% endblock picto_attr %}

CSS can be overriden like html templates: copy them to ``var/media/templates/trekking/`` or ``var/media/templates/tourism/`` folder
``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.css`` for example.

**You can also create a template for each portal.**

Add a folder ``portal_{id_portal}`` (portal ids are located in the portal url path ``/admin/common/targetportal/{id_portal}``) in
``/opt/geotrek-admin/var/conf/extra_templates/<appname>``, as the first template, and add at the top of your file:

::

    {% extends "trekking/trek_public_pdf.html" %}

The template for a specific portal will use the modification made on the overriden template in  ``/opt/geotrek-admin/var/conf/extra_templates/<appname>``
( except if you change specific  block)

.. note::
  This modification is not mandatory, if you have multiple portal and you want to modify the template of only one portal, you create one folder for this specific portal

**You might need to use your own images in the PDF templates.**

Add your own images in ``/opt/geotrek-admin/var/conf/extra_static/images/``.

You can then use these images in your PDF templates with ``{% static 'images/file.jpg' %}``, after adding ``{% load static %}`` at the top of the file.

Example of a customised template (``/opt/geotrek-admin/var/conf/extra_templates/trekking/trek_public_pdf.html``) with a customised logo and URL:

::

    {% extends "trekking/trek_public_pdf.html" %}
    {% load static %}

    {% block logo %}
       <img src="{% static 'images/logo-gte.jpg' %}" alt="Grand tour des Ecrins">
    {% endblock %}
    {% block url %}
       <div class="main">Grand tour des Ecrins</div>
       <div class="geo"><a href="https://www.grand-tour-ecrins.fr">grand-tour-ecrins.fr</a></div>
    {% endblock url %}

.. note::
  The default template may change in the future versions. You will be in charge of porting the modification to your copy.

Test your modifications by exporting a trek or a content to PDF from Geotrek-admin application.

PDF as booklet
----------------

Use booklet for PDF:

.. md-tab-set::
    :name: use-booklet-pdf-tabs

    .. md-tab-item:: Default configuration

            .. code-block:: python
    
                USE_BOOKLET_PDF = False

    .. md-tab-item:: Example

         .. code-block:: python
    
                USE_BOOKLET_PDF = True

.. note:: 
  - During the synchro, pois details will be removed, and the pages will be merged.
  - It is possible to customize the pdf, with trek_public_booklet_pdf.html.

Custom font in public document template
----------------------------------------

In order to use custom fonts in trek PDF, it is necessary to install the
font files on the server.

*Microsoft* fonts like *Arial* and *Verdana* can be installed via the package
manager:

::

    sudo apt-get install ttf-mscorefonts-installer

For specific fonts, copy the ``.ttf`` (or ``.otf``) files into the folder
``/usr/local/share/fonts/custom/`` as root, and run the following command:

.. code-block:: bash

    fc-cache

For more information, check out Ubuntu documentation.

Custom colors in public document template
------------------------------------------

Mapentity for custom colors in PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Trek export geometries are translucid red by default. In order to control the apparence of objects in public trek PDF exports, use the following setting:

Example::

    MAPENTITY_CONFIG['MAP_STYLES']['print']['path'] = {'weight': 3}

See *Leaflet* reference documentation for detail about layers apparence.

Primary color in PDF templates
-------------------------------

Primary color
~~~~~~~~~~~~~~

You can override ``PRIMARY_COLOR`` to change emphase text in PDF export.

Example::

    PRIMARY_COLOR = "#7b8c12"

.. note:: 
  Beware of contrast, white colour is used for text so we advise you to avoid light colour.

Custom logos
-------------

You might also need to deploy logo images in the following places :

* ``var/conf/extra_static/images/favicon.png``
* ``var/conf/extra_static/images/logo-login.png``
* ``var/conf/extra_static/images/logo-header.png``


