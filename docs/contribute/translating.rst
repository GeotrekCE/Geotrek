.. _translating-geotrek:

============
Translating
============

Geotrek-admin can be translated online on
`Makina Corpus Weblate instance <https://weblate.makina-corpus.net/projects/geotrek-admin/>`_

.. important::

  Translating work needs to be synchronized with Geotrek-admin. If you intend to use `Weblate <https://weblate.makina-corpus.net/projects/geotrek-admin/>`_, please inform us by creating a ticket or sending us an email (page contact geotrek.fr).

Getting started
---------------

Create an account
~~~~~~~~~~~~~~~~~

-  Click on "Register"

-  Fill the register form

   .. figure:: ../images/translating/weblate-create-account.png
      :alt: image

-  Validate your email

-  Fill the password

-  Then connect to weblate

`Official documentation <https://docs.weblate.org/en/latest/user/profile.html>`__
to create an account and manage your profile.

Browse by project
~~~~~~~~~~~~~~~~~~~

-  Go to “Project > Browse all projects”

   .. figure:: ../images/translating/weblate-project-menu.png
      :alt: image

-  Select Geotrek-admin project

-  Click on tab “Languages”

-  Choose the language to translate

   .. figure:: ../images/translating/weblate-list-of-languages.png
      :alt: image


Browse by language
~~~~~~~~~~~~~~~~~~~

You could also choose language first

-  Go to “Languages > Browse all languages”
-  Choose the language you want to translate
-  Select the project to translate


Select a component to translate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Select a component (a module or a piece of documentation)
-  Click on "Translate" to start translating

And let's go!

`Weblate official documentation <https://docs.weblate.org/en/latest/user/translating.html>`__
for translation.

Translation features
--------------------

Weblate shows all translation by language and by module.
Errors and left to translate can be displayed easily.

Weblate can identify problematic translations as chains between projects, punctuation inconsistancy.

.. figure:: ../images/translating/weblate-check.png
   :alt: image

Other occurrences in all components allows to check consistency.

.. figure:: ../images/translating/weblate-check-list-occurrences.png
   :alt: image

Each translation generate a permalink (picto |image|).

.. |image| image:: ../images/translating/link.png

Weblate has a "Zen mode" showing only chains to translate.

Release translations (only for github repository managers)
----------------------------------------------------------

Weblate send new translations to `translations` branch in Github, dedicated to translations.
When new translations chains are validated, manager has to send them manually to Github.

For each release, `translations` branch must be merged into master before building the release.

Send modifications to Github repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- In component, click "Manage > Repository maintenance"
- Click "Commit" to save translation in local repository
- Click "Push" to send local commits to `translations` branch in Github repository

Add translations to next release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In **Github**, merge `translations` branch into `master`, and update changelog.

2. After releasing, in **Weblate**, rebase the branch:

  - In the component, click "Manage > Repository maintenance"
  - Click "Rebase" to rebase `translations` branch onto `master`
